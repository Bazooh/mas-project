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
    # if isinstance(agent, Radioactivity):
    #     if agent.color == Color.GREEN:
    #         return {"color": "green", "marker": "s", "size": 100}  # Full-cell rectangle
    #     elif agent.color == Color.YELLOW:
    #         return {"color": "yellow", "marker": "s", "size": 100}  # Full-cell rectangle
    #     elif agent.color == Color.RED:
    #         return {"color": "red", "marker": "s", "size": 100}  # Full-cell rectangle
    if isinstance(agent, Agent):
        return {"color": "tab:red", "size": 100}  # Default portrayal
    return {"color": "tab:blue", "size": 0}  # Default portrayal

# Create initial model instance
model = RobotMission()

# Create only the grid visualization
SpaceGraph = make_space_component(agent_portrayal)

# Create the Dashboard
page = SolaraViz(
    model,
    components=[SpaceGraph],
    name="Minimal Grid Display",
)

page