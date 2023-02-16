from dataclasses import dataclass
from . import card as cl
import typing as t

@dataclass
class GameLogic:
    """ Main blackjack logic class. """
    name: str
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

    def create_and_deal(self):
        self.deck = cl.generate_deck(2)
        self.player_hand = cl.draw_cards(self.deck, 2)
        self.dealer_hand = cl.draw_cards(self.deck, 2)

    @classmethod
    def load(cls, db_table_obj, db_player_obj, db_dealer_obj):
        """run in views. loads three db model objects into GameLogic class object."""
        print(db_table_obj.name)
        name = f'table {db_table_obj.pk}' if db_table_obj == '' else db_table_obj.name
        print(name)
        deck = cl.cards_from_json(db_table_obj.deck)
        player_hand = cl.cards_from_json(db_player_obj.hand)
        dealer_hand = cl.cards_from_json(db_dealer_obj.hand)
        game = cls(name=name, deck=deck, player_hand=player_hand, dealer_hand=dealer_hand)
        return game

    def save(self, db_objects):
        table = db_objects['table']
        player = db_objects['player']
        dealer = db_objects['dealer']

        table.deck = cl.cards_to_json(self.deck)
        player.hand = cl.cards_to_json(self.player_hand)
        dealer.hand = cl.cards_to_json(self.dealer_hand)

        table.save()
        player.save()
        dealer.save()

    def check_deck(self):
        if len(self.deck) <= 52:
            self.deck = cl.generate_deck(2)
            self.player_hand = cl.draw_cards(self.deck, 2)
            self.dealer_hand = cl.draw_cards(self.deck, 2)
        else:
            self.player_hand = cl.draw_cards(self.deck, 2)
            self.dealer_hand = cl.draw_cards(self.deck, 2)

    def hit(self):
        self.player_hand += cl.draw_cards(self.deck, 1)

    def stand(self):
        while self.dealer_total < 17 and self.dealer_total < self.player_total:
            self.dealer_hand += cl.draw_cards(self.deck, 1)