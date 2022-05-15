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


        """ Game States """
        
        def start_state(self):
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
            self.table_card_1.place(relx=0.32, rely=0.29, anchor='center')

            self.table_card_2 = Button(self.root, image= self.default_card, command=None)
            self.table_card_2.place(relx=0.42, rely=0.29, anchor='center')

            self.table_card_3 = Button(self.root, image= self.default_card, command=None)
            self.table_card_3.place(relx=0.52, rely=0.29, anchor='center')

            self.table_card_4 = Button(self.root, image= self.default_card, command=None)
            self.table_card_4.place(relx=0.62, rely=0.29, anchor='center')

            self.table_card_5 = Button(self.root, image= self.default_card, command=None)
            self.table_card_5.place(relx=0.72, rely=0.29, anchor='center')

            # Setting Player buttons
            bx_pos = 0.36
            self.checkButton = Button(self.root, text="Check", activebackground="#2f4f4f", 
                                bg="#18A558", fg="#FFFFFF", bd=0, command=self.exit, height=3, width=15)
            self.checkButton.place(relx=bx_pos, rely=0.95, anchor='center')

            self.callButton = Button(self.root, text="Call", activebackground="#0000FF", 
                                bg="#7EC8E3", fg="#FFFFFF", bd=0, command=self.exit, height=3, width=15)
            self.callButton.place(relx=bx_pos+0.10, rely=0.95, anchor='center')

            self.raiseButton = Button(self.root, text="Raise", activebackground="#FF8A8A", 
                                bg="#FF0000", fg="#FFFFFF", bd=0, command=self.exit, height=3, width=15)
            self.raiseButton.place(relx=bx_pos+0.20, rely=0.95, anchor='center')

            self.foldButton = Button(self.root, text="Fold", activebackground="#737373", 
                                bg="#171717", fg="#FFFFFF", bd=0, command=self.exit, height=3, width=15)
            self.foldButton.place(relx=bx_pos+0.30, rely=0.95, anchor='center')


            self.root.mainloop()
        
        def flop(self):
            pass

        def turn(self):
            pass

        def river(self):
            pass

        def end_state(self):
            pass

        """ Object Functions """

        def reset_game(self):
            self.game.reset()


        """ Button Commands"""

        def startCommand(self):
            self.startButton.destroy()
            self.pre_flop()

        def exit(self):
            exit()

