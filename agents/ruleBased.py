"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 14/03/2025
"""

from typing import TYPE_CHECKING

from action import Action, Drop, Move
from agent import Agent
from knowledge import AllKnowledge
from utils import Color, Direction

if TYPE_CHECKING:
    from model import RobotMission


class GreenRuleBasedAgent(Agent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
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

                return Move(Direction.random(exclude={Direction.RIGHT, Direction.LEFT}))

        pick = self.knowledge.try_pick()
        if pick is not None:
            return pick

        return Move(Direction.random())
    
class YellowRuleBasedAgent(Agent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
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

                return Move(Direction.random(exclude={Direction.RIGHT, Direction.LEFT}))

        pick = self.knowledge.try_pick()
        if pick is not None:
            return pick

        return Move(Direction.random())


class RedRuleBasedAgent(Agent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
        self.knowledge = AllKnowledge()

    def deliberate(self) -> Action:
        """
        Try to pick red waste,
        Move to the dump if has red waste,
        Else move randomly.
        """
        pick = self.knowledge.try_pick()
        if pick is not None:
            return pick

        if not self.inventory.is_empty():
            if self.knowledge.pos == self.knowledge.dump_pos:
                return Drop(self.inventory.wastes[0])

            move = self.knowledge.try_move(Direction.RIGHT)
            if move is not None:
                return move

            if self.knowledge.pos[1] == self.knowledge.dump_pos[1]:
                return Move(Direction.RIGHT)

            return Move(Direction.UP if self.knowledge.pos[1] < self.knowledge.dump_pos[1] else Direction.DOWN)

        return Move(Direction.random())
