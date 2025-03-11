"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

import mesa
import random

from action import Action
from agent import Agent, GreenAgent, YellowAgent, RedAgent
from objects import Radioactivity
from perception import Perception
from utils import Color


class RobotMission(mesa.Model):
    def __init__(
        self,
        width: int = 10,
        height: int = 10,
        n_green_agents: int = 1,
        n_yellow_agents: int = 1,
        n_red_agents: int = 1,
        radioactivity_proportions: list[float] = [1 / 3, 1 / 3, 1 / 3],
        seed: int | None = None,
    ):
        """Initialize a RobotMission instance.

        Args:
            width : The width of the grid.
            height : The height of the grid.
            n_<color>_agents : The number of <color> agents.
            radioactivity_proportions (list[float]): The proportions of the grid for each type of radioactivity. We assume that a column has a single radioactivity.
            seed (int): The seed for the random number generator.
        """
        super().__init__(seed=seed)
        random.seed(seed)
        self.width = width
        self.height = height
        self.n_agent = {
            Color.GREEN: n_green_agents,
            Color.YELLOW: n_yellow_agents,
            Color.RED: n_red_agents,
        }
        self.radioactivity_proportions = radioactivity_proportions

        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=False)

        self.green_yellow_border = int(self.width * self.radioactivity_proportions[0])
        self.yellow_red_border = int(self.width * (self.radioactivity_proportions[0] + self.radioactivity_proportions[1]))
        # green region is from 0 inclusive to green_yellow_border exclusive
        # yellow region is from green_yellow_border inclusive to yellow_red_border exclusive
        # red region is from yellow_red_border inclusive to width exclusive

        self.place_radioactivity()

        self.place_agents()

    def place_radioactivity(self):
        for x in range(0, self.width):
            for y in range(0, self.height):
                pos = x, y
                self.grid.place_agent(Radioactivity(self, self.get_zone(pos)), pos)

    def is_in_zone(self, pos: tuple[int, int], color: Color) -> bool:
        x, y = pos

        if y < 0 or y >= self.height:
            return False

        if color == Color.GREEN:
            return 0 <= x < self.green_yellow_border
        elif color == Color.YELLOW:
            return self.green_yellow_border <= x < self.yellow_red_border
        elif color == Color.RED:
            return self.yellow_red_border <= x < self.width

    def get_zone(self, pos: tuple[int, int]) -> Color:
        x, y = pos
        for color in Color:
            if self.is_in_zone(pos, color):
                return color
        raise ValueError("Invalid position")

    def get_random_pos_in_zone(self, color: Color) -> tuple[int, int]:
        y = random.randint(0, self.height - 1)
        if color == Color.GREEN:
            x = random.randint(0, self.green_yellow_border - 1)
        elif color == Color.YELLOW:
            x = random.randint(self.green_yellow_border, self.yellow_red_border - 1)
        elif color == Color.RED:
            x = random.randint(self.yellow_red_border, self.width - 1)
        return x, y

    def place_agents(self):
        for color, AgentInstantiator in zip(Color, [GreenAgent, YellowAgent, RedAgent]):
            for agent_idx in range(self.n_agent[color]):
                pos = self.get_random_pos_in_zone(color)
                perception = Perception(pos)

                self.grid.place_agent(AgentInstantiator(self, color, perception), pos)

    def step(self) -> None:
        for agent in self.agents:
            agent.step()

    def do(self, action: Action, agent: Agent) -> Perception:
        if action.can_apply(self, agent):
            action.apply(self, agent)
        return Perception(agent.get_true_pos())
