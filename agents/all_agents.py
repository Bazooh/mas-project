from agent import Agent, RandomAgent
from agents.RL import RLAgent
from agents.naive import NaiveAgent, RedNaiveAgent
from agents.ruleBased import GreenCommunicationRuleBasedAgent, YellowCommunicationRuleBasedAgent, RedCommunicationRuleBasedAgent, GreenRuleBasedAgent, YellowRuleBasedAgent, RedRuleBasedAgent
from utils import Color


default_agent = "RuleBased"

str_to_agent: dict[str, type[Agent] | dict[Color, type[Agent]]] = {
    "Random": RandomAgent,
    "Naive": {
        Color.GREEN: NaiveAgent,
        Color.YELLOW: NaiveAgent,
        Color.RED: RedNaiveAgent,
    },
    "DQN": RLAgent,
    "CommunicationRuleBased": {
        Color.GREEN: GreenCommunicationRuleBasedAgent,
        Color.YELLOW: YellowCommunicationRuleBasedAgent,
        Color.RED: RedCommunicationRuleBasedAgent,
    },
    "RuleBased": {
        Color.GREEN: GreenRuleBasedAgent,
        Color.YELLOW: YellowRuleBasedAgent,
        Color.RED: RedRuleBasedAgent,
    },
}


def get_agent_class(agent_name: str, color: Color) -> type[Agent]:
    agent = str_to_agent[agent_name]
    if isinstance(agent, dict):
        return agent[color]
    return agent
