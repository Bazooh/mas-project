"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

import solara

from matplotlib.axes import Axes
from mesa.visualization import SolaraViz, make_space_component, make_plot_component

from model import RobotMission
from agent import Agent
from objects import Radioactivity, Waste
from utils import Color


def post_process(ax: Axes) -> None:
    for agent in model.value.get_agents():
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


model = solara.reactive(RobotMission(n_green_agents=10, n_yellow_agents=10, n_red_agents=10))

MatplotlibGraph = make_plot_component({color.name: color.to_hex() for color in Color})
SpaceGraph = make_space_component(
    agent_portrayal,
    propertylayer_portrayal={
        "canvas_width": 200,  # Total width for 10 cells: 10 * 30px = 300px
        "canvas_height": 20,  # Total height for 10 cells: 10 * 20px = 200px
    },
    post_process=post_process,
)


page = SolaraViz(
    model,  # type: ignore
    components=[SpaceGraph, MatplotlibGraph],  # type: ignore
    name="Minimal Grid Display",
    model_params={
        "width": 10,
        "height": 10,
        "n_green_agents": {
            "type": "SliderInt",
            "value": 10,
            "min": 0,
            "max": 30,
            "label": "Number of Green agents",
        },
        "n_yellow_agents": {
            "type": "SliderInt",
            "value": 10,
            "min": 0,
            "max": 30,
            "label": "Number of Yellow agents",
        },
        "n_red_agents": {
            "type": "SliderInt",
            "value": 10,
            "min": 0,
            "max": 40,
            "label": "Number of Red agents",
        },
        "n_red_wastes": {
            "type": "SliderInt",
            "value": 0,
            "min": 0,
            "max": 40,
            "label": "Number of Red waste",
        },
        "n_yellow_wastes": {
            "type": "SliderInt",
            "value": 0,
            "min": 0,
            "max": 30,
            "label": "Number of Yellow waste",
        },
        "n_green_wastes": {
            "type": "SliderInt",
            "value": 10,
            "min": 0,
            "max": 30,
            "label": "Number of Green waste",
        },
    },
)
