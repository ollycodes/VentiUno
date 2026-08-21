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

    @classmethod
    def new(cls):
        """Starts a fresh game with a full bank and no cards dealt."""
        return cls(
            deck=[],
            player_hand=[],
            dealer_hand=[],
            bet=0,
            coins=2000,
            high_score=0,
            biggest_bet=0,
        )

    def to_session_dict(self):
        return dict(
            deck=cl.cards_to_json(self.deck),
            player_hand=cl.cards_to_json(self.player_hand),
            dealer_hand=cl.cards_to_json(self.dealer_hand),
            bet=self.bet,
            coins=self.coins,
            high_score=self.high_score,
            biggest_bet=self.biggest_bet,
        )

    @classmethod
    def from_session(cls, session):
        """Loads the active game out of request.session, or None if there isn't one."""
        data = session.get('game')
        if data is None:
            return None
        return cls(
            deck=cl.cards_from_json(data['deck']),
            player_hand=cl.cards_from_json(data['player_hand']),
            dealer_hand=cl.cards_from_json(data['dealer_hand']),
            bet=data['bet'],
            coins=data['coins'],
            high_score=data['high_score'],
            biggest_bet=data['biggest_bet'],
        )

    def save(self, session):
        session['game'] = self.to_session_dict()
