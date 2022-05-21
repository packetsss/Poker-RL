from tkinter import *
from PIL import Image, ImageTk
from typing import TYPE_CHECKING

from engine.game.hand_phase import HandPhase
from engine.card.card import *
from engine.game.history import PrehandHistory
from engine.game.action_type import ActionType
if TYPE_CHECKING:
    from poker_env import PokerEnv


class Window():
        def __init__(self, poker):
            self.root = Tk()
            self.root.title('Poker RL Robot')
            self.root.geometry("1200x650")
            self.root.configure(background="green")
            self.env = poker
            self.env.reset()
            self.CARD_SIZE = (95, 144)
            self.CARD_SIZE_ROTATED = (100, 66)
            self.update = False
            self.current_round = "Pre Flop"
            self.converter = {"A": "Ace of ", "K": "King of ", "Q": "Queen of ", "J": "Jack of ", "T": "Ten of ",
                            "9": "Nine of ", "8": "Eight of ", "7": "Seven of ", "6": "Six of ", "5": "Five of ",
                            "4": "Four of ", "3": "Three of ", "2": "Two of ",
                             "d": "Diamonds.png", "s": "Spades.png", "h": "Hearts.png", "c" : "Clubs.png"
                             }



        """ Game States """
        
        def start_state(self):
            self.set_community_cards()
            self.startButton = Button(self.root, text="Start Game", activebackground="#EEEDE7", 
                                bg="#FFF5EE", bd=0, command=self.startCommand, height=5, width=40)
            self.startButton.place(relx=0.5, rely=0.5, anchor='center')
            
            self.root.mainloop()

        
        def pre_flop(self):
            # Creating table card objects
            default_card_path = ".//cards//default.png"
            self.default_card = Image.open(default_card_path)
            self.default_card = self.default_card.resize(self.CARD_SIZE)
            self.default_card = ImageTk.PhotoImage(self.default_card)

            self.table_card_1 = Button(self.root, image= self.default_card, command=None)
            self.table_card_1.place(relx=0.30, rely=0.20, anchor='center')

            self.table_card_2 = Button(self.root, image= self.default_card, command=None)
            self.table_card_2.place(relx=0.40, rely=0.20, anchor='center')

            self.table_card_3 = Button(self.root, image= self.default_card, command=None)
            self.table_card_3.place(relx=0.50, rely=0.20, anchor='center')

            self.table_card_4 = Button(self.root, image= self.default_card, command=None)
            self.table_card_4.place(relx=0.60, rely=0.20, anchor='center')

            self.table_card_5 = Button(self.root, image= self.default_card, command=None)
            self.table_card_5.place(relx=0.70, rely=0.20, anchor='center')

            # Setting Player buttons
            bx_pos = 0.35
            self.checkButton = Button(self.root, text="Check", activebackground="#2f4f4f", 
                                bg="#18A558", fg="#FFFFFF", bd=0, command=self.checkButton, height=3, width=15)
            self.checkButton.place(relx=bx_pos, rely=0.95, anchor='center')

            self.callButton = Button(self.root, text="Call", activebackground="#0000FF", 
                                bg="#7EC8E3", fg="#FFFFFF", bd=0, command=self.callButton, height=3, width=15)
            self.callButton.place(relx=bx_pos+0.10, rely=0.95, anchor='center')

            self.raiseButton = Button(self.root, text="Raise", activebackground="#FF8A8A", 
                                bg="#FF0000", fg="#FFFFFF", bd=0, command=self.raiseButton, height=3, width=15)
            self.raiseButton.place(relx=bx_pos+0.20, rely=0.95, anchor='center')

            self.foldButton = Button(self.root, text="Fold", activebackground="#737373", 
                                bg="#171717", fg="#FFFFFF", bd=0, command=self.foldButton, height=3, width=15)
            self.foldButton.place(relx=bx_pos+0.30, rely=0.95, anchor='center')

            # Setting Opponenets Cards
            default_rotated_path = ".//cards//defaultRotated.png"
            self.default_rotated = Image.open(default_rotated_path)
            self.default_rotated = self.default_rotated.resize(self.CARD_SIZE_ROTATED)
            self.default_rotated = ImageTk.PhotoImage(self.default_rotated)

            # Player Cards
            self.player_card_1.place(relx=0.35+0.10, rely=0.76, anchor='center')

            self.player_card_2.place(relx=0.35+0.20, rely=0.76, anchor='center')


            # Opponent 2
            self.opp_1_card_1 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_1_card_1.place(relx=0.928, rely=0.63, anchor='center')

            self.opp_1_card_2 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_1_card_2.place(relx=0.928, rely=0.75, anchor='center')


            # Opponent 2
            self.opp_2_card_1 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_2_card_1.place(relx=0.928, rely=0.18, anchor='center')

            self.opp_2_card_2 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_2_card_2.place(relx=0.928, rely=0.30, anchor='center')


            # Opponent 3
            self.opp_3_card_1 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_3_card_1.place(relx=0.072, rely=0.18, anchor='center')

            self.opp_3_card_2 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_3_card_2.place(relx=0.072, rely=0.30, anchor='center')

             # Opponent 4
            self.opp_4_card_1 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_4_card_1.place(relx=0.072, rely=0.48, anchor='center')

            self.opp_4_card_2 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_4_card_2.place(relx=0.072, rely=0.60, anchor='center')

             # Opponent 5
            self.opp_5_card_1 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_5_card_1.place(relx=0.072, rely=0.78, anchor='center')

            self.opp_5_card_2 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_5_card_2.place(relx=0.072, rely=0.90, anchor='center')

            self.update_all()
        
            self.root.mainloop()
        
        def flop(self):
            self.set_round_name(self.current_round)
            self.table_card_1.destroy()
            self.show_card_1.place(relx=0.30, rely=0.20, anchor='center')

            self.table_card_2.destroy()
            self.show_card_2.place(relx=0.40, rely=0.20, anchor='center')

            self.table_card_3.destroy()
            self.show_card_3.place(relx=0.50, rely=0.20, anchor='center')
            self.root.mainloop()

        def turn(self):
            self.set_round_name(self.current_round)
            self.table_card_4.destroy()
            self.show_card_4.place(relx=0.60, rely=0.20, anchor='center')
            self.root.mainloop()

        def river(self):
            self.set_round_name(self.current_round)
            self.table_card_5.destroy()
            self.show_card_5.place(relx=0.70, rely=0.20, anchor='center')
            self.root.mainloop()

        def end_state(self):
            self.exit()

        """ Object Functions """

        def reset_game(self):
            self.env.reset()

        def get_card_image_links(self, set_vals):

            table = [] 
            for v in set_vals:
                num, suit = str(v)[0], str(v)[1]
                to_add = ".//cards//"
                to_add = to_add + self.converter[num] + self.converter[suit]
                table.append(to_add)

            return table

        def set_community_cards(self):
            table = self.get_card_image_links(self.get_community_cards())
            player_hand = self.get_card_image_links(self.get_player_hands()[0])
            
            self.img_1 = Image.open(table[0])
            self.img_1 = self.img_1.resize(self.CARD_SIZE)
            self.img_1 = ImageTk.PhotoImage(self.img_1)

            self.img_2 = Image.open(table[1])
            self.img_2 = self.img_2.resize(self.CARD_SIZE)
            self.img_2 = ImageTk.PhotoImage(self.img_2)

            self.img_3 = Image.open(table[2])
            self.img_3 = self.img_3.resize(self.CARD_SIZE)
            self.img_3 = ImageTk.PhotoImage(self.img_3)

            self.img_4 = Image.open(table[3])
            self.img_4 = self.img_4.resize(self.CARD_SIZE)
            self.img_4 = ImageTk.PhotoImage(self.img_4)

            self.img_5 = Image.open(table[4])
            self.img_5 = self.img_5.resize(self.CARD_SIZE)
            self.img_5 = ImageTk.PhotoImage(self.img_5)

            self.p_1 = Image.open(player_hand[0])
            self.p_1 = self.p_1.resize(self.CARD_SIZE)
            self.p_1 = ImageTk.PhotoImage(self.p_1)

            self.p_2 = Image.open(player_hand[1])
            self.p_2 = self.p_2.resize(self.CARD_SIZE)
            self.p_2 = ImageTk.PhotoImage(self.p_2)

            self.get_community_cards()

            self.show_card_1 = Button(self.root, image= self.img_1, command=None)
            self.show_card_2 = Button(self.root, image= self.img_2, command=None)
            self.show_card_3 = Button(self.root, image= self.img_3, command=None)
            self.show_card_4 = Button(self.root, image= self.img_4, command=None)
            self.show_card_5 = Button(self.root, image= self.img_5, command=None)

            # Player Cards
            self.player_card_1 = Button(self.root, image= self.p_1, command=None)
            self.player_card_2 = Button(self.root, image= self.p_2,command=None)


        def step_game(self):
            """Which moves poker_env from Pre-Flop, Flop, Turn, River
            """
            #checks hand phase
            prev = self.env.game.hand_phase
            
            # make sure action is valid, returs true or false
            # define validate_choice
            self.env.game.validate_move(self.env.game.current_player, self.action, self.val)

            obs, reward, done, info = self.env.step(
                (self.action, self.val), format_action=False, get_all_rewards=True
            )

            if(done):
                self.env.reset()
                self.reset_game()

            if(prev != self.env.game.hand_phase):
                self.next_round()

            self.update_all()
   
        def get_community_cards(self):
            """Gets the Comunnity card dict from poker env
            """
            return self.env.game.community_cards
            

        def get_player_hands(self):
            """Gets the player hands from dict
            """
            return self.env.game.hands 
        

        def get_all_players_chips(self):
            """Gets all player chips as a data structure
            """
            return [x.chips for x in self.env.game.players]

        def get_all_players_moves(self):
            """Gets all moves for the round
            """
            actions = [(-1, 0)] * self.env.num_players
            current_round_history = self.env.game.hand_history[self.env.game.hand_phase]
            if self.env.game.hand_phase == HandPhase.PREHAND:
                current_round_history = self.env.game.hand_history.get_last_history()
            if not isinstance(current_round_history, PrehandHistory):

                for player_action in current_round_history.actions:
                    actions[player_action.player_id] = (
                        self.env.action_to_num[player_action.action_type],  # action
                        player_action.value
                        if player_action.value is not None
                        else 0,  # value
                    )
            return actions

        def get_all_players_bets(self):
            """Gets all best for the round
            """
            pot_commits, stage_pot_commits = self.env.get_pot_commits()
            return stage_pot_commits

        def validate_move(self):
            return self.env.game.validate_move(self.env.game.current_player, self.action, self.val)



            """ GUI Text Functions """

        # General
        def update_all(self):
            # Setting Text boxes
            pot_vals = self.get_all_players_chips()
            # General
            self.set_pot(0)
            self.set_round_name(self.current_round)

            # Player
            self.set_player_chips(pot_vals[0])
            self.set_player_round_bet(0)

            # Opponent 1
            self.set_opp1_chips(pot_vals[1])
            self.set_opp1_move("None")
            self.set_opp1_name()

            # Opponent 2
            self.set_opp2_chips(pot_vals[2])
            self.set_opp2_move("None")
            self.set_opp2_name()

            # Opponent 3
            self.set_opp3_chips(pot_vals[3])
            self.set_opp3_move("None")
            self.set_opp3_name()

            # Opponent 4
            self.set_opp4_chips(pot_vals[4])
            self.set_opp4_move("None")
            self.set_opp4_name()

            # Opponent 5
            self.set_opp5_chips(pot_vals[5])
            self.set_opp5_move("None")
            self.set_opp5_name()
            
            self.update = True

        def set_pot(self, value):
            if(self.update):
                self.pot_value.destroy()
            self.pot_value =  Label(self.root, text = "Current Pot: " + str(value), 
                                bg ="#FFFFF0", bd=2, height = 2, width= 50)
            self.pot_value.place(relx=0.50, rely=0.36, anchor='center')
        
        def set_round_name(self, name):
            if(self.update):
                self.round_name.destroy()
            self.round_name =  Label(self.root, text = name, font=("Arial", 12),
                                bg ="#FFFFF0", bd=2, height = 2, width= 50)
            self.round_name.place(relx=0.50, rely=0.025, anchor='center')

        def pop_up_raise(self):
            self.top = TopLevel(self.root)
            self.top.geometry("50x50")

            self.raise_val = entry(self.top, width=20)
            self.raise_val.pack()

            button = Button(self.top, text="Enter", command=lambda: button_pressed.set("button pressed"))
            button.wait_variable(button_pressed)

            self.top.mainloop()

        # Player
        def set_player_chips(self, value):
            if(self.update):
                self.round_name.destroy()
            self.player_chips =  Label(self.root, text = "Chips: " + str(value), 
                                bg ="#FFFFF0", height = 2, width= 15)
            self.player_chips.place(relx=0.35, rely=0.70, anchor='center')

        def set_player_round_bet(self, value):
            if(self.update):
                self.player_round_bet.destroy()
            self.player_round_bet =  Label(self.root, text = "Chips: " + str(value), 
                                bg ="#FFFFF0", height = 2, width= 15)
            self.player_round_bet.place(relx=0.35, rely=0.76, anchor='center')

        # Opponent 1
        def set_opp1_chips(self, value):
            if(self.update):
                self.opp1_chips.destroy()
            self.opp1_chips =  Label(self.root, text = "Chips: " + str(value), 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp1_chips.place(relx=0.82, rely=0.75, anchor='center')

        def set_opp1_move(self, value):
            if(value[0] == -1):
                value = ""
            elif(value[0] == 0):
                value = "Call"
            elif(value[0] == 1):
                value = "Raise"
            elif(value[0] == 2):
                value = "Check"
            elif(value[0] == 3):
                value = "Fold"
            elif(value[0] == 4):
                value = "All-in"

            
            if(self.update):
                self.opp1_move.destroy()
            self.opp1_move =  Label(self.root, text = "Prev Move: " + value, 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp1_move.place(relx=0.82, rely=0.69, anchor='center')

        def set_opp1_name(self):
            if(self.update):
                self.opp1_name.destroy()
            self.opp1_name =  Label(self.root, text = "Opponent 1", 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp1_name.place(relx=0.82, rely=0.63, anchor='center')


        # Opponent 2
        def set_opp2_chips(self, value):
            if(self.update):
                self.opp2_chips.destroy()
            self.opp2_chips =  Label(self.root, text = "Chips: " + str(value), 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp2_chips.place(relx=0.82, rely=0.30, anchor='center')

        def set_opp2_move(self, value):
            if(value[0] == -1):
                value = ""
            elif(value[0] == 0):
                value = "Call"
            elif(value[0] == 1):
                value = "Raise"
            elif(value[0] == 2):
                value = "Check"
            elif(value[0] == 3):
                value = "Fold"
            elif(value[0] == 4):
                value = "All-in"
            if(self.update):
                self.opp2_move .destroy()
            self.opp2_move =  Label(self.root, text = "Prev Move: " + value, 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp2_move.place(relx=0.82, rely=0.24, anchor='center')

        def set_opp2_name(self):
            if(self.update):
                self.opp2_name.destroy()
            self.opp2_name =  Label(self.root, text = "Opponent 2", 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp2_name.place(relx=0.82, rely=0.18, anchor='center')

        # Opponent 3
        def set_opp3_chips(self, value):
            if(self.update):
                self.opp3_chips.destroy()
            self.opp3_chips =  Label(self.root, text = "Chips: " + str(value), 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
        
            self.opp3_chips.place(relx=0.18, rely=0.30, anchor='center')
        
        def set_opp3_move(self, value):
            if(value[0] == -1):
                value = ""
            elif(value[0] == 0):
                value = "Call"
            elif(value[0] == 1):
                value = "Raise"
            elif(value[0] == 2):
                value = "Check"
            elif(value[0] == 3):
                value = "Fold"
            elif(value[0] == 4):
                value = "All-in"
            if(self.update):
                self.opp3_move.destroy()
            self.opp3_move =  Label(self.root, text = "Prev Move: " + value, 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp3_move.place(relx=0.18, rely=0.24, anchor='center')

        def set_opp3_name(self):
            if(self.update):
                self.opp3_name.destroy()
            self.opp3_name =  Label(self.root, text = "Opponent 3", 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp3_name.place(relx=0.18, rely=0.18, anchor='center')


        # Opponent 4
        def set_opp4_chips(self, value):
            if(self.update):
                 self.opp4_chips.destroy()
            self.opp4_chips =  Label(self.root, text = "Chips: " + str(value), 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
        
            self.opp4_chips.place(relx=0.18, rely=0.60, anchor='center')
        
        def set_opp4_move(self, value):
            if(value[0] == -1):
                value = ""
            elif(value[0] == 0):
                value = "Call"
            elif(value[0] == 1):
                value = "Raise"
            elif(value[0] == 2):
                value = "Check"
            elif(value[0] == 3):
                value = "Fold"
            elif(value[0] == 4):
                value = "All-in"
            if(self.update):
                self.opp4_move.destroy()
            self.opp4_move =  Label(self.root, text = "Prev Move: " + value, 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp4_move.place(relx=0.18, rely=0.54, anchor='center')


        def set_opp4_name(self):
            if(self.update):
                self.opp4_name.destroy()
            self.opp4_name =  Label(self.root, text = "Opponent 4", 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp4_name.place(relx=0.18, rely=0.48, anchor='center')


        # Opponent 5
        def set_opp5_chips(self, value):
            if(self.update):
                self.opp5_chips.destroy()
            self.opp5_chips =  Label(self.root, text = "Chips: " + str(value), 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
        
            self.opp5_chips.place(relx=0.18, rely=0.90, anchor='center')
        
        def set_opp5_move(self, value):
            if(value[0] == -1):
                value = ""
            elif(value[0] == 0):
                value = "Call"
            elif(value[0] == 1):
                value = "Raise"
            elif(value[0] == 2):
                value = "Check"
            elif(value[0] == 3):
                value = "Fold"
            elif(value[0] == 4):
                value = "All-in"
            if(self.update):
                self.opp5_chips.destroy()
            self.opp5_move =  Label(self.root, text = "Prev Move: " + value, 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp5_move.place(relx=0.18, rely=0.84, anchor='center')

        def set_opp5_name(self):
            if(self.update):
                self.opp5_name.destroy()
            self.opp5_name =  Label(self.root, text = "Opponent 5", 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp5_name.place(relx=0.18, rely=0.78, anchor='center')


        """ Button Commands"""

        def startCommand(self):
            self.startButton.destroy()
            self.pre_flop()

        def next_round(self):
            if(self.current_round == "Pre Flop"):
                self.current_round = "Flop"
                self.flop()
            if(self.current_round == "Flop"):
                self.current_round = "Turn"
                self.turn()
            if(self.current_round == "Turn"):
                self.current_round = "River"
                self.river()
            if(self.current_round == "River"):
                self.current_round = "End"
                self.end_state()

        def checkButton(self):
            self.action, self.val = ActionType.CHECK, None
            self.step_game()
            pass

        def callButton(self):
            self.action, self.val = ActionType.CALL, None
            self.validate_move()
            self.step_game()
            pass

        def raiseButton(self):
            self.pop_up_raise()
            self.action, self.val = ActionType.RAISE, "some value"
            self.step_game()
            pass

        def foldButton(self):
            self.action, self.val = ActionType.FOLD, None
            self.step_game()
            pass
                    

        def exit(self):
            exit()

