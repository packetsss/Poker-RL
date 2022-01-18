from itertools import product
from random import shuffle

def hand_generator(num_players=1):
    suits = ["C","D","H","S"] 
    ranks = ["2","3","4","5","4","6","7","8","9","J","Q","K","A"]

    cards = list(r + s for r, s in product(ranks, suits))
    shuffle(cards)

    community = cards[:5]
    num_players_hands = []
    for i in range(num_players):
        num_players_hands.append(cards[5 + i * 2:7 + i * 2])
    
    return community, num_players_hands
    
    
if __name__ == "__main__":
    print(hand_generator())