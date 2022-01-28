import gym
import numpy as np
from gym import spaces
from treys import Card
from treys import Evaluator

from generator import hand_generator


class PokerEnv(gym.Env):
    metadata = {"render.modes": ["human", "rgb_array"], "video.frames_per_second": 500}

    def __init__(self):
        # gym environment
        self.evaluator = Evaluator()
        self.spec = None
        self.num_envs = 1
        self.reward_range = np.array([-1, 1])
        self.action_space = spaces.Box(low=-1, high=1, shape=(2,))
        # decide the raise amount seperately? --> maybe using loss function to calculate best amount

        self.observation_space = spaces.Box(low=-1, high=1, shape=(2,))
        """
        observation space
        {
            [own data, eval score]
            ["player 1", action(1-4), (amount of raises if any)],
            ["player 2", action(1-4), (amount of raises if any)],
            
            [1990, 0],
            [2, 10],
            [3, 0]
        }
        
        same issue with action space (raise amount)
        """
        self.reset()

    
    def calculate_reward(self):
        pass
    
    def evaluate(self, data, cards_revealed=3):
        community_cards = [Card.new(x) for x in data[0][0:cards_revealed]]
        score_list = []
        for x in data[1]:
            hand = [Card.new(y) for y in x]
            score_list.append(7463 - self.evaluator.evaluate(community_cards, hand))
            
        return score_list
        
    def step(self):
        pass

    def reset(self):
        pass
    
if __name__ == "__main__":
    poker = PokerEnv()
    print(poker.evaluate(hand_generator(1), cards_revealed=3))