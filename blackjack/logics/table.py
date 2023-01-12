import typing as t

from dataclasses import dataclass
from . import card as cl

# bug: dealer will hit on soft 16 with an ace


@dataclass
class Game:
    """ Main blackjack game class."""
    deck: t.List[cl.Card]
    player_hand: t.List[cl.Card]
    dealer_hand: t.List[cl.Card]

    def _total(self, hand):
        hand_total = 0
        has_ace = False
        for card in getattr(self, hand):
            card_value = cl.RANKS.get(card.rank)
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
        deck = cl.generate_deck(2)
        game = cls(
            deck = deck,
            player_hand = cl.draw_cards(deck, 2),
            dealer_hand = cl.draw_cards(deck, 2),
        )
        return game

    @classmethod
    def load(cls, table):
        """run in views; loads cards into game instance"""

        deck = cl.cards_from_json(table.game_data.get("deck"))
        player_hand = cl.cards_from_json(table.game_data.get("player_hand"))
        dealer_hand = cl.cards_from_json(table.game_data.get("dealer_hand"))
        return cls(deck, player_hand, dealer_hand)

    def check_deck(self):
        if len(self.deck) <= 52:
            self.deck = cl.generate_deck(2)
            self.player_hand = cl.draw_cards(self.deck, 2)
            self.dealer_hand = cl.draw_cards(self.deck, 2)
        else:
            self.player_hand = cl.draw_cards(self.deck, 2)
            self.dealer_hand = cl.draw_cards(self.deck, 2)

    def save(self, table):
        table.game_data = dict(
            deck=cl.cards_to_json(self.deck),
            player_hand=cl.cards_to_json(self.player_hand),
            dealer_hand=cl.cards_to_json(self.dealer_hand),
        )
        table.save()

    def hit(self):
        self.player_hand += cl.draw_cards(self.deck, 1)

    def stand(self, table):
        while self.dealer_total < 17 and self.dealer_total < self.player_total:
            self.dealer_hand += cl.draw_cards(self.deck, 1)
