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


class BaseRuleBasedAgent(Agent):
    """
    For behaviors common to all colors rule based agents
    """

    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
        self.knowledge = AllKnowledge()
        self.patrol_horizontal_direction = Direction.RIGHT
        self.patrol_vertical_direction = Direction.DOWN
        self.coop_mode = 0

    def cooperate(self) -> Action | None:
        if self.coop_mode <= 0:
            return

        if self.coop_mode == 1:
            self.coop_mode = 0
            return Wait()

        if self.coop_mode == 2:  # we want to move
            self.coop_mode = 1
            return Move(Direction.random())

    def try_merge(self) -> Action | None:
        merge = self.knowledge.try_merge()
        if merge is not None:
            return merge

    def try_start_cooperation(self) -> Action | None:
        if len(self.inventory) != 1:
            return

        for waste in self.inventory:
            if waste.color != self.color:
                continue

            for direction in self.knowledge.perception:
                if (
                    direction == Direction.NONE
                    or (agent := self.knowledge.perception[direction].agent) is None
                    or agent.color != self.color
                    or len(agent.inventory) != 1
                ):
                    continue

                for other_waste in agent.inventory:
                    if other_waste.color == self.color:
                        # we want to cooperate
                        drop = self.knowledge.try_drop(waste)
                        if drop is not None:
                            self.coop_mode = 2
                            return drop

    def go_to_target(self) -> Action | None:
        return

    def next_patrol_direction_template(self, left_obstacle: Color | None, right_obstacle: Color | None) -> Action | None:
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

        if an obstacle is None, it means it is walls
        """
        if self.patrol_horizontal_direction == Direction.RIGHT:
            # we check if right cell is accessible, if so we go patrol_vertical_direction (and maybe change it) and next one will be left

            if (
                right_obstacle is not None
                and Direction.RIGHT in self.knowledge.perception
                and self.knowledge.perception[Direction.RIGHT].color == right_obstacle
            ) or (right_obstacle is None and Direction.RIGHT not in self.knowledge.perception):
                self.patrol_horizontal_direction = Direction.LEFT
                # possible to follow patrol_vertical_direction ?
                if self.patrol_vertical_direction in self.knowledge.perception:
                    return self.knowledge.try_move(self.patrol_vertical_direction)

                self.patrol_vertical_direction = (
                    Direction.DOWN if self.patrol_vertical_direction == Direction.UP else Direction.UP
                )
                return self.knowledge.try_move(self.patrol_vertical_direction)

            # we can go right
            return self.knowledge.try_move(Direction.RIGHT)

        elif self.patrol_horizontal_direction == Direction.LEFT:
            # we check if left cell is accessible, if so we go patrol_vertical_direction (and maybe change it) and next one will be right

            if (
                left_obstacle is not None
                and Direction.LEFT in self.knowledge.perception
                and self.knowledge.perception[Direction.LEFT].color == left_obstacle
            ) or (left_obstacle is None and Direction.LEFT not in self.knowledge.perception):
                self.patrol_horizontal_direction = Direction.RIGHT
                # possible to follow patrol_vertical_direction ?
                if self.patrol_vertical_direction in self.knowledge.perception:
                    return self.knowledge.try_move(self.patrol_vertical_direction)

                self.patrol_vertical_direction = (
                    Direction.DOWN if self.patrol_vertical_direction == Direction.UP else Direction.UP
                )
                return self.knowledge.try_move(self.patrol_vertical_direction)

            return self.knowledge.try_move(Direction.LEFT)


class GreenRuleBasedAgent(BaseRuleBasedAgent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)

    def next_patrol_direction(self):
        return self.next_patrol_direction_template(None, Color.YELLOW)

    def try_move_yellow(self):
        for waste in self.inventory:
            if waste.color > self.color:
                move = self.knowledge.try_move(Direction.RIGHT)
                if move is not None:
                    return move

                if self.knowledge.perception[Direction.RIGHT].color == Color.YELLOW:
                    drop = self.knowledge.try_drop(waste)
                    if drop is not None:
                        if isinstance(self, CommunicationAgent):
                            self.target = self.get_true_pos()
                        return drop

                return Move(Direction.random(exclude={Direction.RIGHT, Direction.LEFT}))

    def deliberate(self) -> Action:
        currentAction = None

        if currentAction is None:
            currentAction = self.cooperate()

        # We try to merge
        if currentAction is None:
            currentAction = self.try_merge()

        # If we have yellow waste, we go put it at the green-yellow frontier
        if currentAction is None:
            currentAction = self.try_move_yellow()

        # If we can pick a waste, we do it
        if currentAction is None:
            currentAction = self.knowledge.try_pick()

        # If there is a waste in an adjacent cell, we move to that cell
        if currentAction is None:
            currentAction = self.knowledge.look_around()

        # If we have exactly one waste of our color, and there is an agent of our color having exactly one waste of our color near, we want to cooperate
        if currentAction is None:
            currentAction = self.try_start_cooperation()

        # We follow the patrol cycle
        if currentAction is None:
            currentAction = self.next_patrol_direction()

        if currentAction is not None:
            return currentAction

        return Move(Direction.random())


class YellowRuleBasedAgent(BaseRuleBasedAgent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)

    def try_move_red(self):
        for waste in self.inventory:
            if waste.color > self.color:
                move = self.knowledge.try_move(Direction.RIGHT)
                if move is not None:
                    return move

                if self.knowledge.perception[Direction.RIGHT].color == Color.RED:
                    drop = self.knowledge.try_drop(waste)
                    if drop is not None:
                        if isinstance(self, CommunicationAgent):
                            self.target = self.get_true_pos()
                        return drop

                return Move(Direction.random(exclude={Direction.RIGHT, Direction.LEFT}))

    def next_patrol_direction(self):
        return self.next_patrol_direction_template(Color.GREEN, Color.RED)

    def deliberate(self) -> Action:
        currentAction = None

        if currentAction is None:
            currentAction = self.cooperate()

        # We try to merge
        if currentAction is None:
            currentAction = self.try_merge()

        # If we have red waste, we go put it at the red-yellow frontier
        if currentAction is None:
            currentAction = self.try_move_red()

        # If we can pick a waste, we do it
        if currentAction is None:
            currentAction = self.knowledge.try_pick()

        # If there is a waste in an adjacent cell, we move to that cell
        if currentAction is None:
            currentAction = self.knowledge.look_around()

        # If we have exactly one waste of our color, and there is an agent of our color having exactly one waste of our color near, we want to cooperate
        if currentAction is None:
            currentAction = self.try_start_cooperation()

        # if we have a target, we go to it (communications agents only)
        if currentAction is None:
            currentAction = self.go_to_target()

        # We follow the patrol cycle
        if currentAction is None:
            currentAction = self.next_patrol_direction()

        if currentAction is not None:
            return currentAction

        return Move(Direction.random())


class RedRuleBasedAgent(BaseRuleBasedAgent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
        self.patrol_direction = Direction.DOWN  # At start, it will go down, then up, then down, etc.

    def try_go_to_dump(self):
        if not self.inventory.is_empty():
            if self.knowledge.pos == self.knowledge.dump_pos:
                return Drop(self.inventory.wastes[0])

            move = self.knowledge.try_move(Direction.RIGHT)
            if move is not None:
                return move

            if self.knowledge.pos[1] == self.knowledge.dump_pos[1]:
                return Move(Direction.RIGHT)

            return Move(Direction.UP if self.knowledge.pos[1] < self.knowledge.dump_pos[1] else Direction.DOWN)

    def next_patrol_direction(self):
        return self.next_patrol_direction_template(Color.YELLOW, None)

    def deliberate(self) -> Action:
        currentAction = None

        # If we have red waste, move to the dump
        if currentAction is None:
            currentAction = self.try_go_to_dump()

        # We try to pick red waste
        if currentAction is None:
            currentAction = self.knowledge.try_pick()

        # If red waste in adjacent cell, move to that cell
        if currentAction is None:
            currentAction = self.knowledge.look_around()

        # if we have a target, we go to it (communications agents only)
        if currentAction is None:
            currentAction = self.go_to_target()

        # We follow the patrol cycle
        if currentAction is None:
            currentAction = self.next_patrol_direction()

        if currentAction is not None:
            return currentAction

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


class GreenCommunicationRuleBasedAgent(CommunicationAgent, GreenRuleBasedAgent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        CommunicationAgent.__init__(self, model, color)
        GreenRuleBasedAgent.__init__(self, model, color)


class YellowCommunicationRuleBasedAgent(CommunicationAgent, YellowRuleBasedAgent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        CommunicationAgent.__init__(self, model, color)
        YellowRuleBasedAgent.__init__(self, model, color)

    def go_to_target(self):
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


class RedCommunicationRuleBasedAgent(CommunicationAgent, RedRuleBasedAgent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        CommunicationAgent.__init__(self, model, color)
        RedRuleBasedAgent.__init__(self, model, color)

    def go_to_target(self) -> Action | None:
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
