from typing import Union

import gym
import yaml
import numpy as np
from gym import spaces

from texasholdem import TexasHoldEm
from texasholdem.game.game import Player
from texasholdem.game.hand_phase import HandPhase
from texasholdem.game.action_type import ActionType
from texasholdem.game.player_state import PlayerState

from agent import RandomAgent, CrammerAgent


class PokerEnv(gym.Env):
    # for agent training
    metadata = {"render.modes": ["human", "rgb_array"], "video.frames_per_second": 120}

    def __init__(self, config=None, debug=False):
        # poker
        if config is None:
            with open("config.yaml") as f:
                config = yaml.load(f, Loader=yaml.FullLoader)["normal-six-player"]
        self.buy_in = config["stack"]
        self.small_blind = config["small-blind"]
        self.big_blind = config["big-blind"]
        self.num_players = config["players"]
        self.opponent_config = config["opponents"]
        self.max_value = self.buy_in * self.num_players

        self.debug = debug

        self.game = TexasHoldEm(
            buyin=self.buy_in,
            big_blind=self.big_blind,
            small_blind=self.small_blind,
            max_players=self.num_players,
            add_chips_when_lose=True,
        )

        # dictionary constants
        self.num_to_action = {
            0: ActionType.CALL,
            1: ActionType.RAISE,
            2: ActionType.CHECK,
            3: ActionType.FOLD,
        }
        self.action_to_num = {
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

        # step function
        self.agent_id = 0  # id for our own agent
        self.fresh_start = True
        self.previous_chips = {}

        # opponents
        self.opponents: dict[int, Union[RandomAgent, CrammerAgent]] = {}
        self.add_opponent()

        # gym environment
        self.spec = None
        self.num_envs = 1

        # reward
        self.reward_multiplier = 1.1
        self.reward_range = np.array([-1, 1])

        # action space
        self.action_space = spaces.MultiDiscrete(
            [
                4,
                self.max_value,
            ],
        )

        # observation space
        card_space = spaces.Tuple((spaces.Discrete(14), spaces.Discrete(5)))
        self.observation_space = spaces.Dict(
            {
                "actions": spaces.Tuple(
                    (
                        spaces.Tuple(
                            (
                                spaces.Discrete(5, start=-1),  # -1 for padding
                                spaces.Discrete(self.max_value),
                            )
                        ),
                    )
                    * self.num_players
                ),  # all opponents actions
                "active": spaces.MultiBinary(self.num_players),  # [0, 1, 1, 0, 1, 0]
                "chips": spaces.Tuple(
                    (spaces.Discrete(self.max_value),) * self.num_players
                ),  # every player's chips
                "community_cards": spaces.Tuple((card_space,) * 5),  # ((1, 2)) * 5
                "player_card": spaces.Tuple((card_space,) * 2),  # ((3, 2)) * 2
                "max_raise": spaces.Discrete(self.max_value),  # player.chips
                "min_raise": spaces.Discrete(self.big_blind),
                "pot": spaces.Discrete(self.max_value),  # pot.amount
                "player_stacks": spaces.Tuple(
                    (spaces.Discrete(self.max_value),) * self.num_players
                ),  # pot_commits for every player in the whole game
                "stage_bettings": spaces.Tuple(
                    (spaces.Discrete(self.max_value),) * self.num_players
                ),  # pot_commits for every player in the current stage
            }
        )

    def add_opponent(self):
        # temporarily adding all random agents
        opponents = []

        random_agent = self.opponent_config["random-agent"]
        for _ in range(random_agent):
            opponents.append(RandomAgent(self.game))

        crammer_agent = self.opponent_config["crammer-agent"]
        for _ in range(crammer_agent):
            opponents.append(CrammerAgent(self.game, self.num_to_action))

        reserved = False
        for i in range(len(opponents)):
            if i == self.agent_id:
                reserved = True
            if not reserved:
                self.opponents[i] = opponents[i]
            else:
                self.opponents[i + 1] = opponents[i]

    def card_to_observation(self, card):
        card = list(str(card))
        if self.card_num_to_int.get(card[0], 0):
            card[0] = self.card_num_to_int[card[0]]
        else:
            card[0] = int(card[0]) - 1
        card[1] = self.suit_to_int[card[1]]
        return tuple(card)

    def get_winners(self):
        if self.game.hand_history[HandPhase.SETTLE]:
            winners = self.game.hand_history[HandPhase.SETTLE].pot_winners

            # player_id: (winning_chips, score, pot_id)
            return {x[1][2][0]: (x[1][0], x[1][1], x[0]) for x in winners.items()}
        return None

    def get_reward(self, pot_commits: dict):
        # calculate the total number of pot commits for each player
        player_active_dict = {
            x.player_id: x.state != PlayerState.OUT and x.state != PlayerState.SKIP
            for x in self.game.players
        }

        # calculate the payouts
        payouts = {
            pot_commit[0]: -1 * pot_commit[1] * (not player_active_dict[pot_commit[0]])
            for pot_commit in pot_commits.items()
        }

        # calculate winners
        winners = self.get_winners()

        # everyone but one folded / all-in
        if sum(player_active_dict.values()) == 1:
            pot_total = sum(list(map(lambda x: x.amount, self.game.pots)))
            payouts = {
                player_id: payouts[player_id]
                + player_active_dict[player_id] * (pot_total - pot_commits[player_id])
                for player_id in player_active_dict.keys()
            }
        # if last street played and still multiple players active
        elif not self.game.is_hand_running() and not self.game._is_hand_over():
            new_payouts = {}
            for player_payout in payouts.items():
                # if player folded earlier
                if player_payout[1] != 0:
                    new_payouts[player_payout[0]] = player_payout[1]
                # if player wins
                elif winners.get(player_payout[0]) is not None:
                    new_payouts[player_payout[0]] = winners.get(player_payout[0])[0]
                # if player stay to the end and loses
                else:
                    new_payouts[player_payout[0]] = -pot_commits[player_payout[0]]
            payouts = new_payouts

        # calculate percentage of the player's stack
        percent_payouts = {}
        for player in self.game.players:
            current_player_id = player.player_id
            if winners and winners.get(current_player_id) is not None:
                payout_percentage = winners[current_player_id][0] / (
                    self.previous_chips[current_player_id]
                    - pot_commits[current_player_id]
                    + 0.001
                )
            else:
                payout_percentage = payouts[current_player_id] / (
                    self.previous_chips[current_player_id]
                    - payouts[current_player_id]
                    + 0.001
                )

            if player.chips == 0:
                percent_payouts[current_player_id] = -1
            else:
                percent_payouts[current_player_id] = round(
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

    def get_observations(
        self, current_player_id: int, pot_commits: dict, stage_pot_commits: dict
    ):
        observations = {}

        # actions
        current_round_history = self.game.hand_history[self.game.hand_phase]
        if self.game.hand_phase == HandPhase.PREHAND:
            current_round_history = self.game.hand_history.get_last_history()
        # prefill action list
        actions = [(-1, 0)] * self.num_players
        for player_action in current_round_history.actions:
            actions[player_action.player_id] = (
                self.action_to_num[player_action.action_type],  # action
                player_action.value if player_action.value is not None else 0,  # value
            )

        # active + chips
        active = []
        chips = []
        winners = None
        # if last street played and still multiple players active
        if not self.game.is_hand_running() and not self.game._is_hand_over():
            winners = self.game.hand_history[HandPhase.SETTLE].pot_winners
            active = [0] * self.num_players
            for winner_id in winners.keys():
                active[winner_id] = 1

        for x in self.game.players:
            if winners is None:
                active.append(int(x.state != PlayerState.OUT))
            chips.append(x.chips)

        # community cards
        community_cards = [(0, 0)] * 5
        for i in range(len(self.game.board)):
            card = self.game.board[i]
            community_cards[i] = self.card_to_observation(card)

        # player hand
        player_card = ((0, 0),) * 2
        if self.game.hand_phase != HandPhase.PREFLOP:
            player_card = tuple(
                map(
                    lambda x: self.card_to_observation(x),
                    self.game.hands[current_player_id],
                )
            )

        # update observations
        observations.update(
            actions=tuple(actions),
            active=tuple(active),
            chips=tuple(chips),
            community_cards=tuple(community_cards),
            player_card=player_card,
            max_raise=self.game.players[current_player_id].chips,
            min_raise=self.game.pots[0].raised,
            pot=sum(map(lambda x: x.amount, self.game.pots)),
            player_stacks=tuple(pot_commits.values()),
            stage_bettings=tuple(stage_pot_commits.values()),
        )

        return observations

    def step(self, action, format_action=True):
        """
        Standard gym env step function. Each step is a round of everyone has placed their bets
        """
        action, val = action
        current_player: Player = list(
            filter(
                lambda x: x.player_id == self.game.current_player,
                self.game.players,
            )
        )[0]

        if action == 1 or action == ActionType.RAISE:
            # start of the game and the model choose to raise
            previous_pot_commit = self.game.pots[0].raised
            if self.fresh_start:
                self.fresh_start = False
                val = max(self.big_blind, val)

            # middle of the game and the model choose to raise
            else:
                val = max(previous_pot_commit, val)

            # make sure we add raise value to the prev commits since the game simulator is calculate raise differently
            if format_action:
                val += previous_pot_commit

        else:
            val = None

        # convert action
        if format_action:
            action = self.num_to_action[action]

        if action == ActionType.RAISE and val >= current_player.chips:
            # print(val)
            action = ActionType.ALL_IN
            val = None

        if self.debug:
            print(
                f"{str(self.game.hand_phase)[10:]}: Player {self.game.current_player}, Chips: {self.game.players[self.game.current_player].chips}, Action - {str(action)[11:].capitalize()}{f': {val}' if val else ''}"
            )

        # agent take action
        self.game.take_action(action, val)
        done = not self.game.is_hand_running()

        if not done:
            # Take the other agent actions (and values) in the game.
            while self.game.current_player != self.agent_id and not done:
                action, val = self.opponents[
                    self.game.current_player
                ].calculate_action()
                if self.debug:
                    print(
                        f"{str(self.game.hand_phase)[10:]}: Player {self.game.current_player}, Chips: {self.game.players[self.game.current_player].chips}, Action - {str(action)[11:].capitalize()}{f': {val}' if val else ''}"
                    )

                self.game.take_action(action, val)
                done = not self.game.is_hand_running()

        # observations
        pot_commits = {}
        stage_pot_commits = {}
        for pot in self.game.pots:
            player_amount = pot.player_amounts_without_remove
            stage_amount = pot.player_amounts  ### FIXED NEEDED HERE

            for player_id in player_amount:
                if player_id in pot_commits:
                    pot_commits[player_id] += player_amount[player_id]
                else:
                    pot_commits[player_id] = player_amount[player_id]

                if player_id in stage_pot_commits:
                    stage_pot_commits[player_id] += stage_amount.get(player_id, 0)
                else:
                    stage_pot_commits[player_id] = (
                        stage_amount[player_id] if stage_amount.get(player_id, 0) else 0
                    )
        pot_commits = dict(sorted(pot_commits.items()))
        stage_pot_commits = dict(sorted(stage_pot_commits.items()))
        observation = self.get_observations(
            current_player.player_id, pot_commits, stage_pot_commits
        )

        # reward + info
        reward = self.get_reward(pot_commits)
        info = None

        return observation, reward, done, info

    def render(self):
        pass

    def reset(self):
        self.fresh_start = True
        for x in self.game.players:
            self.previous_chips.update({x.player_id: x.chips})
        # self.previous_chips = {x.player_id: x.chips for x in self.game.players}

        self.game.start_hand()

        # take opponent actions in the game
        done = not self.game.is_hand_running()
        while self.game.current_player != self.agent_id and not done:
            action, val = self.opponents[self.game.current_player].calculate_action()
            if self.debug:
                print(
                    f"{str(self.game.hand_phase)[10:]}: Player {self.game.current_player}, Chips: {self.game.players[self.game.current_player].chips}, Action - {str(action)[11:].capitalize()}{f': {val}' if val else ''}"
                )

            self.game.take_action(action, val)
            done = not self.game.is_hand_running()

        # calculate + return information
        current_player: Player = list(
            filter(
                lambda x: x.player_id == self.game.current_player,
                self.game.players,
            )
        )[0]

        pot_commits = {}
        stage_pot_commits = {}
        for pot in self.game.pots:
            player_amount = pot.player_amounts_without_remove
            stage_amount = pot.player_amounts
            for player_id in player_amount:
                if player_id in pot_commits:
                    pot_commits[player_id] += player_amount[player_id]
                else:
                    pot_commits[player_id] = player_amount[player_id]

                if player_id in stage_pot_commits:
                    stage_pot_commits[player_id] += stage_amount[player_id]
                else:
                    stage_pot_commits[player_id] = (
                        stage_amount[player_id] if stage_amount.get(player_id, 0) else 0
                    )
        observation = self.get_observations(
            current_player.player_id, pot_commits, stage_pot_commits
        )
        reward = self.get_reward(pot_commits)
        return observation, reward, done, None

    def close(self):
        # some cleanups
        print("Environment is closing...")


def main():
    # with open("config.yaml") as f:
    #     config = yaml.load(f, Loader=yaml.FullLoader)
    # poker = PokerEnv(config=config["hard-six-player"])

    poker = PokerEnv(debug=True)
    agent = CrammerAgent(poker.game)

    # reset environment
    obs, reward, done, info = poker.reset()

    # start step loop
    games_to_play = 0
    while not done:
        action, val = agent.calculate_action()
        obs, reward, done, info = poker.step((action, val), format_action=False)

        if done:
            print(
                f"\nchips: {obs['chips']}",
                f"\nreward: {tuple(reward.values())}",
                f"\npots: {poker.game.pots}",
            )
            games_to_play += 1
            obs, reward, done, info = poker.reset()
            print(
                f"\ndone: {done}",
                f"\nchips: {obs['chips']}",
                f"\nreward: {tuple(reward.values())}",
                f"\npots: {poker.game.pots}",
            )

        if games_to_play > 10:
            break

    poker.close()


if __name__ == "__main__":
    # function runtime: 0.00184 s (pretty fast for 1 game/hand)
    import pstats
    import cProfile

    with cProfile.Profile() as pr:
        main()

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.dump_stats("profile.prof")
    # use `snakeviz .\profile.prof` to see stats
