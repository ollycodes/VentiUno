from dataclasses import dataclass
from . import card as cl
import typing as t

@dataclass
class GameLogic:
    """ Main blackjack logic class. """
    deck: t.List[cl.Card]
    player_hand: t.List[cl.Card]
    dealer_hand: t.List[cl.Card]
    bet: int
    coins: int
    high_score: int
    biggest_bet: int

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
    def player_card_count(self):
        return len(self.player_hand)

    @property
    def dealer_card_count(self):
        return len(self.dealer_hand)

    @property
    def winner(self):
        if self.player_total == self.dealer_total:
            return "Draw"
        elif self.player_total > self.dealer_total and self.player_total <= 21:
            return "You won"
        elif self.dealer_total > 21:
            return "You won"
        return "Dealer won"

    def player_bet(self, amount):
        self.bet = amount
        self.coins -= self.bet
        if self.bet > self.biggest_bet:
            self.biggest_bet = self.bet

    def check_deck(self):
        if len(self.deck) <= 52:
            self.deck = cl.generate_deck(2)
            self.player_hand = cl.draw_cards(self.deck, 2)
            self.dealer_hand = cl.draw_cards(self.deck, 2)
        else:
            self.player_hand = cl.draw_cards(self.deck, 2)
            self.dealer_hand = cl.draw_cards(self.deck, 2)

    def conclude_bet(self):
        if self.winner == "Draw":
            self.coins = self.coins + self.bet
        elif self.winner == "You won":
            self.coins += self.bet * 2
        self.bet = 0
        if self.biggest_bet < self.bet:
            self.biggest_bet = self.bet
        if self.high_score < self.coins:
            self.high_score = self.coins

    def hit(self):
        self.player_hand += cl.draw_cards(self.deck, 1)

    def stand(self):
        while self.dealer_total < 17 and self.dealer_total < self.player_total:
            self.dealer_hand += cl.draw_cards(self.deck, 1)
        self.conclude_bet()

    def save_attr_to_db(self, db_object, attr_name):
        if attr_name in ['deck', 'player_hand', 'dealer_hand']:
            db_attr_value = cl.cards_to_json(getattr(self, attr_name))
        else:
            db_attr_value = getattr(self, attr_name)
        db_attr_name = self.ATTR_MAP.get(attr_name, attr_name)
        setattr(db_object, db_attr_name, db_attr_value)
        db_object.save()

    @classmethod
    def load(cls, db_table_obj, db_player_obj, db_dealer_obj):
        """run in views. loads three db model objects into GameLogic class object."""
        deck = cl.cards_from_json(db_table_obj.deck)
        player_hand = cl.cards_from_json(db_player_obj.hand)
        dealer_hand = cl.cards_from_json(db_dealer_obj.hand)
        game = cls(
            deck=deck, 
            player_hand=player_hand, 
            dealer_hand=dealer_hand,
            bet=db_player_obj.bet,
            coins=db_player_obj.coins,
            high_score=db_player_obj.high_score,
            biggest_bet=db_player_obj.biggest_bet,
        )
        return game

    def save_action(self, db_objects):
        table = db_objects['table']
        player = db_objects['player']
        dealer = db_objects['dealer']

        self.save_attr_to_db(table, 'deck')
        self.save_attr_to_db(player, 'player_hand')
        self.save_attr_to_db(player, 'bet')
        self.save_attr_to_db(player, 'biggest_bet')
        self.save_attr_to_db(player, 'coins')
        self.save_attr_to_db(player, 'high_score')
        self.save_attr_to_db(dealer, 'dealer_hand')
