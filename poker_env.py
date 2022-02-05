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
        observation space: {
            ---OUR THOUGHTS---
            
            [own data, eval score, reward],
            ["player 1", action(1-4), (amount of raises if any)],
            ["player 2", action(1-4), (amount of raises if any)],
            
            [123, 1212], [1, None], [None, None], [None, None]
            [8465, 95], [2, 120], [1, None], [None, None]

            ---FROM neuron_poker---
            
            player data: Player specific information
                self.position = None
                self.equity_to_river_alive = 0
                self.equity_to_river_2plr = 0
                self.equity_to_river_3plr = 0
                self.stack = None
            
            community data: Data available to everybody
                self.current_player_position = [False] * num_players  # ix[0] = dealer
                self.stage = [False] * 4  # preflop, flop, turn, river
                self.community_pot = None
                self.current_round_pot = None
                self.active_players = [False] * num_players  # one hot encoded, 0 = dealer
                self.big_blind = 0
                self.small_blind = 0
                self.legal_moves = [0 for action in Action]
            
            stage data: Preflop, flop, turn and river
                self.calls = [False] * num_players  # index[0] = dealer
                self.raises = [False] * num_players
                self.min_call_at_action = [0] * num_players 
                self.contribution = [0] * num_players 
                self.stack_at_action = [0] * num_players
                self.community_pot_at_action = [0] * num_players
                
            ---FROM holdem--- (similar to our idea)
            self.observation_space = spaces.Tuple([
                # player info
                spaces.Tuple([                
                    spaces.MultiDiscrete([
                    1,                   # emptyplayer
                    n_seats - 1,         # seat
                    max_limit,           # stack
                    1,                   # is_playing_hand
                    max_limit,           # handrank
                    1,                   # playedthisround
                    1,                   # is_betting
                    1,                   # isallin
                    max_limit,           # last side pot
                    ]),
                    spaces.Tuple([
                    spaces.MultiDiscrete([    # hand
                        n_suits,          # suit, can be negative one if it's not avaiable.
                        n_ranks,          # rank, can be negative one if it's not avaiable.
                    ])
                    ] * n_pocket_cards)
                ] * n_seats),
                
                # community info
                spaces.Tuple([
                    spaces.Discrete(n_seats - 1), # big blind location
                    spaces.Discrete(max_limit),   # small blind
                    spaces.Discrete(max_limit),   # big blind
                    spaces.Discrete(max_limit),   # pot amount
                    spaces.Discrete(max_limit),   # last raise
                    spaces.Discrete(max_limit),   # minimum amount to raise
                    spaces.Discrete(max_limit),   # how much needed to call by current player.
                    spaces.Discrete(n_seats - 1), # current player seat location.
                    spaces.MultiDiscrete([        # community cards
                    n_suits - 1,          # suit
                    n_ranks - 1,          # rank
                    1,                     # is_flopped
                    ]),
                ] * n_stud),
                ])
            
            ---FROM clubs_gym--- (They uses dict obs space, looks decent)
            card_space = spaces.Tuple(
                (spaces.Discrete(num_ranks), spaces.Discrete(num_suits))
            )
            hole_card_space = spaces.Tuple((card_space,) * num_hole_cards)
            
            self.observation_space = spaces.Dict(
                {
                    "action": spaces.Discrete(num_players),
                    "active": spaces.MultiBinary(num_players),
                    "button": spaces.Discrete(num_players),
                    "call": spaces.Discrete(max_bet),
                    "community_cards": spaces.Tuple((card_space,) * comm_card_numb),
                    "hole_cards": spaces.Tuple((hole_card_space,) * num_players),
                    "max_raise": spaces.Discrete(max_bet),
                    "min_raise": spaces.Discrete(max_bet),
                    "pot": spaces.Discrete(max_bet),
                    "stacks": spaces.Tuple((spaces.Discrete(max_bet),) * num_players),
                    "street_commits": spaces.Tuple(
                        (spaces.Discrete(max_bet),) * num_players
                    ),
                })
        }
            
        action space: {
            ---OUR THOUGHTS---
            [1, None], call
            [2, 10], raise
            [3, None], check
            [4, None], fold
            
            same issue with action space (raise amount)
            should we decide the raise amount seperately? --> maybe using loss function to calculate best amount
            
            ---FROM neuron_poker---
            FOLD = 0
            CHECK = 1
            CALL = 2
            RAISE_3BB = 3
            RAISE_HALF_POT = 3
            RAISE_POT = 4
            RAISE_2POT = 5
            ALL_IN = 6
            SMALL_BLIND = 7
            BIG_BLIND = 8
            
            ---FROM holdem--- (similar to our idea)
            self.action_space = spaces.Tuple([
                spaces.MultiDiscrete([
                    3,                     # action_id
                    max_limit,             # raise_amount
                ]),
                ] * n_seats)
            
            ---FROM clubs_gym--- (looks too simple??)
            self.action_space = spaces.Discrete(max_bet)
        }
        

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
        ---OUR THOUGHTS---
        Goal: most chips
        Rounds: Pre-flop, flop, turn, river

        Limits: 10$-1000$, Increments of 10$

        Small/big blind(pre game bets), Call: match previous player's bet, Raise: increase previous player's bet, Check:
        decline to bet but still keep cards --> can only do if no one has bet yet (if any player
        bets, then this person has to make an action), Fold: lose cards and bets

        Low score + first:
        check -> call


        ---FROM neuron_poker---
        calculate reward from previous round's winnings?

        reward = self.funds_history.iloc[-1, self.acting_agent] - self.funds_history.iloc[
                -2, self.acting_agent]


        ---FROM holdem---
        Looks like just getting chip amounts for each player, not sure what this has to do with rewards...

        rew = [player.stack for player in self._seats]
        
        --FROM clubs_gym---
        seems like the reward has nothing to do with the action provided by the model, similar as above...
        
        # pot_commits are pot commits for each player
        def _payouts(self) -> List[int]:
            # players that have folded lose their bets
            payouts = [
                -1 * pot_commit * (not active)
                for pot_commit, active in zip(self.pot_commits, self.active)
            ]
            # if only one player left give that player all chips
            if sum(self.active) == 1:
                payouts = [
                    payout + active * (self.pot - pot_commit)
                    for payout, active, pot_commit in zip(
                        
                        payouts, self.active, self.pot_commits 
                    )
                ]
                return payouts
            # if last street played and still multiple players active
            elif self.street >= self.num_streets:
                payouts = self._eval_round() # see below
                payouts = [
                    payout - pot_commit
                    for payout, pot_commit in zip(payouts, self.pot_commits)
                ]
                return payouts
            return payouts
            
        def _eval_round(self):
            # payouts = [0] * self.num_players
            # grab array of hand strength and pot commits
            # sort hands by hand strength and pot commits
            # iterate over hand strength and pot commits from smallest to largest
            # give worst position player remainder chips
            # return payouts
            
        """

        pass

    def step(self):
        # return observation, reward, done, info (optional)
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
