from typing import Union

import yaml
import numpy as np
from gym import spaces, Env

from engine import TexasHoldEm
from engine.game.game import Player
from engine.game.hand_phase import HandPhase
from engine.game.action_type import ActionType
from engine.game.history import PrehandHistory
from engine.game.player_state import PlayerState

from agent import RandomAgent, CrammerAgent, RLAgent

from utils.flatten import flatten_spaces, flatten_array


class PokerEnv(Env):
    # for agent training
    metadata = {"render.modes": ["human", "rgb_array"], "video.frames_per_second": 120}

    def __init__(self, config=None, debug=False):
        # poker

        with open("config.yaml") as f:
            cf = yaml.load(f, Loader=yaml.FullLoader)
            env_constants = cf["environment-constants"]
            if config is None:
                config = cf["normal-six-player"]

        self.buy_in = config["stack"]
        self.small_blind = config["small-blind"]
        self.big_blind = config["big-blind"]
        self.num_players = config["players"]
        self.opponent_config = config["opponents"]
        self.buyin_limit = config["buyin_limit"]
        self.agent_id = config["agent_id"]  # id for our own agent

        self.max_value = self.buy_in * self.num_players * self.buyin_limit + 1
        self.debug = debug

        self.game = TexasHoldEm(
            buyin=self.buy_in,
            big_blind=self.big_blind,
            small_blind=self.small_blind,
            max_players=self.num_players,
            agent_id=self.agent_id,
            add_chips_when_lose=False,
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
        self.fresh_start = True
        self.previous_chips = {}
        self.default_pot_commit = {x.player_id: 0 for x in self.game.players}

        # gym environment
        self.spec = None
        self.num_envs = 1

        # reward
        self.reward_multiplier = env_constants["reward_multiplier"]
        self.winner_reward_multiplier = env_constants[
            "winner_reward_multiplier"
        ]  # amplify winner's reward to encourage winning

        self.reward_range = np.array([-1, 1])

        # action space
        self.action_space = spaces.Box(
            np.array([0, 0]), np.array([3, self.max_value - 1]), (2,), dtype=np.int32
        )

        # observation space
        card_space = spaces.Tuple((spaces.Discrete(14), spaces.Discrete(5)))
        obs_space = spaces.Dict(
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

        self.observation_space = flatten_spaces(obs_space)

        # opponents
        self.opponents: dict[int, Union[RandomAgent, CrammerAgent]] = {}
        self.add_opponent()

    def add_opponent(self):
        # temporarily adding all random agents
        opponents = []

        rl_agent: dict = self.opponent_config["rl-agent"]
        for name, paths in rl_agent.items():
            for path in paths:
                opponents.append(RLAgent(self, path, name, self.num_to_action))

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
                self.opponents[i].player_id = i
            else:
                self.opponents[i + 1] = opponents[i]
                self.opponents[i + 1].player_id = i + 1

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

    def get_pot_commits(self):
        pot_commits = self.default_pot_commit.copy()
        stage_pot_commits = self.default_pot_commit.copy()

        for pot in self.game.pots:
            player_amount = pot.player_amounts_without_remove
            stage_amount = pot.player_amounts

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
        return pot_commits, stage_pot_commits

    def get_reward(self, pot_commits: dict):
        # calculate the total number of pot commits for each player
        player_active_dict = {
            x.player_id: x.state not in (PlayerState.OUT, PlayerState.SKIP)
            for x in self.game.players
        }

        # calculate the payouts
        payouts = {
            pot_commit[0]: -1 * pot_commit[1] * (not player_active_dict[pot_commit[0]])
            for pot_commit in pot_commits.items()
        }

        # calculate winners
        winners = self.get_winners()

        # everyone but one folded
        if sum(player_active_dict.values()) == 1:
            pot_total = sum(list(map(lambda x: x.amount, self.game.pots)))
            payouts = {
                player_id: payouts[player_id]
                + player_active_dict[player_id] * (pot_total - pot_commits[player_id])
                for player_id in player_active_dict.keys()
            }

        # if last street played and still multiple players active or everyone all-in
        elif (not self.game.is_hand_running() and not self.game._is_hand_over()) or (
            sum(player_active_dict.values()) > 1 and winners is not None
        ):
            new_payouts = {}
            for player_payout in payouts.items():
                # if player folded earlier
                if player_payout[1] != 0:
                    new_payouts[player_payout[0]] = player_payout[1]

                # if player wins
                elif winners.get(player_payout[0]) is not None:
                    new_payouts[player_payout[0]] = (
                        self.game.players[player_payout[0]].chips
                        - self.previous_chips[player_payout[0]]
                    )  # this game chips - last game chips

                # if player stay to the end and loses
                else:
                    new_payouts[player_payout[0]] = -pot_commits[player_payout[0]]
            payouts = new_payouts

        # calculate percentage of the player's stack
        percent_payouts = {}
        for player in self.game.players:
            current_player_id = player.player_id
            payout_percentage = payouts[current_player_id] / (
                self.previous_chips[current_player_id] + 0.001
            )
            if payout_percentage > 0:
                payout_percentage *= self.winner_reward_multiplier
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
        # actions
        current_round_history = self.game.hand_history[self.game.hand_phase]
        if self.game.hand_phase == HandPhase.PREHAND:
            current_round_history = self.game.hand_history.get_last_history()
        # prefill action list
        actions = [(-1, 0)] * self.num_players
        if not isinstance(current_round_history, PrehandHistory):

            for player_action in current_round_history.actions:
                actions[player_action.player_id] = (
                    self.action_to_num[player_action.action_type],  # action
                    player_action.value
                    if player_action.value is not None
                    else 0,  # value
                )

        # active + chips
        active = [0] * self.num_players
        chips = [0] * self.num_players
        winners = None
        # if last street played and still multiple players active
        if not self.game.is_hand_running() and not self.game._is_hand_over():
            winners = self.game.hand_history[HandPhase.SETTLE].pot_winners
            for winner_id in winners.keys():
                active[winner_id] = 1

        for x in self.game.players:
            if winners is None:
                active[x.player_id] = int(
                    x.state not in (PlayerState.OUT, PlayerState.SKIP)
                )
            chips[x.player_id] = x.chips

        # community cards
        community_cards = [(0, 0)] * 5
        for i in range(len(self.game.board)):
            card = self.game.board[i]
            community_cards[i] = self.card_to_observation(card)

        # player hand
        player_card = ((0, 0),) * 2
        if self.game.hand_phase != HandPhase.PREFLOP:
            player_card = [
                self.card_to_observation(x) for x in self.game.hands[current_player_id]
            ]

        # update observations
        """
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
        """
        return np.array(
            flatten_array(
                [
                    tuple(actions),
                    tuple(active),
                    tuple(chips),
                    tuple(community_cards),
                    player_card,
                    self.game.players[current_player_id].chips,
                    self.game.pots[0].raised,
                    sum([x.amount for x in self.game.pots]),
                    tuple(pot_commits.values()),
                    tuple(stage_pot_commits.values()),
                ]
            )
        )

    def step(self, action, format_action=True, get_all_rewards=False):
        """
        Standard gym env step function. Each step is a round of everyone has placed their bets
        """

        action, val = action

        # convert action to ActionType
        if format_action:
            action = round(action)
            action = self.num_to_action[action]

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
                val += self.game.player_bet_amount(
                    current_player.player_id
                ) + self.game.chips_to_call(current_player.player_id)
            val = round(val)
        else:
            val = None

        # translate action to ALL_IN
        if action == ActionType.RAISE and val >= current_player.chips:
            action = ActionType.ALL_IN
            val = None

        if self.debug:
            print(
                f"{str(self.game.hand_phase)[10:]}: Player {self.game.current_player}, Chips: {self.game.players[self.game.current_player].chips}, Action - {str(action)[11:].capitalize()}{f': {val}' if val else ''}"
            )

        # check valid action
        if not self.game.validate_move(current_player.player_id, action, val):
            action = (
                ActionType.CHECK
                if self.game.validate_move(
                    current_player.player_id, ActionType.CHECK, None
                )
                else ActionType.FOLD
            )
            val = None

        # agent take action
        self.game.take_action(action, val)
        done = not self.game.is_hand_running()

        # Take the other agent actions (and values) in the game.
        while self.game.current_player != self.agent_id and not done:
            observations = None
            if isinstance(self.opponents[self.game.current_player], RLAgent):
                observations = self.get_observations(
                    self.game.current_player, *self.get_pot_commits()
                )
            action, val = self.opponents[self.game.current_player].calculate_action(
                observations
            )
            if self.debug:
                print(
                    f"{str(self.game.hand_phase)[10:]}: Player {self.game.current_player}, Chips: {self.game.players[self.game.current_player].chips}, Action - {str(action)[11:].capitalize()}{f': {val}' if val else ''}"
                )

            # opponent take action
            self.game.take_action(action, val)
            done = not self.game.is_hand_running()

        # observations

        pot_commits, stage_pot_commits = self.get_pot_commits()
        observation = self.get_observations(
            current_player.player_id, pot_commits, stage_pot_commits
        )

        # reward + info
        if get_all_rewards:
            reward = self.get_reward(pot_commits)
        else:
            reward = self.get_reward(pot_commits)[self.agent_id]
        info = {"winners": self.get_winners()}
        return observation, reward, done, info

    def render(self):
        pass

    def reset_game(self):
        self.game.reset_game()
        for x in self.game.players:
            self.previous_chips.update({x.player_id: x.chips})

    def reset(self):
        # update previous chips
        self.fresh_start = True
        for x in self.game.players:
            self.previous_chips.update({x.player_id: x.chips})

        # initiate game engine
        while not self.game.is_hand_running():
            self.game.start_hand()
            if not self.game.is_game_running():
                self.reset_game()

        # take opponent actions in the game
        while self.game.current_player != self.agent_id:
            observations = None
            if isinstance(self.opponents[self.game.current_player], RLAgent):
                observations = self.get_observations(
                    self.game.current_player, *self.get_pot_commits()
                )
            action, val = self.opponents[self.game.current_player].calculate_action(
                observations
            )

            if self.debug:
                print(
                    f"{str(self.game.hand_phase)[10:]}: Player {self.game.current_player}, Chips: {self.game.players[self.game.current_player].chips}, Action - {str(action)[11:].capitalize()}{f': {val}' if val else ''}"
                )
            self.game.take_action(action, val)

            while not self.game.is_hand_running():
                self.game.start_hand()
                if not self.game.is_game_running():
                    self.reset_game()

        # calculate + return information
        current_player: Player = list(
            filter(
                lambda x: x.player_id == self.game.current_player,
                self.game.players,
            )
        )[0]

        observation = self.get_observations(
            current_player.player_id, *self.get_pot_commits()
        )
        return observation

    def close(self):
        # some cleanups
        print("Environment is closing...")


def main(n_games=1):
    with open("config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    poker = PokerEnv(config=config["sac-six-player"], debug=n_games <= 5)
    agent = CrammerAgent(poker.game)
    agent.player_id = poker.agent_id

    # reset environment
    obs = poker.reset()

    # start step loop
    games_to_play = 0
    while 1:
        action, val = agent.calculate_action()
        obs, reward, done, info = poker.step(
            (action, val), format_action=False, get_all_rewards=True
        )

        if done:
            if n_games <= 5:
                print(
                    f"\nprev chips: {tuple(poker.previous_chips.values())}",
                    f"\nchips: {[x.chips for x in poker.game.players]}",
                    f"\nreward: {tuple(reward.values())}",
                    f"\nwinners: {info}",
                    "\n",
                )

            games_to_play += 1
            if games_to_play >= n_games:
                break
            obs = poker.reset()

    print(
        f"\nprev chips: {tuple(poker.previous_chips.values())}",
        f"\nchips: {tuple([x.chips for x in poker.game.players])}",
        f"\nsum chips: {sum(tuple([x.chips for x in poker.game.players]))}",
        f"\nreward: {tuple(reward.values())}",
        f"\nwinners: {info}",
        f"\nbuyin history: {tuple(poker.game.total_buyin_history.values())}",
        f"\nrestart times: {poker.game.game_restarts}",
        "\n",
    )
    poker.close()


if __name__ == "__main__":
    # --- about 2s for 1000 games (0.002s / game) --- #
    import pstats
    import cProfile

    with cProfile.Profile() as pr:
        main(n_games=3000)

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.dump_stats("profile.prof")
    # run `snakeviz profile.prof` to see stats
