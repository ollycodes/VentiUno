import typing as t

from dataclasses import dataclass
from . import card_logics

@dataclass
class Game:
    deck: t.List[card_logics.Card]
    player_hand: t.List[card_logics.Card]
    dealer_hand: t.List[card_logics.Card]
    action: str = "no_action"

    def _total(self, hand):
        hand_total = 0
        has_ace = False
        for card in getattr(self, hand):
            card_value = card_logics.RANKS.get(card.rank)
            if card_value == 1:
                has_ace = True
            hand_total += card_value

        if hand_total <= 11 and has_ace:
            hand_total += 10
        return hand_total

    @property
    def player_total(self):
        return self._total("player_hand")

    @property
    def dealer_total(self):
        return self._total("dealer_hand")

    @property
    def player_card_count(self):
        return len(self.player_hand)

    @property
    def dealer_card_count(self):
        return len(self.dealer_hand)

    @property
    def deck_card_count(self):
        return len(self.deck)

    @property
    def winner(self):
        if self.player_total == self.dealer_total:
            return "Draw"
        elif self.player_total > self.dealer_total and self.player_total <= 21:
            return "You won"
        elif self.dealer_total > 21:
            return "You won"
        return "Dealer won"

    @classmethod
    def create(cls):
        deck = card_logics.generate_deck(2)
        game = cls(
            deck = deck,
            player_hand = card_logics.draw_cards(deck, 2),
            dealer_hand = card_logics.draw_cards(deck, 2),
        )
        return game

    @classmethod
    def load(cls, table):
        # run in views; loads cards into game instance

        deck = card_logics.cards_from_json(table.game_data.get("deck"))
        player_hand = card_logics.cards_from_json(table.game_data.get("player_hand"))
        dealer_hand = card_logics.cards_from_json(table.game_data.get("dealer_hand"))
        action = table.game_data.get("action")
        return cls(deck, player_hand, dealer_hand, action)

    def check_deck(self):
        self.action = "no_action"
        if len(self.deck) <= 52:
            self.deck = card_logics.generate_deck(2)
            self.player_hand = card_logics.draw_cards(self.deck, 2)
            self.dealer_hand = card_logics.draw_cards(self.deck, 2)
        else:
            self.player_hand = card_logics.draw_cards(self.deck, 2)
            self.dealer_hand = card_logics.draw_cards(self.deck, 2)

    def save(self, table):
        table.game_data = dict(
            deck=card_logics.cards_to_json(self.deck),
            player_hand=card_logics.cards_to_json(self.player_hand),
            dealer_hand=card_logics.cards_to_json(self.dealer_hand),
            action=self.action
        )
        table.save()

    def hit(self):
        self.action = "hit"
        self.player_hand += card_logics.draw_cards(self.deck, 1)

    def stand(self, table):
        self.action = "stand"
        while self.dealer_total < 17:
            self.dealer_hand += card_logics.draw_cards(self.deck, 1)

def generate_username():
    '''
    retrieves one random adjective and noun.
    '''
    import sqlite3, random

    con = sqlite3.connect("name_gen.db")
    cur = con.cursor()

    tables = ["Adjectives", "Nouns"]
    username = ""

    for table in tables:
        cur.execute(f"SELECT Word FROM {table}")
        rows = cur.fetchall()
        word = rows[random.randrange(len(rows))]
        word = ",".join(word)
        word = word.replace(" ","")
        username += word.capitalize()
    return username
