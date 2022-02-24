import random
import gym
import numpy as np
from gym import spaces
from treys import Card
from treys import Evaluator
from itertools import groupby
from operator import itemgetter
from texasholdem import TexasHoldEm
from texasholdem.game.player_state import PlayerState


from card_generator import hand_generator


class PokerEnv(gym.Env):
    metadata = {"render.modes": ["human", "rgb_array"], "video.frames_per_second": 120}

    def __init__(self, buy_in=500, big_blind=5, small_blind=2, num_players=2):
        # poker
        self.evaluator = Evaluator()
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.game = TexasHoldEm(
            buyin=buy_in,
            big_blind=big_blind,
            small_blind=small_blind,
            max_players=num_players,
        )
        self.action_to_string = {1: "call", 2: "raise", 3: "check", 4: "fold"}

        # TODO: gym environment
        self.spec = None
        self.num_envs = 1

        self.reward_range = np.array([-1, 1])
        self.action_space = spaces.MultiDiscrete(
            [
                3,
                buy_in,
            ],
        )

        card_space = spaces.Tuple((spaces.Discrete(13), spaces.Discrete(4)))
        player_card_space = spaces.Tuple((card_space,) * 2)
        self.observation_space = spaces.Dict(
            {
                "action": self.action_space,
                "active": spaces.MultiBinary(num_players),
                # "button": spaces.Discrete(num_players),
                "call": spaces.Discrete(buy_in),
                "community_cards": spaces.Tuple((card_space,) * 5),
                "player_cards": spaces.Tuple((player_card_space,) * num_players),
                "max_raise": spaces.Discrete(buy_in),
                "min_raise": spaces.Discrete(buy_in),
                "pot": spaces.Discrete(buy_in),
                "player_stacks": spaces.Tuple((spaces.Discrete(buy_in),) * num_players),
                "stage_bettings": spaces.Tuple(
                    (spaces.Discrete(buy_in),) * num_players
                ),
            }
        )
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
            [0, 1, 2, 3, ..., 1000]
        }
        

        """
        self.reset()

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

        Should we consider actions or not?

        ---FROM neuron_poker---
        calculate reward from previous game's winnings?


        reward = self.funds_history.iloc[-1, self.acting_agent] - self.funds_history.iloc[
                -2, self.acting_agent]


        ---FROM holdem---
        Looks like just getting chip amounts for each player, not sure what this has to do with rewards...

        rew = [player.stack for player in self._seats]

        ---FROM clubs_gym---
        seems like the reward has nothing to do with the action provided by the model, similar as above...

        # pot_commits are pot commits for each player
        def _payouts(self) -> List[int]:
            # players that have folded lose their bets (MOSTLY USED)
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

        reward output: [-2, 0, 9, -4, 0, -4, 9, -4, -4]
        """

        """
        ---Adaith's Design ---
        We could try basing a seperate design of a reward function based of a simple neural network with data from the following:

        1. Your Pot
        2. Opponents Pot Size
        3. Previous Pot Winner's betting amount
        4. Previous Winner's Hand

        We could base the final node output on binary cross entropy, saying that if you minimised the loss of your own chips or maximized your winnings 
        it should correspond to a 1, else should be 0;

        base design:

        4 Noded Input --> hidden Layers --> Output Node

        This could be trained on a realtime basis whenever a game is played. As even if the robot loses, this reward function can be updated with the robots moves
        and the winning players moves.

        Brief Code Design:

        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras import layers
        from tensorflow.keras.optimizers.*

        #Function Should be called after 20 games worth of data
        #Epoch Number should be updated accordingly
        def rewardTrain(self):
            #Predefined model which well import
            model_path = ""
            model = create_model()
            model.load_weight(model_path)

            poker_inputs = self.get_input()
            poker_output = self.get_output()

            cp_callback = callbacks.ModelCheckpoint(filepath= model_path, save_weights_only = True, verbose= someVerboseYouWant)

            model.fit(poker_input, poker_outputs, epochs = 10, callbacks = [cp_callback])

        Brief inital model Desgin
        Add Layers to the model:
        def create_model:
            model_path = ""
            model = models.Sequential([
                layers.Dense(4, activation="relu"),
                layers.Dense(128, activation="relu"),
                layers.Dense(10, activation="relu")
            ])
            
            model.compile(loss='categorical_crossentropy',
                optimizer=RMSprop(lr=0.001),
                metrics=['accuracy])
                
            model.save(model_path);
        """
        # calculate the total number of pot commits for each player
        pot_commits = {}
        for d in [pot.player_amounts_without_remove for pot in self.game.pots]:
            for key in d:
                if key in pot_commits:
                    pot_commits[key] += d[key]
                else:
                    pot_commits[key] = d[key]

        # calculate the payouts
        # consider percentage of the player's stack ######
        payouts = {
            pot_commit[0]: -1
            * pot_commit[1]
            * (self.game.players[pot_commit[0]].state == PlayerState.OUT)
            for pot_commit in pot_commits.items()
        }
        player_active_list = {
            x.player_id: x.state != PlayerState.OUT for x in self.game.players
        }
        # print(payouts, player_active_list, pot_commits)

        # ask adu how raise should work (add up to pot or change pot value to raise value)
        if sum(player_active_list.values()) == 1:
            pot_total = sum(list(map(lambda x: x.amount, self.game.pots)))
            payouts = {
                player_id: payouts[player_id]
                + (self.game.players[player_id].state != PlayerState.OUT)
                * (pot_total - pot_commits[player_id])
                for player_id in player_active_list.keys()
            }

            return payouts
        # if last street played and still multiple players active
        # elif self.street >= self.num_streets:
        #     payouts = self._eval_round()
        #     payouts = [
        #         payout - pot_commit
        #         for payout, pot_commit in zip(payouts, self.pot_commits)
        #     ]
        #     return payouts
        # print(pot_commits, len(self.game.players))
        return payouts

    def step(self, action):
        # process action (space)
        action, val = action
        if action != 2:
            val = None
        else:
            if self.fresh_start:  # starting and the model choose to raise
                self.fresh_start = False
                val = max(5, val)
            else:  # not starting and the model choose to raise
                self.current_pot = sum([x.get_total_amount() for x in self.game.pots])
                previous_bet = self.current_pot - self.previous_pot
                val = max(previous_bet, val)
                self.previous_pot = self.current_pot

        # step through simulator
        self.game.take_action(self.action_to_string[action], val)

        # opponents turn
        # get obs
        # get reward
        # return observation, reward, done, info (optional)
        pass

    def render(self):
        pass

    def reset(self):
        self.game.start_hand()
        self.fresh_start = True
        self.previous_pot = self.big_blind + self.small_blind
        self.current_pot = 0

    def close(self):
        # some cleanups
        pass


if __name__ == "__main__":
    poker = PokerEnv(num_players=6)

    from texasholdem import TexasHoldEm
    from texasholdem.game.action_type import ActionType

    while poker.game.is_hand_running():
        lines = []
        for i in range(len(poker.game.pots)):
            lines.append(
                f"Pot {i}: {poker.game.pots[i].get_total_amount()} Board: {poker.game.board}"
            )

        while 1:
            # print(f"{bet} {val} is not valid for player {poker.game.current_player}")

            rand = random.random()
            # 15% chance to fold
            val = None
            if rand < 0.15:
                bet = ActionType.FOLD
            # 80% chance to call
            elif rand < 0.95:
                bet = ActionType.CALL
            # 5% to raise to min_raise
            else:
                bet = ActionType.RAISE
                val = random.randint(5, 30)
            if poker.game.validate_move(poker.game.current_player, bet, val):
                break

        print(
            f"{str(poker.game.hand_phase)[10:]}: Player {poker.game.current_player}, Chips: {poker.game.players[poker.game.current_player].chips}, Action - {str(bet)[11:].capitalize()}{f': {val}' if val else ''}"
        )
        poker.game.take_action(bet, val)
        print(poker.calculate_reward())

    # print(poker.evaluate(hand_generator(num_players=5), cards_revealed=3))
    # [551, 486, 555, 555, 2153]
