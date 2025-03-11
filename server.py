"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from mesa.visualization import SolaraViz, make_space_component
from model import RobotMission
from agent import Agent
from objects import Radioactivity


def agent_portrayal(agent):
    if isinstance(agent, Radioactivity):
        return {"color": agent.color.to_light_hex(), "marker": "s", "size": 1200, "zorder": 0}
    if isinstance(agent, Agent):
        return {"color": agent.color.to_hex(), "marker": "o", "size": 100, "zorder": 1}
    return {"color": "tab:blue", "size": 10}  # Default


model = RobotMission(n_green_agents=10, n_yellow_agents=10, n_red_agents=10)

SpaceGraph = make_space_component(
    agent_portrayal,
    propertylayer_portrayal={
        "canvas_width": 200,  # Total width for 10 cells: 10 * 30px = 300px
        "canvas_height": 20,  # Total height for 10 cells: 10 * 20px = 200px
    },
)

page = SolaraViz(
    model,
    components=[SpaceGraph],
    name="Minimal Grid Display",
)
