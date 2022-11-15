import typing as t

from dataclasses import dataclass
from . import card_logics

@dataclass
class Game:
    deck: t.List[card_logics.Card]
    player_hand: t.List[card_logics.Card]
    dealer_hand: t.List[card_logics.Card]
    is_finished: bool = False

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
    def winner(self):
        if self.player_total == self.dealer_total:
            return "Draw!"
        elif self.player_total > self.dealer_total and self.player_total <= 21:
            return "player won!"
        elif self.dealer_total > 21:
            return "player won!"
        return "dealer won!"

    def check(self):
        if self.player_total >= 21:
            self.is_finished = True

    @classmethod
    def create(cls):
        deck = card_logics.generate_deck(2)
        game = cls(
            deck = deck,
            player_hand = card_logics.draw_cards(deck, 2),
            dealer_hand = card_logics.draw_cards(deck, 2),
        )
        game.check()
        return game

    @classmethod
    def load(cls, table):
        # run in views; loads cards into game instance
        deck = card_logics.cards_from_json(table.deck)
        player_hand = card_logics.cards_from_json(table.player_hand)
        dealer_hand = card_logics.cards_from_json(table.dealer_hand)
        is_finished = table.is_finished
        return cls(deck, player_hand, dealer_hand, is_finished)

    def save(self, table):
        # saves card_logics. to views table object
        table.deck = card_logics.cards_to_json(self.deck)
        table.player_hand = card_logics.cards_to_json(self.player_hand)
        table.dealer_hand = card_logics.cards_to_json(self.dealer_hand)
        table.is_finished = self.is_finished
        table.save()

    def hit(self):
        self.player_hand += card_logics.draw_cards(self.deck, 1)
        self.check()

    def stand(self, table):
        while self.dealer_total < 17:
            self.dealer_hand += card_logics.draw_cards(self.deck, 1)
