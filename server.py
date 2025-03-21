"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from itertools import product
import numpy as np
import solara
import mesa

from matplotlib.axes import Axes
from mesa.visualization import SolaraViz, make_space_component, make_plot_component

from model import RobotMission
from agent import Agent
from objects import Dump, Radioactivity, Waste
from utils import Color
from run import model, model_params


def post_process(model: solara.Reactive[RobotMission], ax: Axes) -> None:
    grid = np.zeros((model.value.height, model.value.width, 3))
    for x, y in product(range(model.value.width), range(model.value.height)):
        cells = [cell for cell in model.value.grid.get_cell_list_contents([(x, y)]) if isinstance(cell, Radioactivity)]
        assert len(cells) == 1, "Multiple or no radioactivity in the cell"

        radioactivity = cells[0]

        if isinstance(radioactivity, Dump):
            grid[y, x] = (0.8, 0.5, 0.5)
        else:
            grid[y, x] = radioactivity.color.to_light_rgb()

    ax.imshow(grid, origin="lower", extent=(-0.5, model.value.width - 0.5, -0.5, model.value.height - 0.5), zorder=0)

    for agent in model.value.get_agents():
        for idx, waste in enumerate(agent.inventory):
            pos = agent.get_true_pos()
            pos = (pos[0] + 0.2 * idx + 0.2, pos[1] + 0.3)

            ax.scatter(*pos, color=waste.color.to_hex(), marker="*", s=50, zorder=3, edgecolors="black", linewidths=0.4)


def agent_portrayal(agent: mesa.Agent):
    if isinstance(agent, Waste):
        color = agent.color.to_hex()
        return {"edgecolors": "black", "color": color, "marker": "*", "size": 100, "zorder": 2, "linewidths": 0.4}

    if isinstance(agent, Agent):
        color = agent.color.to_hex()
        return {"color": color, "marker": "o", "size": 200, "zorder": 1, "edgecolors": "black", "linewidths": 0}

    return {"edgecolors": "black", "color": "black", "marker": "s", "size": 0, "zorder": 0, "linewidths": 0}


def make_graphs(model: solara.Reactive[RobotMission]):
    MatplotlibGraph = make_plot_component({color.name: color.to_hex() for color in Color})
    SpaceGraph = make_space_component(agent_portrayal, post_process=lambda ax: post_process(model, ax))

    return [SpaceGraph, MatplotlibGraph]


@solara.core.component
def Save(test):
    solara.Button("Save", on_click=lambda: model.value.save("simulation.json"))


if __name__ == "__main__":
    page = SolaraViz(
        model,  # type: ignore
        components=make_graphs(model) + [Save],
        name="Minimal Grid Display",
        model_params=model_params,
    )
