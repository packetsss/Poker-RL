from tkinter import *


class Window():
        def __init__(self, poker):
            self.root = Tk()
            self.root.title('Poker RL Robot')
            self.root.geometry("1200x650")
            self.root.configure(background="green")
            self.game = poker
            self.table_cards = 


        """ Game States """
        
        def start_state(self):
            self.startButton = Button(self.root, text="Start Game", activebackground="#EEEDE7", 
                                bg="#FFF5EE", bd=0, command=self.startCommand, height=5, width=40)
            self.startButton.place(relx=0.5, rely=0.5, anchor='center')
            
            self.root.mainloop()

        
        def pre_flop(self):
            

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

