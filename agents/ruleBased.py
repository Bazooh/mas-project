"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 14/03/2025
"""

from typing import TYPE_CHECKING

from action import Action, Drop, Move, Wait
from agent import CommunicationAgent, Agent
from information import TargetInformation
from knowledge import AllKnowledge
from utils import Color, Direction

if TYPE_CHECKING:
    from model import RobotMission


class GreenRuleBasedAgent(Agent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
        self.knowledge = AllKnowledge()
        self.patrol_horizontal_direction = Direction.RIGHT
        self.patrol_vertical_direction = Direction.DOWN
        self.coop_mode = 0

    def next_patrol_direction(self):
        """
        The cycle is :
        ...
        >-----|
              v
        |--<--|
        |
        |->---|
              |
        --<---|
        ...
        and then when we hit bottom :
        ...
        |--<--|
              ^
        |->---|
        |
        |--<--|        ...
        """
        if self.patrol_horizontal_direction == Direction.RIGHT:
            # we check if right cell is yellow, if so we go patrol_vertical_direction (and maybe change it) and next one will be left
            if (
                Direction.RIGHT in self.knowledge.perception
                and self.knowledge.perception[Direction.RIGHT].color == Color.YELLOW
            ):
                self.patrol_horizontal_direction = Direction.LEFT
                # possible to follow patrol_vertical_direction ?
                if self.patrol_vertical_direction in self.knowledge.perception:
                    return self.knowledge.try_move(self.patrol_vertical_direction)
                else:
                    self.patrol_vertical_direction = (
                        Direction.DOWN if self.patrol_vertical_direction == Direction.UP else Direction.UP
                    )
                    return self.knowledge.try_move(self.patrol_vertical_direction)

            else:  # we can go right
                return self.knowledge.try_move(Direction.RIGHT)

        elif self.patrol_horizontal_direction == Direction.LEFT:
            # we check if left cell is wall, if so we go patrol_vertical_direction (and maybe change it) and next one will be right
            if Direction.LEFT not in self.knowledge.perception:
                self.patrol_horizontal_direction = Direction.RIGHT
                # possible to follow patrol_vertical_direction ?
                if self.patrol_vertical_direction in self.knowledge.perception:
                    return self.knowledge.try_move(self.patrol_vertical_direction)
                else:
                    self.patrol_vertical_direction = (
                        Direction.DOWN if self.patrol_vertical_direction == Direction.UP else Direction.UP
                    )
                    return self.knowledge.try_move(self.patrol_vertical_direction)
            else:  # we can go left
                return self.knowledge.try_move(Direction.LEFT)

    def deliberate(self) -> Action:
        """
        Always merge if possible,
        Move right to deposit waste if possible,
        Drop waste if possible,
        Finally move randomly.
        """
        if self.coop_mode > 0:
            if self.coop_mode == 2:  # we want to move
                self.coop_mode = 1
                return Move(Direction.random())
            if self.coop_mode == 1:
                self.coop_mode = 0
                return Wait()

        # We try to merge
        merge = self.knowledge.try_merge()
        if merge is not None:
            return merge

        # If we have green waste, we go put it at the green-yellow frontier
        for waste in self.inventory:
            if waste.color > self.color:
                move = self.knowledge.try_move(Direction.RIGHT)
                if move is not None:
                    return move

                if self.knowledge.perception[Direction.RIGHT].color == Color.YELLOW:
                    drop = self.knowledge.try_drop(waste)
                    if drop is not None:
                        return drop

                return Move(Direction.random(exclude={Direction.RIGHT, Direction.LEFT}))

        # If we can pick a waste, we do it
        pick = self.knowledge.try_pick()
        if pick is not None:
            return pick

        # If there is a waste in an adjacent cell, we move to that cell
        moveOrWait = self.knowledge.look_around()
        if moveOrWait is not None:
            return moveOrWait

        # If we have exactly one waste of our color, and there is an agent of our color having exactly one waste of our color near, we want to cooperate
        if len(self.inventory) == 1:
            for waste in self.inventory:
                if waste.color == self.color:
                    for direction in self.knowledge.perception:
                        if (
                            direction != Direction.NONE
                            and (agent := self.knowledge.perception[direction].agent) is not None
                            and agent.color == self.color
                            and len(agent.inventory) == 1
                        ):
                            for other_waste in agent.inventory:
                                if other_waste.color == self.color:
                                    # we want to cooperate
                                    drop = self.knowledge.try_drop(waste)
                                    if drop is not None:
                                        self.coop_mode = 2
                                        return drop

        # We follow the patrol cycle
        move = self.next_patrol_direction()
        if move is not None:
            return move

        return Move(Direction.random())


class YellowRuleBasedAgent(Agent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
        self.knowledge = AllKnowledge()
        self.patrol_direction = Direction.DOWN  # At start, it will go down, then up, then down, etc.
        self.coop_mode = 0

    def deliberate(self) -> Action:
        """
        Always merge if possible,
        Move right to deposit waste if possible,
        Drop waste if possible,
        Finally move randomly.
        """

        if self.coop_mode > 0:
            if self.coop_mode == 2:  # we want to move
                self.coop_mode = 1
                return Move(Direction.random())
            if self.coop_mode == 1:
                self.coop_mode = 0
                return Wait()

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

                if self.knowledge.perception[Direction.RIGHT].color == Color.RED:
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

        # If we have exactly one waste of our color, and there is an agent of our color having exactly one waste of our color near, we want to cooperate
        if len(self.inventory) == 1:
            for waste in self.inventory:
                if waste.color == self.color:
                    for direction in self.knowledge.perception:
                        if (
                            direction != Direction.NONE
                            and (agent := self.knowledge.perception[direction].agent) is not None
                            and agent.color == self.color
                            and len(agent.inventory) == 1
                        ):
                            for other_waste in agent.inventory:
                                if other_waste.color == self.color:
                                    # we want to cooperate
                                    drop = self.knowledge.try_drop(waste)
                                    if drop is not None:
                                        self.coop_mode = 2
                                        return drop

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
        if self.patrol_direction not in self.knowledge.perception or (
            (waste := self.knowledge.perception[self.patrol_direction].agent) is not None and waste.color == Color.YELLOW
        ):
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
        self.patrol_direction = Direction.DOWN  # At start, it will go down, then up, then down, etc.

    def deliberate(self) -> Action:
        """
        Try to pick red waste,
        Move to the dump if has red waste,
        Else move randomly.
        """

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

        # We try to pick red waste
        pick = self.knowledge.try_pick()
        if pick is not None:
            return pick

        # If red waste in adjacent cell, move to that cell
        move = self.knowledge.look_around()
        if move is not None:
            return move

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
        if self.patrol_direction not in self.knowledge.perception or (
            (waste := self.knowledge.perception[self.patrol_direction].agent) is not None and waste.color == Color.RED
        ):
            self.patrol_direction = Direction.UP if self.patrol_direction == Direction.DOWN else Direction.DOWN

        # We try to move towards cycle direction
        move = self.knowledge.try_move(self.patrol_direction)
        if move is not None:
            return move

        return Move(Direction.random())


def go_toward_target(x, y, xtarget, ytarget) -> Action | None:
    if y > ytarget:
        return Move(Direction.DOWN)
    elif y < ytarget:
        return Move(Direction.UP)
    elif x > xtarget:
        return Move(Direction.LEFT)
    elif x < xtarget:
        return Move(Direction.RIGHT)
    else:
        return None


class GreenCommunicationRuleBasedAgent(CommunicationAgent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
        self.knowledge = AllKnowledge()
        self.patrol_horizontal_direction = Direction.RIGHT
        self.patrol_vertical_direction = Direction.DOWN
        self.coop_mode = 0

    def next_patrol_direction(self):
        """
        The cycle is :
        ...
        >-----|
              v
        |--<--|
        |
        |->---|
              |
        --<---|
        ...
        and then when we hit bottom :
        ...
        |--<--|
              ^
        |->---|
        |
        |--<--|        ...
        """
        if self.patrol_horizontal_direction == Direction.RIGHT:
            # we check if right cell is yellow, if so we go patrol_vertical_direction (and maybe change it) and next one will be left
            if (
                Direction.RIGHT in self.knowledge.perception
                and self.knowledge.perception[Direction.RIGHT].color == Color.YELLOW
            ):
                self.patrol_horizontal_direction = Direction.LEFT
                # possible to follow patrol_vertical_direction ?
                if self.patrol_vertical_direction in self.knowledge.perception:
                    return self.knowledge.try_move(self.patrol_vertical_direction)
                else:
                    self.patrol_vertical_direction = (
                        Direction.DOWN if self.patrol_vertical_direction == Direction.UP else Direction.UP
                    )
                    return self.knowledge.try_move(self.patrol_vertical_direction)

            else:  # we can go right
                return self.knowledge.try_move(Direction.RIGHT)

        elif self.patrol_horizontal_direction == Direction.LEFT:
            # we check if left cell is wall, if so we go patrol_vertical_direction (and maybe change it) and next one will be right
            if Direction.LEFT not in self.knowledge.perception:
                self.patrol_horizontal_direction = Direction.RIGHT
                # possible to follow patrol_vertical_direction ?
                if self.patrol_vertical_direction in self.knowledge.perception:
                    return self.knowledge.try_move(self.patrol_vertical_direction)
                else:
                    self.patrol_vertical_direction = (
                        Direction.DOWN if self.patrol_vertical_direction == Direction.UP else Direction.UP
                    )
                    return self.knowledge.try_move(self.patrol_vertical_direction)
            else:  # we can go left
                return self.knowledge.try_move(Direction.LEFT)

    def deliberate(self) -> Action:
        """
        Always merge if possible,
        Move right to deposit waste if possible,
        Drop waste if possible,
        Finally move randomly.
        """
        if self.coop_mode > 0:
            if self.coop_mode == 2:  # we want to move
                self.coop_mode = 1
                return Move(Direction.random())
            if self.coop_mode == 1:
                self.coop_mode = 0
                return Wait()

        # We try to merge
        merge = self.knowledge.try_merge()
        if merge is not None:
            return merge

        # If we have green waste, we go put it at the green-yellow frontier
        for waste in self.inventory:
            if waste.color > self.color:
                move = self.knowledge.try_move(Direction.RIGHT)
                if move is not None:
                    return move

                if self.knowledge.perception[Direction.RIGHT].color == Color.YELLOW:
                    drop = self.knowledge.try_drop(waste)
                    if drop is not None:
                        self.target = self.get_true_pos()
                        return drop

                return Move(Direction.random(exclude={Direction.RIGHT, Direction.LEFT}))

        # If we can pick a waste, we do it
        pick = self.knowledge.try_pick()
        if pick is not None:
            return pick

        # If there is a waste in an adjacent cell, we move to that cell
        moveOrWait = self.knowledge.look_around()
        if moveOrWait is not None:
            return moveOrWait

        # If we have exactly one waste of our color, and there is an agent of our color having exactly one waste of our color near, we want to cooperate
        if len(self.inventory) == 1:
            for waste in self.inventory:
                if waste.color == self.color:
                    for direction in self.knowledge.perception:
                        if (
                            direction != Direction.NONE
                            and (agent := self.knowledge.perception[direction].agent) is not None
                            and agent.color == self.color
                            and len(agent.inventory) == 1
                        ):
                            for other_waste in agent.inventory:
                                if other_waste.color == self.color:
                                    # we want to cooperate
                                    drop = self.knowledge.try_drop(waste)
                                    if drop is not None:
                                        self.coop_mode = 2
                                        return drop

        # We follow the patrol cycle
        move = self.next_patrol_direction()
        if move is not None:
            return move

        return Move(Direction.random())


class YellowCommunicationRuleBasedAgent(CommunicationAgent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
        self.knowledge = AllKnowledge()
        self.patrol_direction = Direction.DOWN  # At start, it will go down, then up, then down, etc.
        self.coop_mode = 0

    def deliberate(self) -> Action:
        """
        Always merge if possible,
        Move right to deposit waste if possible,
        Drop waste if possible,
        Finally move randomly.
        """

        if self.coop_mode > 0:
            if self.coop_mode == 2:  # we want to move
                self.coop_mode = 1
                return Move(Direction.random())
            if self.coop_mode == 1:
                self.coop_mode = 0
                return Wait()

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

                if self.knowledge.perception[Direction.RIGHT].color == Color.RED:
                    drop = self.knowledge.try_drop(waste)
                    if drop is not None:
                        self.target = self.get_true_pos()
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

        # If we have exactly one waste of our color, and there is an agent of our color having exactly one waste of our color near, we want to cooperate
        if len(self.inventory) == 1:
            for waste in self.inventory:
                if waste.color == self.color:
                    for direction in self.knowledge.perception:
                        if (
                            direction != Direction.NONE
                            and (agent := self.knowledge.perception[direction].agent) is not None
                            and agent.color == self.color
                            and len(agent.inventory) == 1
                        ):
                            for other_waste in agent.inventory:
                                if other_waste.color == self.color:
                                    # we want to cooperate
                                    drop = self.knowledge.try_drop(waste)
                                    if drop is not None:
                                        self.coop_mode = 2
                                        return drop

        # If we have a target, we go to it
        target_information = self.information.informations["TargetInformation"]
        assert isinstance(target_information, TargetInformation)

        if len(target_information.targets) > 0:  # we have a target
            xtarget, ytarget = target_information.targets[0]
            x, y = self.get_true_pos()
            dist = abs(xtarget - x) + abs(ytarget - y)
            action = None
            if dist < 2:  # we are already here, we remove it from targets
                target_information.targets.pop(0)
            else:
                action = go_toward_target(x, y, xtarget, ytarget)

            if action is not None:
                return action

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
        if self.patrol_direction not in self.knowledge.perception or (
            (waste := self.knowledge.perception[self.patrol_direction].agent) is not None and waste.color == Color.YELLOW
        ):
            self.patrol_direction = Direction.UP if self.patrol_direction == Direction.DOWN else Direction.DOWN

        # We try to move towards cycle direction
        move = self.knowledge.try_move(self.patrol_direction)
        if move is not None:
            return move

        return Move(Direction.random())


class RedCommunicationRuleBasedAgent(CommunicationAgent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
        self.knowledge = AllKnowledge()
        self.patrol_direction = Direction.DOWN  # At start, it will go down, then up, then down, etc.

    def deliberate(self) -> Action:
        """
        Try to pick red waste,
        Move to the dump if has red waste,
        Else move randomly.
        """

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

        # We try to pick red waste
        pick = self.knowledge.try_pick()
        if pick is not None:
            return pick

        # If red waste in adjacent cell, move to that cell
        move = self.knowledge.look_around()
        if move is not None:
            return move

        target_information = self.information.informations["TargetInformation"]
        assert isinstance(target_information, TargetInformation)

        # If we have a target, we go to it
        if len(target_information.targets) > 0:  # we have a target
            xtarget, ytarget = target_information.targets[0]
            x, y = self.get_true_pos()
            dist = abs(xtarget - x) + abs(ytarget - y)
            action = None
            if dist < 2:  # we are already here, we remove it from targets
                target_information.targets.pop(0)
            else:
                action = go_toward_target(x, y, xtarget, ytarget)

            if action is not None:
                return action

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
        if self.patrol_direction not in self.knowledge.perception or (
            (waste := self.knowledge.perception[self.patrol_direction].agent) is not None and waste.color == Color.RED
        ):
            self.patrol_direction = Direction.UP if self.patrol_direction == Direction.DOWN else Direction.DOWN

        # We try to move towards cycle direction
        move = self.knowledge.try_move(self.patrol_direction)
        if move is not None:
            return move

        return Move(Direction.random())
