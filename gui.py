from tkinter import *
from PIL import Image, ImageTk


class Window():
        def __init__(self, poker):
            self.root = Tk()
            self.root.title('Poker RL Robot')
            self.root.geometry("1200x650")
            self.root.configure(background="green")
            self.game = poker
            self.CARD_SIZE = (95, 144)
            self.CARD_SIZE_ROTATED = (144, 95)
            self.current_round = "Pre Flop"


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
                                bg="#18A558", fg="#FFFFFF", bd=0, command=self.next_round, height=3, width=15)
            self.checkButton.place(relx=bx_pos, rely=0.95, anchor='center')

            self.callButton = Button(self.root, text="Call", activebackground="#0000FF", 
                                bg="#7EC8E3", fg="#FFFFFF", bd=0, command=self.next_round, height=3, width=15)
            self.callButton.place(relx=bx_pos+0.10, rely=0.95, anchor='center')

            self.raiseButton = Button(self.root, text="Raise", activebackground="#FF8A8A", 
                                bg="#FF0000", fg="#FFFFFF", bd=0, command=self.next_round, height=3, width=15)
            self.raiseButton.place(relx=bx_pos+0.20, rely=0.95, anchor='center')

            self.foldButton = Button(self.root, text="Fold", activebackground="#737373", 
                                bg="#171717", fg="#FFFFFF", bd=0, command=self.exit, height=3, width=15)
            self.foldButton.place(relx=bx_pos+0.30, rely=0.95, anchor='center')

            # Setting Opponenets Cards
            default_rotated_path = ".//cards//defaultRotated.png"
            self.default_rotated = Image.open(default_rotated_path)
            self.default_rotated = self.default_rotated.resize(self.CARD_SIZE_ROTATED)
            self.default_rotated = ImageTk.PhotoImage(self.default_rotated)


            # Opponent 1
            self.opp_1_card_1 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_1_card_1.place(relx=0.072, rely=0.39, anchor='center')

            self.opp_1_card_2 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_1_card_2.place(relx=0.072, rely=0.57, anchor='center')

            # Opponent 2
            self.opp_2_card_1 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_2_card_1.place(relx=0.928, rely=0.39, anchor='center')

            self.opp_2_card_2 = Button(self.root, image= self.default_rotated, command=None)
            self.opp_2_card_2.place(relx=0.928, rely=0.57, anchor='center')

            # Player Cards
            self.player_card_1 = Button(self.root, image= self.default_card, command=None)
            self.player_card_1.place(relx=bx_pos+0.10, rely=0.76, anchor='center')

            self.player_card_2 = Button(self.root, image= self.default_card,command=None)
            self.player_card_2.place(relx=bx_pos+0.20, rely=0.76, anchor='center')

            # Setting Text boxes

            # General
            self.set_pot(0)
            self.set_round_name(self.current_round)

            # Player
            self.set_player_chips(1000)

            # Opponent 1
            self.set_opp1_chips(1000)
            self.set_opp1_move("None")

            # Opponent 2
            self.set_opp2_chips(1000)
            self.set_opp2_move("None")

            self.root.mainloop()
        
        def flop(self):
            self.table_card_1.destroy()
            self.show_card_1.place(relx=0.30, rely=0.20, anchor='center')

            self.table_card_2.destroy()
            self.show_card_2.place(relx=0.40, rely=0.20, anchor='center')

            self.table_card_3.destroy()
            self.show_card_3.place(relx=0.50, rely=0.20, anchor='center')
            self.root.mainloop()

        def turn(self):
            self.table_card_4.destroy()
            self.show_card_4.place(relx=0.60, rely=0.20, anchor='center')
            self.root.mainloop()

        def river(self):
            self.table_card_5.destroy()
            self.show_card_5.place(relx=0.70, rely=0.20, anchor='center')
            self.root.mainloop()

        def end_state(self):
            self.exit()

        """ Object Functions """

        def reset_game(self):
            self.game.reset()

        def set_community_cards(self):
            temp_path = ".//cards//Ace of Spades.png"
            self.temp = Image.open(temp_path)
            self.temp = self.temp.resize(self.CARD_SIZE)
            self.temp = ImageTk.PhotoImage(self.temp)

            self.show_card_1 = Button(self.root, image= self.temp, command=None)
            self.show_card_2 = Button(self.root, image= self.temp, command=None)
            self.show_card_3 = Button(self.root, image= self.temp, command=None)
            self.show_card_4 = Button(self.root, image= self.temp, command=None)
            self.show_card_5 = Button(self.root, image= self.temp, command=None)

        def step_game(self, action=None, val=None):
            pass

        """ GUI Text Functions """


        # General
        def set_pot(self, value):
            self.pot_value =  Label(self.root, text = "Current Pot: " + str(value), 
                                bg ="#FFFFF0", bd=2, height = 2, width= 50)
            self.pot_value.place(relx=0.50, rely=0.36, anchor='center')
        
        def set_round_name(self, name):
            self.round_name =  Label(self.root, text = name, font=("Arial", 12),
                                bg ="#FFFFF0", bd=2, height = 2, width= 50)
            self.round_name.place(relx=0.50, rely=0.025, anchor='center')


        # Player
        def set_player_chips(self, value):
            self.player_chips =  Label(self.root, text = "Chips: " + str(value), 
                                bg ="#FFFFF0", height = 2, width= 15)
            self.player_chips.place(relx=0.35, rely=0.70, anchor='center')

        # Opponent 1
        def set_opp1_chips(self, value):
            self.opp1_chips =  Label(self.root, text = "Chips: " + str(value), 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp1_chips.place(relx=0.195, rely=0.40, anchor='center')
        
        def set_opp1_move(self, value):
            self.opp1_chips =  Label(self.root, text = "Prev Move: " + value, 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp1_chips.place(relx=0.195, rely=0.50, anchor='center')


        # Opponent 2
        def set_opp2_chips(self, value):
            self.opp2_chips =  Label(self.root, text = "Chips: " + str(value), 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp2_chips.place(relx=0.795, rely=0.40, anchor='center')

        def set_opp2_move(self, value):
            self.opp2_chips =  Label(self.root, text = "Prev Move: " + value, 
                                bg ="#FFFFF0", bd=2, height = 2, width= 15)
            self.opp2_chips.place(relx=0.795, rely=0.50, anchor='center')



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
                self.river=()
            if(self.current_round == "River"):
                self.current_round = "End"
                self.end_state()
                    

        def exit(self):
            exit()

