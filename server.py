"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from mesa.visualization import SolaraViz, make_space_component
from model import RobotMission
from agent import Agent
from objects import Radioactivity
from utils import Color

def agent_portrayal(agent):
    if isinstance(agent, Radioactivity):
        if agent.color == Color.GREEN:
            return {"color": "#e4fade", "marker": "s", "size": 1200, "zorder": 0}  # Full-cell rectangle
        elif agent.color == Color.YELLOW:
            return {"color": "#f5f3c9", "marker": "s", "size": 1200, "zorder": 0}  # Full-cell rectangle
        elif agent.color == Color.RED:
            return {"color": "#fadede", "marker": "s", "size": 1200, "zorder": 0}  # Full-cell rectangle
    if isinstance(agent, Agent):
        return {"color": agent.color.to_hex(), "marker": "o", "size": 100, "zorder": 1}  # Default portrayal
    return {"color": "tab:blue", "size": 10}  # Default portrayal

# Create initial model instance
model = RobotMission()

# Create only the grid visualization
SpaceGraph = make_space_component(agent_portrayal,     propertylayer_portrayal={
        "canvas_width": 200,  # Total width for 10 cells: 10 * 30px = 300px
        "canvas_height": 20  # Total height for 10 cells: 10 * 20px = 200px
    })

# Create the Dashboard
page = SolaraViz(
    model,
    components=[SpaceGraph],
    name="Minimal Grid Display",
)

page