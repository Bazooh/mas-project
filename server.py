"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from matplotlib.axes import Axes
from mesa.visualization import SolaraViz, make_space_component
from model import RobotMission
from agent import Agent
from objects import Radioactivity, Waste


def post_process(ax: Axes) -> None:
    for agent in model.get_agents():
        for idx, waste in enumerate(agent.inventory):
            pos = agent.get_true_pos()
            pos = (pos[0] + 0.2 * idx + 0.2, pos[1] + 0.3)

            ax.scatter(*pos, color=waste.color.to_hex(), marker="*", s=50, zorder=3, edgecolors="black", linewidths=0.4)


def agent_portrayal(agent):
    if isinstance(agent, Radioactivity):
        color = agent.color.to_light_hex()
        return {"color": color, "marker": "s", "size": 1200, "zorder": 0, "edgecolors": "black", "linewidths": 0}

    if isinstance(agent, Waste):
        color = agent.color.to_hex()
        return {"edgecolors": "black", "color": color, "marker": "*", "size": 100, "zorder": 2, "linewidths": 0.4}

    if isinstance(agent, Agent):
        color = agent.color.to_hex()
        return {"color": color, "marker": "o", "size": 200, "zorder": 1, "edgecolors": "black", "linewidths": 0}


model = RobotMission(n_green_agents=10, n_yellow_agents=10, n_red_agents=10)

SpaceGraph = make_space_component(
    agent_portrayal,
    propertylayer_portrayal={
        "canvas_width": 200,  # Total width for 10 cells: 10 * 30px = 300px
        "canvas_height": 20,  # Total height for 10 cells: 10 * 20px = 200px
    },
    post_process=post_process,
)

page = SolaraViz(
    model,
    components=[SpaceGraph],
    name="Minimal Grid Display",
)
