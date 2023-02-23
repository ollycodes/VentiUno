from dataclasses import dataclass
from . import card as cl
import typing as t

@dataclass
class GameLogic:
    """ Main blackjack logic class. """
    name: str
    state: str
    deck: t.List[cl.Card]
    player_hand: t.List[cl.Card]
    dealer_hand: t.List[cl.Card]

    ATTR_MAP = {
        'player_hand':'hand',
        'dealer_hand':'hand',
    }

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
        self.state = 'first_deal'
    
    def check_deck(self):
        if len(self.deck) <= 52:
            self.deck = cl.generate_deck(2)
            self.player_hand = cl.draw_cards(self.deck, 2)
            self.dealer_hand = cl.draw_cards(self.deck, 2)
        else:
            self.player_hand = cl.draw_cards(self.deck, 2)
            self.dealer_hand = cl.draw_cards(self.deck, 2)
        self.state = 'new_round'

    def hit(self):
        self.player_hand += cl.draw_cards(self.deck, 1)
        self.state = 'hit'

    def stand(self):
        while self.dealer_total < 17 and self.dealer_total < self.player_total:
            self.dealer_hand += cl.draw_cards(self.deck, 1)
        self.state = 'stand'

    def save_attr_to_db(self, db_object, attr_name):
        if attr_name == 'deck' or attr_name == 'player_hand' or attr_name == 'dealer_hand':
            db_attr_value = cl.cards_to_json(getattr(self, attr_name))
        else:
            db_attr_value = getattr(self, attr_name)
        db_attr_name = self.ATTR_MAP.get(attr_name, attr_name)
        setattr(db_object, db_attr_name, db_attr_value)
        db_object.save()

    @classmethod
    def load(cls, db_table_obj, db_player_obj, db_dealer_obj):
        """run in views. loads three db model objects into GameLogic class object."""
        name = db_table_obj.name
        state = db_table_obj.state
        deck = cl.cards_from_json(db_table_obj.deck)
        player_hand = cl.cards_from_json(db_player_obj.hand)
        dealer_hand = cl.cards_from_json(db_dealer_obj.hand)
        game = cls(name=name, state=state, deck=deck, player_hand=player_hand, dealer_hand=dealer_hand)
        return game

    def save_action(self, db_objects):
        table = db_objects['table']
        player = db_objects['player']
        dealer = db_objects['dealer']

        self.save_attr_to_db(table, 'deck')
        self.save_attr_to_db(player, 'player_hand')
        self.save_attr_to_db(dealer, 'dealer_hand')
        self.save_attr_to_db(table, 'state')

    def save_name(self, db_objects):
        table = db_objects['table']
        self.save_attr_to_db(table, 'name')
