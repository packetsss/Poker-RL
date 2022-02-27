import gym
import random
import numpy as np
from gym import spaces
from treys import Card
from treys import Evaluator
from texasholdem import TexasHoldEm
from texasholdem.game.action_type import ActionType
from texasholdem.game.hand_phase import HandPhase
from texasholdem.game.player_state import PlayerState

from card_generator import hand_generator
from agent import RandomAgent, CrammerAgent


class PokerEnv(gym.Env):
    metadata = {"render.modes": ["human", "rgb_array"], "video.frames_per_second": 120}

    def __init__(self, buy_in=500, big_blind=5, small_blind=2, num_players=6):
        # poker
        self.buy_in = buy_in
        self.evaluator = Evaluator()
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.num_players = num_players  # num_players - 1 == harcoded players.
        self.game = TexasHoldEm(
            buyin=buy_in,
            big_blind=big_blind,
            small_blind=small_blind,
            max_players=num_players,
        )

        self.action_to_string = {
            0: ActionType.CALL,
            1: ActionType.RAISE,
            2: ActionType.CHECK,
            3: ActionType.FOLD,
        }

        self.cnt = 0
        self.num_hardcoded_players = self.num_players - 1
        self.hardcoded_players = {}
        # 0 index reserved for our trained agent.
        # {
        #   1: agent,
        #   2: agent,
        #   3: agent,
        #   4: agent,
        #   5: agent
        # }

        # gym environment
        self.spec = None
        self.num_envs = 1

        # reward
        self.reward_multiplier = 1.2
        self.reward_range = np.array([-1, 1])

        # spaces
        self.action_space = spaces.MultiDiscrete(
            [
                4,
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

    def add_agent(self, agent):
        self.cnt += 1
        self.hardcoded_players[self.cnt] = agent

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
        player_active_dict = {
            x.player_id: x.state != PlayerState.OUT for x in self.game.players
        }
        payouts = {
            pot_commit[0]: -1 * pot_commit[1] * (not player_active_dict[pot_commit[0]])
            for pot_commit in pot_commits.items()
        }
        winners = None

        # ask adu how raise should work (add up to pot or change pot value to raise value)
        if sum(player_active_dict.values()) == 1:
            pot_total = sum(list(map(lambda x: x.amount, self.game.pots)))
            payouts = {
                player_id: payouts[player_id]
                + player_active_dict[player_id] * (pot_total - pot_commits[player_id])
                for player_id in player_active_dict.keys()
            }

        # if last street played and still multiple players active
        elif not self.game.is_hand_running() and not self.game._is_hand_over():
            winners = self.game.hand_history[HandPhase.SETTLE].winners

            new_payouts = {}
            for player_payout in payouts.items():
                # if player folded earlier
                if player_payout[1] != 0:
                    new_payouts[player_payout[0]] = player_payout[1]
                # if player wins
                elif winners.get(player_payout[0]) is not None:
                    new_payouts[player_payout[0]] = winners.get(player_payout[0])[1]
                # if player stay to the end and loses
                else:
                    new_payouts[player_payout[0]] = -pot_commits[player_payout[0]]
            payouts = new_payouts

        # TODO: consider percentage of the player's stack
        percent_payouts = {}
        for player in self.game.players:
            if winners and winners.get(player.player_id) is not None:
                payout_percentage = payouts[player.player_id] / (
                    player.chips - pot_commits[player.player_id]
                )
            else:
                payout_percentage = payouts[player.player_id] / (
                    player.chips - payouts[player.player_id]
                )

            percent_payouts[player.player_id] = round(
                np.clip(
                    payout_percentage * self.reward_multiplier,
                    -1,
                    1,
                ),
                3,
            )

        return percent_payouts

    def step(self, action):

        """ Standard gym env step function. Each step is a round (e.g. the
        preflop, flop, turn, river).
        
        """

        # At the initial call of step, our agent gives an action and a value.
        # 
        # action in {0: ActionType.CALL, 
        #            1: ActionType.RAISE, 
        #            2: ActionType.CHECK, 
        #            3: ActionType.FOLD}
        # val in [0, infty]
        action, val = action

        # If action is not raise, then val is None.
        if action != 2:
            val = None

        if self.game.is_hand_running():
            done = False
        else:
            done = True

        if not done:
            # Our agent takes the action.
            self.game.take_action(self.action_to_string[action], val)

            # Take the other agent actions (and values) in the game.
            while self.game.current_player != 0:
                h_bet, h_val = self.hardcoded_players[self.game.current_player].calculate_action()
                self.game.take_action(h_bet, h_val)



        # We need to make the observation!
        # FIGURE OUT OBSERVATION SPACE HERE!


        reward = self.calculate_reward()
        info = None

        # return observation, reward, done, info (optional)
        pass

    def render(self):
        pass

    def reset(self):
        self.game.start_hand()

        # # Take the other agent actions (and values) in the game.
        # while self.game.current_player != 0:
        #     h_bet, h_val = self.hardcoded_players[self.game.current_player].calculate_action()
        #     self.game.take_action(h_bet, h_val)

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
            if rand < 0.10:
                bet = ActionType.FOLD
            elif rand < 0.90:
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
