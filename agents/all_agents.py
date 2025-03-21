from agent import Agent
from agents.RL import RLAgent
from agents.naive import NaiveAgent, RedNaiveAgent
from utils import Color


default_agent = "Naive"

str_to_agent: dict[str, type[Agent] | dict[Color, type[Agent]]] = {
    "Naive": {
        Color.GREEN: NaiveAgent,
        Color.YELLOW: NaiveAgent,
        Color.RED: RedNaiveAgent,
    },
    "DQN": RLAgent,
}


def get_agent_class(agent_name: str, color: Color) -> type[Agent]:
    agent = str_to_agent[agent_name]
    if isinstance(agent, dict):
        return agent[color]
    return agent
