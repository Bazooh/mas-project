"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

import solara

from model import RobotMission
from utils import Color
from agents.all_agents import str_to_agent, default_agent


model_params = {
    "width": {
        "type": "SliderInt",
        "value": 10,
        "min": 1,
        "max": 20,
    },
    "height": {
        "type": "SliderInt",
        "value": 10,
        "min": 1,
        "max": 20,
    },
    "n_green_agents": {
        "type": "SliderInt",
        "value": 2,
        "min": 0,
        "max": 30,
        "label": "Number of Green agents",
    },
    "n_yellow_agents": {
        "type": "SliderInt",
        "value": 1,
        "min": 0,
        "max": 30,
        "label": "Number of Yellow agents",
    },
    "n_red_agents": {
        "type": "SliderInt",
        "value": 1,
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
        "step": 2,
    },
    "n_green_wastes": {
        "type": "SliderInt",
        "value": 12,
        "min": 0,
        "max": 30,
        "label": "Number of Green waste",
        "step": 4,
    },
    **{
        f"{color.name.lower()}_agent_model": {
            "type": "Select",
            "value": default_agent,
            "values": list(str_to_agent.keys()),
            "label": f"Model for {color.name[0] + color.name.lower()[1:]} agent",
        }
        for color in Color
    },
}


def get_model_args():
    return {key: (value["value"] if isinstance(value, dict) else value) for key, value in model_params.items()}


model = solara.reactive(RobotMission(**get_model_args()))


def reset_model(**kwargs):
    model.set(RobotMission(**get_model_args() | kwargs))
