"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from __future__ import annotations

import json
from typing import Any, Iterator, cast
import mesa
import random

import torch

from action import Action
from agent import Agent, CommunicationAgent

from agents.RL import RLAgent

from objects import Dump, Radioactivity, Waste
from perception import Perception
from utils import Color, Position
from agents.all_agents import default_agent, get_agent_class

from communication import Message


default_agents_params: dict[Color, dict[str, Any]] = {Color.GREEN: {}, Color.YELLOW: {}, Color.RED: {}}


def model_to_n_waste(model: RobotMission) -> dict[Color, int]:
    n_waste = {Color.GREEN: 0, Color.YELLOW: 0, Color.RED: 0}

    for cells, coords in model.grid.coord_iter():
        cells = cast(mesa.space.MultiGridContent, cells)

        for cell in cells:
            if isinstance(cell, Waste):
                n_waste[cell.color] += 1
            elif isinstance(cell, Agent):
                for waste in cell.inventory:
                    n_waste[waste.color] += 1

    return n_waste


class MessageService:
    """
    Object possessed by the model that can transfer messages between agents.
    """
    def __init__(self, model):
        self.model = model

    def send(self, receiver_id: int, message: Message):
        receiver = self.model.get_agent_by_id(receiver_id)
        receiver.mailbox.receive(message)

        from communication import ContentType
        if message.type == ContentType.TARGET:
            print('zzzzzzzzzzzzzzzzzzzzzzzzzzz', "receiver_id", receiver_id, "message_type", message.type)

    def send_all(self, receiver_ids: list[int], message: Message):
        for receiver_id in receiver_ids:
            self.send(receiver_id, message)

class RobotMission(mesa.Model):
    def __init__(
        self,
        width: int = 10,
        height: int = 10,
        n_green_agents: int = 2,
        n_yellow_agents: int = 1,
        n_red_agents: int = 1,
        n_green_wastes: int = 12,
        n_yellow_wastes: int = 0,
        n_red_wastes: int = 0,
        green_agent_model: str = default_agent,
        yellow_agent_model: str = default_agent,
        red_agent_model: str = default_agent,
        radioactivity_proportions: list[float] = [1 / 3, 1 / 3, 1 / 3],
        seed: int | None = None,
        agent_params: dict[Color, dict[str, Any]] = default_agents_params,
    ):
        """Initialize a RobotMission instance.

        Args:
            width : The width of the grid.
            height : The height of the grid.
            n_<color>_agents : The number of <color> agents.
            radioactivity_proportions (list[float]): The proportions of the grid for each type of radioactivity. We assume that a column has a single radioactivity.
            seed (int): The seed for the random number generator.
        """
        super().__init__(seed=seed)
        random.seed(seed)
        self.width = width
        self.height = height
        self.n_agents_by_color = {
            Color.GREEN: n_green_agents,
            Color.YELLOW: n_yellow_agents,
            Color.RED: n_red_agents,
        }
        self.radioactivity_proportions = radioactivity_proportions

        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=False)
        self.step_idx = 0

        green_yellow_border = int(self.width * self.radioactivity_proportions[0])
        yellow_red_border = int(self.width * (self.radioactivity_proportions[0] + self.radioactivity_proportions[1]))
        # green region is from 0 inclusive to green_yellow_border exclusive
        # yellow region is from green_yellow_border inclusive to yellow_red_border exclusive
        # red region is from yellow_red_border inclusive to width exclusive

        self.dump_pos: Position
        self.place_radioactivity(green_yellow_border, yellow_red_border)

        self.dumped_wastes: list[Waste] = []

        wastes = {
            Color.GREEN: n_green_wastes,
            Color.YELLOW: n_yellow_wastes,
            Color.RED: n_red_wastes,
        }
        self.place_waste(wastes)

        agents_class = [green_agent_model, yellow_agent_model, red_agent_model]
        self.place_agents({color: get_agent_class(agent, color) for agent, color in zip(agents_class, Color)}, agent_params)

        for agent in self.get_agents():
            agent.init_perception(Perception.from_agent(self, agent))

        self.datacollector = mesa.DataCollector(
            {color.name: lambda model, color=color: model_to_n_waste(model)[color] for color in Color}
        )
        self.datacollector.collect(self)

        self.history: list[dict[str, Any]] = []

        self.message_service = MessageService(self)

    @property
    def n_agents(self) -> int:
        return sum(self.n_agents_by_color.values())

    def get_n_wastes(self, color: Color) -> int:
        s = 0
        for waste in [cell for cell in self.agents if isinstance(cell, Waste)]:
            s += 1 if waste.color == color else 0
        for agent in self.get_agents():
            for waste in agent.inventory:
                s += 1 if waste.color == color else 0
        return s

    def serialize(self):
        """Serialize the model state. (Used for replay)"""
        return {
            "step": len(self.history),
            "agents": [
                {
                    "id": agent.unique_id,
                    "x": agent.pos[0],  # type: ignore
                    "y": agent.pos[1],  # type: ignore
                    "inventory": [waste.color for waste in agent.inventory],
                }
                for agent in self.get_agents()
            ],
            "wastes": [
                {"x": waste.pos[0], "y": waste.pos[1], "color": waste.color}  # type: ignore
                for waste in self.grid.agents
                if isinstance(waste, Waste)
            ],
        }

    def is_done(self) -> bool:
        return sum(self.get_n_wastes(color) for color in Color) == 0

    def place_radioactivity(self, green_yellow_border: int, yellow_red_border: int) -> None:
        for x in range(0, self.width):
            for y in range(0, self.height):
                if x == self.width - 1 and y == (self.height - 1) // 2:
                    self.grid.place_agent(Dump(self, Color.RED), (x, y))
                    self.dump_pos = (x, y)
                    continue

                if x < green_yellow_border:
                    color = Color.GREEN
                elif x < yellow_red_border:
                    color = Color.YELLOW
                else:
                    color = Color.RED
                self.grid.place_agent(Radioactivity(self, color), (x, y))

    def run(self, steps: int) -> None:
        for _ in range(steps):
            if self.is_done():
                break
            self.step()

    def place_waste(self, wastes: dict[Color, int]) -> None:
        for color, n_waste in wastes.items():
            for _ in range(n_waste):
                pos = self.get_random_pos_with_color(color, no_waste=True)
                self.grid.place_agent(Waste(self, color), pos)

    def get_color_at(self, pos: Position) -> Color:
        for cell in self.grid.iter_cell_list_contents([pos]):
            if isinstance(cell, Radioactivity):
                return cell.color
        raise ValueError("No radioactivity found at this position")

    def iter_pos_with_color(self, color: Color, no_agent=False, no_waste=False) -> Iterator[Position]:
        for cells, pos in self.grid.coord_iter():
            cells = cast(mesa.space.MultiGridContent, cells)

            if no_agent and self.is_any_agent_at(pos):
                continue

            if no_waste and self.is_any_waste_at(pos):
                continue

            for cell in cells:
                if isinstance(cell, Radioactivity) and cell.color == color:
                    yield pos

    def get_random_pos_with_color(self, color: Color, no_agent=False, no_waste=False) -> Position:
        return random.choice(list(self.iter_pos_with_color(color, no_agent, no_waste)))

    def is_any_agent_at(self, pos: Position) -> bool:
        return any(isinstance(cell, Agent) for cell in self.grid.iter_cell_list_contents([pos]))

    def get_waste_at(self, pos: Position) -> Waste:
        cells = [cell for cell in self.grid.iter_cell_list_contents([pos]) if isinstance(cell, Waste)]
        assert len(cells) <= 1, "Multiple wastes at the same position"
        assert len(cells) >= 1, "No waste at this position"
        return cells[0]

    def is_any_waste_at(self, pos: Position) -> bool:
        return any(isinstance(cell, Waste) for cell in self.grid.iter_cell_list_contents([pos]))

    def get_agents(self) -> list[Agent]:
        return [cell for cell in self.grid.agents if isinstance(cell, Agent)]

    def place_agents(self, agent_model: dict[Color, type[Agent]], params: dict[Color, dict[str, Any]]) -> None:
        for color in Color:
            for agent_idx in range(self.n_agents_by_color[color]):
                pos = self.get_random_pos_with_color(color, no_agent=True)

                self.grid.place_agent(agent_model[color](self, color, **params[color]), pos)

    def step(self) -> None:
        agents = self.get_agents()
        random.shuffle(agents)
        for agent in agents:
            agent.step()
        self.datacollector.collect(self)
        self.history.append(self.serialize())
        self.step_idx += 1

    def do(self, action: Action, agent: Agent) -> Perception:
        if action.can_apply(self, agent):
            action.apply(self, agent)
        return Perception.from_agent(self, agent)

    def to_dict(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "agents_color": [{"id": agent.unique_id, "color": agent.color} for agent in self.get_agents()],
            "steps": self.history,
        }

    def save(self, path: str = "simulation.json") -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    def to_tensor(self) -> torch.Tensor:
        """
        - 3 dimensions for the colors of the wastes
        - 1 dimension for the non-RL agents
        - 2 dimensions for the inventory of the non-RL agents
        - for each RL agent:
            - 1 dimension for the agent itself
            - 2 dimensions for the inventory
        """
        rl_agents = [agent for agent in self.get_agents() if isinstance(agent, RLAgent)]

        out = torch.zeros((len(Color) + 3 * (len(rl_agents) + 1), self.width, self.height))

        for cell in self.grid.agents:
            x, y = cast(Position, cell.pos)

            if isinstance(cell, Waste):
                out[cell.color - 1, x, y] = 1

            elif isinstance(cell, Agent):
                offset = len(Color) * ((cell.training_id + 2) if isinstance(cell, RLAgent) else 1)

                out[offset, x, y] = 1
                for waste in cell.inventory:
                    out[offset + (1 if waste.color == cell.color else 2), x, y] += 1

        return out
    
    def get_agent_by_id(self, agent_id: int) -> Agent :
        for agent in self.get_agents():
            if agent.unique_id == agent_id:
                return agent
            
        possible_ids = [agent.unique_id for agent in self.get_agents()]
        raise ValueError(f"Agent with id {agent_id} not found, the possible ids are {possible_ids}")
        #return self._agents.get(agent_id)
