"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

import mesa
from .agent import greenAgent, yellowAgent, redAgent
from .objects import Radioactivity
from utils import Color

class RobotMission(mesa.Model):
    def __init__(self, width = 10, height = 10, n_green_agents = 1, n_yellow_agents = 1, n_red_agents = 1, radioactivity_proportions:list[float] = [1/3, 1/3, 1/3], seed=1):
        """Initialize a RobotMission instance.

        Args:
            width : The width of the grid.
            height : The height of the grid.
            n_<color>_agents : The number of <color> agents.
            radioactivity_proportions (list[float]): The proportions of the grid for each type of radioactivity. We assume that a column has a single radioactivity.
            seed (int): The seed for the random number generator.
        """
        super().__init__(seed=seed)
        self.width = width
        self.height = height
        self.n_green_agents = n_green_agents
        self.n_yellow_agents = n_yellow_agents
        self.n_red_agents = n_red_agents
        self.radioactivity_proportions = radioactivity_proportions

        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=False)

        self.green_yellow_border = int(self.width * self.radioactivity_proportions[0])
        self.yellow_red_border = int(self.width * (self.radioactivity_proportions[0]+ self.radioactivity_proportions[1]))
        # green region is from 0 inclusive to green_yellow_border exclusive
        # yellow region is from green_yellow_border inclusive to yellow_red_border exclusive
        # red region is from yellow_red_border inclusive to width exclusive

    def place_radioactivity(self):
        # place green radioactivity
        for i in range(0, self.green_yellow_border):
            for j in range(0, self.height):
                self.grid.place_agent(Radioactivity(self, Color.GREEN, x=i, y=j), (i, j))


    def step(self):
        """do one step of the model"""
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
