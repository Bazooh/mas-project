from action import Action, Move
from agent import Agent
from utils import Direction


class NaiveAgent(Agent):
    def deliberate(self) -> Action:
        """
        Always merge if possible,
        Move right to deposit waste if possible,
        Drop waste if possible,
        Finally move randomly.
        """
        merge = self.try_merge()
        if merge is not None:
            return merge

        for waste in self.inventory:
            if waste.color > self.color:
                move = self.try_move(Direction.RIGHT)
                if move is not None:
                    return move

                drop = self.try_drop(waste)
                if drop is not None:
                    return drop

                return Move(Direction.random(exclude={Direction.RIGHT}))

        pick = self.try_pick()
        if pick is not None:
            return pick

        return Move(Direction.random())
