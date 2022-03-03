import gym
import random
import numpy as np
from gym import spaces

from texasholdem import TexasHoldEm
from texasholdem.game.game import Player
from texasholdem.game.hand_phase import HandPhase
from texasholdem.game.action_type import ActionType
from texasholdem.game.player_state import PlayerState

from agent import RandomAgent, CrammerAgent


class PokerEnv(gym.Env):
    metadata = {"render.modes": ["human", "rgb_array"], "video.frames_per_second": 120}

    def __init__(self, buy_in=500, big_blind=5, small_blind=2, num_players=6):
        # poker
        self.buy_in = buy_in
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.num_players = num_players  # num_players - 1 == hardcoded players
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

        self.string_to_action = {
            ActionType.CALL: 0,
            ActionType.RAISE: 1,
            ActionType.CHECK: 2,
            ActionType.FOLD: 3,
        }

        self.suit_to_int = {
            "s": 1,  # spades
            "h": 2,  # hearts
            "d": 3,  # diamonds
            "c": 4,  # clubs
        }

        self.card_num_to_int = {"T": 9, "J": 10, "Q": 11, "K": 12, "A": 13}

        self.max_value = buy_in * num_players
        self.previous_round_history = None

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

        card_space = spaces.Tuple((spaces.Discrete(14), spaces.Discrete(5)))
        player_card_space = spaces.Tuple((card_space,) * 2)
        self.observation_space = spaces.Dict(
            {
                "actions": spaces.Tuple(
                    (self.action_space,) * self.num_hardcoded_players
                ),  # all opponents actions
                "active": spaces.MultiBinary(num_players),  # [0, 1, 1, 0, 1, 0]
                "chips": spaces.Tuple(
                    (spaces.Discrete(self.max_value),) * self.num_hardcoded_players
                ),  # every player's chips
                "community_cards": spaces.Tuple((card_space,) * 5),  # ((1, 2), ...)
                "player_cards": spaces.Tuple(
                    (player_card_space,) * num_players
                ),  # ((1, 2), (3, 2))
                "max_raise": spaces.Discrete(self.max_value),  # player.chips
                "min_raise": spaces.Discrete(self.big_blind),
                "pot": spaces.Discrete(self.max_value),  # pot.amount
                "player_stacks": spaces.Tuple(
                    (spaces.Discrete(self.max_value),) * num_players
                ),  # pot_commits for every player in the whole game
                "stage_bettings": spaces.Tuple(
                    (spaces.Discrete(self.max_value),) * num_players
                ),  # pot_commits for every player in the current stage
            }
        )

        self.reset()

    def add_agent(self, agent):
        self.cnt += 1
        self.hardcoded_players[self.cnt] = agent

    def calculate_reward(self):
        # calculate the total number of pot commits for each player
        pot_commits = {}
        for pot in self.game.pots:
            player_amount = pot.player_amounts_without_remove
            for player_id in player_amount:
                if player_id in pot_commits:
                    pot_commits[player_id] += player_amount[player_id]
                else:
                    pot_commits[player_id] = player_amount[player_id]
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
                max(
                    min(
                        payout_percentage * self.reward_multiplier,
                        1,
                    ),
                    -1,
                ),
                3,
            )
        return percent_payouts

    def get_observations(self):
        """
        "actions": spaces.Tuple(
            (self.action_space,) * self.num_hardcoded_players
        ),  # all opponents actions
        "active": spaces.MultiBinary(num_players),  # [0, 1, 1, 0, 1, 0]
        "chips": spaces.Tuple(
            (spaces.Discrete(self.max_value),) * self.num_hardcoded_players
        ),  # every player's chips
        "community_cards": spaces.Tuple((card_space,) * 5),  # ((1, 2), ...)
        "player_cards": spaces.Tuple(
            (player_card_space,) * num_players
        ),  # ((1, 2), (3, 2))
        "max_raise": spaces.Discrete(self.max_value),  # player.chips
        "min_raise": spaces.Discrete(self.big_blind),
        "pot": spaces.Discrete(self.max_value),  # pot.amount
        "player_stacks": spaces.Tuple(
            (spaces.Discrete(self.max_value),) * num_players
        ),  # pot_commits for every player in the whole game
        "stage_bettings": spaces.Tuple(
            (spaces.Discrete(self.max_value),) * num_players
        ),  # pot_commits for every player in the current stage

        """
        observations = {}
        current_round_history = self.game.hand_history[self.game.hand_phase]
        if self.game.hand_phase == HandPhase.PREHAND:
            current_round_history = self.previous_round_history

        actions = list(
            map(
                lambda x: self.string_to_action[x.action_type],
                current_round_history.actions,
            )
        )

        active = []
        chips = []
        winners = None
        if not self.game.is_hand_running() and not self.game._is_hand_over():
            winners = self.game.hand_history[HandPhase.SETTLE].winners
            # modify it later
            active = [1, 0, 0, 0, 0, 0]

        for x in self.game.players:
            if winners is None:
                active.append(int(x.state != PlayerState.OUT))
            chips.append(x.chips)

        community_cards = [(0, 0)] * 5
        for i in range(len(self.game.board)):
            card = list(str(self.game.board[i]))
            if self.card_num_to_int.get(card[0], 0):
                card[0] = self.card_num_to_int[card[0]]
            else:
                card[0] = int(card[0]) - 1

            card[1] = self.suit_to_int[card[1]]
            community_cards[i] = tuple(card)

        observations.update(
            actions=actions,
            active=active,
            chips=chips,
            community_cards=tuple(community_cards),
        )

        # print(self.game.hand_history[self.game.hand_phase])
        self.previous_round_history = current_round_history
        return observations

    def step(self, action):
        """
        Standard gym env step function. Each step is a round of everyone has placed their bets
        """

        # At the initial call of step, our agent gives an action and a value.
        #
        # action in {0: ActionType.CALL,
        #            1: ActionType.RAISE,
        #            2: ActionType.CHECK,
        #            3: ActionType.FOLD}
        # val in [0, infty]
        
        action, val = action
        done = not self.game.is_hand_running()

        # If action is not raise, then val is None.
        if action != 2:
            val = None
        else:
            current_player: Player = list(
                filter(
                    lambda x: x.player_id == self.game.current_player,
                    self.game.players,
                )
            )[0]
            # starting and the model choose to raise
            if self.fresh_start:
                self.fresh_start = False
                val = min(max(self.big_blind, val), current_player.chips)

            # not starting and the model choose to raise
            else:
                previous_pot_commit = self.game.pots[0].raised
                val = min(max(previous_pot_commit, val), current_player.chips)

            # make sure we all that to the prev commits
            val += previous_pot_commit

        if not done:
            # Our agent takes the action.
            self.game.take_action(self.action_to_string[action], val)

            # Take the other agent actions (and values) in the game.
            while self.game.current_player != 0:
                h_bet, h_val = self.hardcoded_players[
                    self.game.current_player
                ].calculate_action()
                self.game.take_action(h_bet, h_val)

        # We need to make the observation!
        # FIGURE OUT OBSERVATION SPACE HERE!

        observation = self.get_observations()
        
        reward = self.calculate_reward()
        info = None

        # return observation, reward, done, info (optional)
        return observation, reward, done, info

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


def main():
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
        # print(poker.calculate_reward())
        print(poker.get_observations())


if __name__ == "__main__":
    # function runtime: 0.00184 s (pretty fast for 1 game/hand)
    main()
