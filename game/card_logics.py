import random
from dataclasses import dataclass

SUITS = {'Hearts', 'Diamonds', 'Spades', 'Clubs'}
RANKS = {
    'Ace': 1,
    'Two': 2,
    'Three': 3,
    'Four': 4,
    'Five': 5,
    'Six': 6,
    'Seven': 7,
    'Eight': 8,
    'Nine': 9,
    'Ten': 10,
    'Jack': 10,
    'Queen': 10,
    'King': 10
    }

@dataclass
class Card:
    deck_id: int
    rank: str
    suit: str
    name: str

    def to_dict(self):
        return dict(
            deck_id=self.deck_id,
            rank=self.rank,
            suit=self.suit,
            name=self.name
        )

def generate_deck(number):
    # creates a list of card OBJECTS
    cards = []

    for num in range(number):
        for suit in SUITS:
            for rank in RANKS:
                name = f'{rank} of {suit}'
                cards.append(Card(num, rank, suit, name))
    random.shuffle(cards)
    return cards

def cards_to_json(cards):
    # runs to_dict function on all card OBJECTS;
    # converts card OBJECTS into dict items
    return [card.to_dict() for card in cards]

def cards_from_json(cards):
    # **card expands the dictionary items into arguments for the dataclass
    # converts dict items into card OBJECTS
    return [Card(**card) for card in cards]

def draw_cards(deck, number):
    return [deck.pop() for _ in range(number)]
