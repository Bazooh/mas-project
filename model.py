"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from __future__ import annotations

from typing import Iterator, cast
import mesa
import random

from action import Action
from agent import Agent, GreenAgent, YellowAgent, RedAgent
from objects import Radioactivity, Waste
from perception import Perception
from utils import Color, Position


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


class RobotMission(mesa.Model):
    def __init__(
        self,
        width: int = 10,
        height: int = 10,
        n_green_agents: int = 1,
        n_yellow_agents: int = 1,
        n_red_agents: int = 1,
        radioactivity_proportions: list[float] = [1 / 3, 1 / 3, 1 / 3],
        seed: int | None = None,
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
        self.n_agent = {
            Color.GREEN: n_green_agents,
            Color.YELLOW: n_yellow_agents,
            Color.RED: n_red_agents,
        }
        self.radioactivity_proportions = radioactivity_proportions

        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=False)

        green_yellow_border = int(self.width * self.radioactivity_proportions[0])
        yellow_red_border = int(self.width * (self.radioactivity_proportions[0] + self.radioactivity_proportions[1]))
        # green region is from 0 inclusive to green_yellow_border exclusive
        # yellow region is from green_yellow_border inclusive to yellow_red_border exclusive
        # red region is from yellow_red_border inclusive to width exclusive

        self.place_radioactivity(green_yellow_border, yellow_red_border)

        wastes = {
            Color.GREEN: 10,
            Color.YELLOW: 0,
            Color.RED: 0,
        }
        self.place_waste(wastes)

        self.place_agents(
            {
                Color.GREEN: {"inventory_capacity": 2},
                Color.YELLOW: {"inventory_capacity": 2},
                Color.RED: {"inventory_capacity": 1},
            }
        )

        self.datacollector = mesa.DataCollector(
            {color.name: lambda model, color=color: model_to_n_waste(model)[color] for color in Color}
        )
        self.datacollector.collect(self)

    def place_radioactivity(self, green_yellow_border: int, yellow_red_border: int) -> None:
        for x in range(0, self.width):
            for y in range(0, self.height):
                if x < green_yellow_border:
                    color = Color.GREEN
                elif x < yellow_red_border:
                    color = Color.YELLOW
                else:
                    color = Color.RED
                self.grid.place_agent(Radioactivity(self, color), (x, y))

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

    def place_agents(self, params: dict[Color, dict[str, int]]) -> None:
        for color, AgentInstantiator in zip(params, [GreenAgent, YellowAgent, RedAgent]):
            for agent_idx in range(self.n_agent[color]):
                pos = self.get_random_pos_with_color(color, no_agent=True)

                self.grid.place_agent(AgentInstantiator(self, color, Perception(pos), **params[color]), pos)

    def step(self) -> None:
        agents = list(self.agents)
        random.shuffle(agents)
        for agent in agents:
            agent.step()
        self.datacollector.collect(self)

    def do(self, action: Action, agent: Agent) -> Perception:
        if action.can_apply(self, agent):
            action.apply(self, agent)
        return Perception(agent.get_true_pos())
