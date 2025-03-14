"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 14/03/2025
"""

from typing import TYPE_CHECKING

from action import Action, Move
from agent import Agent
from knowledge import AllKnowledge
from utils import Color, Direction

if TYPE_CHECKING:
    from model import RobotMission

class NaiveAgent(Agent):
    def __init__(self, model: "RobotMission", color: Color, inventory_capacity: int) -> None:
        super().__init__(model, color, inventory_capacity)
        self.knowledge = AllKnowledge()

    def deliberate(self) -> Action:
        """
        Always merge if possible,
        Move right to deposit waste if possible,
        Drop waste if possible,
        Finally move randomly.
        """
        merge = self.knowledge.try_merge()
        if merge is not None:
            return merge

        for waste in self.inventory:
            if waste.color > self.color:
                move = self.knowledge.try_move(Direction.RIGHT)
                if move is not None:
                    return move

                drop = self.knowledge.try_drop(waste)
                if drop is not None:
                    return drop

                return Move(Direction.random(exclude={Direction.RIGHT}))

        pick = self.knowledge.try_pick()
        if pick is not None:
            return pick

        return Move(Direction.random())
