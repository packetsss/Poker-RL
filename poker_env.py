import random
import gym
import numpy as np
from gym import spaces
from treys import Card
from treys import Evaluator
from itertools import groupby
from operator import itemgetter
from texasholdem import TexasHoldEm
from texasholdem.game.action_type import ActionType
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

        # gym environment
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
        player_active_dict = {
            x.player_id: x.state != PlayerState.OUT for x in self.game.players
        }

        # ask adu how raise should work (add up to pot or change pot value to raise value)
        if sum(player_active_dict.values()) == 1:
            pot_total = sum(list(map(lambda x: x.amount, self.game.pots)))
            payouts = {
                player_id: payouts[player_id]
                + (self.game.players[player_id].state != PlayerState.OUT)
                * (pot_total - pot_commits[player_id])
                for player_id in player_active_dict.keys()
            }

            return payouts
        # if last street played and still multiple players active
        """
        elif self.street >= self.num_streets:
            payouts = self._eval_round()
            payouts = [
                payout - pot_commit
                for payout, pot_commit in zip(payouts, self.pot_commits)
            ]
            return payouts
        """
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

    while poker.game.is_hand_running():
        lines = []
        for i in range(len(poker.game.pots)):
            lines.append(
                f"Pot {i}: {poker.game.pots[i].get_total_amount()} Board: {poker.game.board}"
            )

        while 1:
            rand = random.random()
            val = None
            if rand < 0.15:
                bet = ActionType.FOLD
            elif rand < 0.95:
                bet = ActionType.CALL
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
