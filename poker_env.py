"""
This is the game demo(bot) from the texasholdem library

slow but seems to work
"""


import gym
import numpy as np
from gym import spaces
from treys import Card
from treys import Evaluator

from generator import hand_generator


class PokerEnv(gym.Env):
    metadata = {"render.modes": ["human", "rgb_array"], "video.frames_per_second": 120}

    def __init__(self):
        # poker
        self.evaluator = Evaluator()

        # TODO: gym environment
        self.spec = None
        self.num_envs = 1

        self.reward_range = np.array([-1, 1])
        self.action_space = spaces.Box(low=-1, high=1, shape=(2,))
        self.observation_space = spaces.Box(low=-1, high=1, shape=(2,))
        """
        observation space
        {
            [own data, eval score]
            ["player 1", action(1-4), (amount of raises if any)],
            ["player 2", action(1-4), (amount of raises if any)],
            
            [1, None],
            [2, 10],
            [3, None],
            [4, None]
        }
        
        same issue with action space (raise amount)
        should we decide the raise amount seperately? --> maybe using loss function to calculate best amount
        """

    def evaluate(self, data, cards_revealed=3):
        # 0 - 7462
        community_cards = [Card.new(x) for x in data[0][0:cards_revealed]]
        score_list = []
        for x in data[1]:
            hand = [Card.new(y) for y in x]
            score_list.append(7463 - self.evaluator.evaluate(community_cards, hand))

        return score_list

    def calculate_reward(self):
        # evaluate the good move or bad move
        
        """
        Goal: most chips
        Rounds: Pre-flop, flop, turn, river

        Limits: 10$-1000$, Increments of 10$

        Small/big blind(pre game bets), Call: match previous player's bet, Raise: increase previous player's bet, Check:
        decline to bet but still keep cards --> can only do if no one has bet yet (if any player
        bets, then this person has to make an action), Fold: lose cards and bets

        Low score + first:
        check -> call
        """
        pass

    def step(self):
        pass

    def render(self):
        pass

    def reset(self):
        pass

    def close(self):
        # some cleanups
        pass


if __name__ == "__main__":
    poker = PokerEnv()
    print(poker.evaluate(hand_generator(num_players=5), cards_revealed=3))
    # [551, 486, 555, 555, 2153]
