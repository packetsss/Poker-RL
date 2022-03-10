import random
import numpy as np

from engine.game.game import TexasHoldEm
from engine.game.action_type import ActionType
from engine.evaluator.evaluator import evaluate


class RandomAgent:
    def __init__(self, game: TexasHoldEm):
        self.game = game

    def calculate_action(self):
        while 1:
            rand = random.random()
            val = None
            if rand < 0.10:
                action = ActionType.FOLD
            elif rand < 0.90:
                action = ActionType.CALL
            else:
                action = ActionType.RAISE
                val = random.randint(5, 30)
            if self.game.validate_move(self.game.current_player, action, val):
                break

        return action, val


class CrammerAgent:
    def __init__(self, game: TexasHoldEm, num_to_action: dict = None, alpha=2, beta=50):
        self.game = game
        if num_to_action is None:
            num_to_action = {
                0: ActionType.CALL,
                1: ActionType.RAISE,
                2: ActionType.CHECK,
                3: ActionType.FOLD,
            }
        self.num_to_action = num_to_action

        self.alpha = alpha
        self.beta = beta

    def calculate_action(self):
        board = self.game.board
        community_cards = self.game.community_cards
        all_hands = self.game.hands
        hand_phase = self.game.hand_phase
        hand_history = self.game.hand_history
        big_blind = self.game.big_blind
        curr_player_id = self.game.current_player
        curr_player_chips = self.game.players[curr_player_id].chips

        # Find all possible actions.
        # Possible actions should always include FOLD and RAISE.
        # CHECK and CALL may sometimes be invalid.
        # I don't believe CHECK and CALL can ever be simultaneously possible.
        possible_actions = []  # 3 in length.
        for action in self.num_to_action.values():
            if action.name == "RAISE":
                val = int((self.game.big_blind + curr_player_chips) / 2)
            else:
                val = None

            if self.game.validate_move(curr_player_id, action, val):
                possible_actions.append(action.name)

            # All other hand phases besides PREFLOP.
            # Okay, so during the FLOP, we know the 3 community cards.
            # Our agent will also know everyone else's cards.

            # Let's first evaluate everyone's hands. This list will be our
            # "odds" calculator for how likely it is for our CrammerAgent to win.
            # This dict can vary based on which players are active in the current
            # game.
        player_odds = {}
        for active_player_id in self.game.active_iter():
            active_player_hand = self.game.hands[active_player_id]
            player_odds[active_player_id] = evaluate(
                active_player_hand, community_cards
            )

        # player_odds:
        # {3: 3117, 4: 6530, 5: 6316, 0: 3522, 1: 6585, 2: 6528}
        ids = list(player_odds.keys())
        odds = list(player_odds.values())

        # Player ID with highest odds of winning.
        possible_winner_id = ids[odds.index(min(odds))]
        difference = (
            player_odds[possible_winner_id] - player_odds[curr_player_id]
        )  # [0, 7461]

        # Hmmm, we want to have it return some bet and val
        # given the odds of winning out of all active players.
        # We can assume there will always be >= 2 players at this time
        # point.
        # We assume the current player is an active player.
        if difference == 0:  # Our current player has the highest odds of winning.
            rand = random.random()
            val = None

            # We definitely don't want to fold (unlikely).
            if rand < 0.02:
                action = ActionType.FOLD
            elif rand < 0.32:
                if "CALL" in possible_actions:
                    action = ActionType.CALL
                else:
                    action = ActionType.CHECK
            else:
                action = ActionType.RAISE
                proportion = np.random.beta(self.alpha, self.beta, size=1)
                chips_bet = int(proportion * curr_player_chips)
                chips_to_call = self.game.chips_to_call(curr_player_id)
                val = max(
                    chips_to_call,
                    self.game.big_blind,
                    min(chips_bet, curr_player_chips),
                )

        else:
            # We need to check how large this difference is. Depending on its size, we need to act accordingly.
            # The temp is near 1 if the difference between curr player odds and best player odds is small.
            # The temp is near 0 if the difference is large.

            var = np.random.uniform() * (0.1 * 7461)

            temp = 1 - (
                max(0, min(7461, (difference + var))) / (7461 + 1)
            )  # [near 1 if difference is smaller, near 0 if difference is bigger].
            val = None

            # Maybe we can try a more complex decision maker here.
            # log_diff = max(np.log10(1/difference), 2)  # We will find the magnitude of it.
            # # difference:
            # # [0, 1] -> within 0 and 10 -> 1
            # # [1, 2] -> within 10 and 100
            # # [2, 3] -> within 100 and 1000
            # # [3, 4] -> within 1000 and 10000

            if temp < 0.4:  # If the difference is 4500 or greater (up to 7461).
                action = ActionType.FOLD
            elif temp < 0.50:  # If the difference is between 4500 and roughly 3750.
                if "CALL" in possible_actions:
                    action = ActionType.CALL
                else:
                    action = ActionType.CHECK
            else:  # If the difference is less than 3750 (down to 0).
                action = ActionType.RAISE
                proportion = np.random.beta(self.alpha, self.beta, size=1)
                chips_bet = int(proportion * curr_player_chips)
                chips_to_call = self.game.chips_to_call(curr_player_id)
                val = max(
                    chips_to_call,
                    self.game.big_blind,
                    min(chips_bet, curr_player_chips),
                )

        # # Debugging.
        # if not self.game.validate_move(curr_player_id, bet, val):
        #     print(
        #         "INVALID MOVE: ",
        #         self.game.hand_phase.name,
        #         curr_player_id,
        #         bet.name,
        #         val,
        #     )
        # else:
        #     print(self.game.hand_phase, curr_player_id, bet, val)

        if action == ActionType.RAISE:
            """
            ADDED THIS PREVIOUS POT COMMIT TO AVOID INVALID MOVE:
            """
            val += self.game.player_bet_amount(
                curr_player_id
            ) + self.game.chips_to_call(curr_player_id)

            if val >= curr_player_chips:
                action = ActionType.ALL_IN
                val = None

        return action, val


