from dataclasses import dataclass
import random

SUITS = {'hearts', 'diamonds', 'spades', 'clubs'}
RANKS = {
    'ace': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'jack': 10,
    'queen': 10,
    'king': 10
    }

@dataclass
class Card:
    deck_id: int
    rank: str
    suit: str
    name: str
    file_name: str

    def to_dict(self):
        return dict(
            deck_id=self.deck_id,
            rank=self.rank,
            suit=self.suit,
            name = self.name,
            file_name=self.file_name
        )

def generate_deck(number):
    # creates a list of card OBJECTS
    cards = []

    for num in range(number):
        for suit in SUITS:
            for rank in RANKS:
                name = f'{rank} of {suit}'
                file_name = f'{suit}_{rank}.svg'
                cards.append(Card(num, rank, suit, name, file_name))
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
