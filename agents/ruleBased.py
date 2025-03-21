"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 14/03/2025
"""

from typing import TYPE_CHECKING

from action import Action, Drop, Move
from agent import Agent
from knowledge import AllKnowledge ,History
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
        
        move = self.knowledge.look_around()
        if move is not None:
            return move

        return Move(Direction.random())
    
class YellowRuleBasedAgent(Agent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
        self.knowledge = AllKnowledge()
        self.patrol_direction = Direction.DOWN # At start, it will go down, then up, then down, etc.

    def deliberate(self) -> Action:
        """
        Always merge if possible,
        Move right to deposit waste if possible,
        Drop waste if possible,
        Finally move randomly.
        """

        # We try to merge
        merge = self.knowledge.try_merge()
        if merge is not None:
            return merge

        # If we have yellow waste, we go put it at the red-yellow frontier
        for waste in self.inventory:
            if waste.color > self.color:
                move = self.knowledge.try_move(Direction.RIGHT)
                if move is not None:
                    return move

                drop = self.knowledge.try_drop(waste)
                if drop is not None:
                    return drop

                return Move(Direction.random(exclude={Direction.RIGHT, Direction.LEFT}))

        # If we can pick a waste, we do it
        pick = self.knowledge.try_pick()
        if pick is not None:
            return pick
        
        # If there is a waste in an adjacent cell, we move to that cell
        move = self.knowledge.look_around()
        if move is not None:
            return move
        
        # If left case is yellow, we move left
        if Direction.LEFT in self.knowledge.perception and self.knowledge.perception[Direction.LEFT].color == Color.YELLOW:
            move = self.knowledge.try_move(Direction.LEFT)
            if move is not None:
                return move
            
        # If right case is not green, we move right
        if Direction.RIGHT in self.knowledge.perception and self.knowledge.perception[Direction.RIGHT].color == Color.GREEN:
            move = self.knowledge.try_move(Direction.RIGHT)
            if move is not None:
                return move
            
        # If there is a wall in the cycle direction, or a yellow agent, we change the cycle variable
        if self.patrol_direction not in self.knowledge.perception or (self.knowledge.perception[self.patrol_direction].agent is not None and self.knowledge.perception[self.patrol_direction].agent.color == Color.YELLOW):
            self.patrol_direction = Direction.UP if self.patrol_direction == Direction.DOWN else Direction.DOWN
            
        # We try to move towards cycle direction
        move = self.knowledge.try_move(self.patrol_direction)
        if move is not None:
            return move

        return Move(Direction.random())


class RedRuleBasedAgent(Agent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
        self.knowledge = AllKnowledge()
        self.patrol_direction = Direction.DOWN # At start, it will go down, then up, then down, etc.

    def deliberate(self) -> Action:
        """
        Try to pick red waste,
        Move to the dump if has red waste,
        Else move randomly.
        """

        # We try to pick red waste
        pick = self.knowledge.try_pick()
        if pick is not None:
            return pick
        
        # If red waste in adjacent cell, move to that cell
        move = self.knowledge.look_around()
        if move is not None:
            return move

        # If we have red waste, move to the dump
        if not self.inventory.is_empty():
            if self.knowledge.pos == self.knowledge.dump_pos:
                return Drop(self.inventory.wastes[0])

            move = self.knowledge.try_move(Direction.RIGHT)
            if move is not None:
                return move

            if self.knowledge.pos[1] == self.knowledge.dump_pos[1]:
                return Move(Direction.RIGHT)

            return Move(Direction.UP if self.knowledge.pos[1] < self.knowledge.dump_pos[1] else Direction.DOWN)

        # If left case is red, we move left
        if Direction.LEFT in self.knowledge.perception and self.knowledge.perception[Direction.LEFT].color == Color.RED:
            move = self.knowledge.try_move(Direction.LEFT)
            if move is not None:
                return move
            
        # If right case is not red, we move right
        if Direction.RIGHT in self.knowledge.perception and self.knowledge.perception[Direction.RIGHT].color != Color.RED:
            move = self.knowledge.try_move(Direction.RIGHT)
            if move is not None:
                return move
            
        # If there is a wall in the cycle direction, or a red agent, we change the cycle variable
        if self.patrol_direction not in self.knowledge.perception or (self.knowledge.perception[self.patrol_direction].agent is not None and self.knowledge.perception[self.patrol_direction].agent.color == Color.RED):
            self.patrol_direction = Direction.UP if self.patrol_direction == Direction.DOWN else Direction.DOWN
            
        # We try to move towards cycle direction
        move = self.knowledge.try_move(self.patrol_direction)
        if move is not None:
            return move

        return Move(Direction.random())