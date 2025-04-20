"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 15/03/2025
"""

import json
import solara

from typing import Any
from mesa.visualization import SolaraViz
from action import Action, Wait
from server import make_graphs

from agent import Agent
from model import RobotMission
from objects import Waste
from utils import Color


step_index = solara.reactive(0)


class ReplayAgent(Agent):
    def deliberate(self) -> Action:
        return Wait()

    def step(self):
        pass


class ReplayModel(RobotMission):
    """Fake model to simulate a Mesa model from JSON data."""

    def __init__(self, json_path: str = "simulations/10000.json"):
        with open(json_path, "r") as f:
            self.replay_data = json.load(f)

        super().__init__(self.replay_data["width"], self.replay_data["height"], 0, 0, 0, 0, 0, 0)

        self.id_to_agent: dict[int, Agent] = {
            agent_dict["id"]: ReplayAgent(self, Color(agent_dict["color"]))
            for agent_dict in self.replay_data["agents_color"]
        }

        for agent in self.id_to_agent.values():
            self.grid.place_agent(agent, (0, 0))

        step_index.set(0)
        self.reset_map()

    def get_current_step_data(self) -> dict[str, Any]:
        return self.replay_data["steps"][step_index.value]

    def step(self) -> None:
        if step_index.value >= len(self.replay_data["steps"]) - 1:
            return

        step_index.set(step_index.value + 1)
        self.reset_map()

    def reset_map(self):
        step_data = self.get_current_step_data()

        for waste in self.agents_by_type.get(Waste, []):
            if waste.pos is not None:
                self.grid.remove_agent(waste)

        for waste_dict in step_data["wastes"]:
            waste = Waste(self, Color(waste_dict["color"]))
            self.grid.place_agent(waste, (waste_dict["x"], waste_dict["y"]))

        for agent_dict in step_data["agents"]:
            agent = self.id_to_agent[agent_dict["id"]]
            self.grid.move_agent(agent, (agent_dict["x"], agent_dict["y"]))
            agent.inventory.clear()
            for waste_color in agent_dict["inventory"]:
                agent.inventory.add(Waste(self, Color(waste_color)))


model = solara.reactive(ReplayModel())


@solara.core.component
def SimulationReplay():
    """Solara UI for replaying the recorded simulation."""
    solara.Text(f"Step {step_index.value} / {len(model.value.replay_data) - 1}")
    solara.Button("Previous", on_click=lambda: step_index.set(max(0, step_index.value - 1)))
    solara.Button("Next", on_click=lambda: step_index.set(min(len(model.value.replay_data) - 1, step_index.value + 1)))


page = SolaraViz(
    model,  # type: ignore
    components=make_graphs(model),  # type: ignore
    name="Replay Simulation",
)
