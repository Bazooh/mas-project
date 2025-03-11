"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

import solara
from mesa.visualization import SolaraViz, make_space_component
from model import RobotMission

def agent_portrayal(agent):
    return {"color": "tab:blue", "size": 10}  # Minimal portrayal

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