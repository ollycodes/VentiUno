from dataclasses import dataclass
from . import card as cl
import typing as t

Wallet = t.Dict[int, int]


@dataclass
class GameLogic:
    """ Main blackjack logic class. """
    deck: t.List[cl.Card]
    player_hand: t.List[cl.Card]
    dealer_hand: t.List[cl.Card]
    wallet: Wallet  # denomination -> coins on hand, available to bet
    pit: Wallet     # denomination -> coins currently wagered
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
    def coins(self):
        return sum(denom * count for denom, count in self.wallet.items())

    @property
    def bet(self):
        return sum(denom * count for denom, count in self.pit.items())

    @property
    def winner(self):
        if self.player_total == self.dealer_total:
            return "Draw"
        elif self.player_total > self.dealer_total and self.player_total <= 21:
            return "You won"
        elif self.dealer_total > 21:
            return "You won"
        return "Dealer won"

    # COIN ACTIONS
    # The bet is never a typed amount — it's just whatever coins are
    # sitting in the pit. Every action here just moves whole coins between
    # wallet and pit (or up/down the denomination ladder), so there's no
    # amount validation to get wrong: a coin either exists to move or it
    # doesn't.
    def bet_coin(self, denom, count=1):
        count = min(count, self.wallet.get(denom, 0))
        if count > 0:
            self.wallet[denom] -= count
            self.pit[denom] = self.pit.get(denom, 0) + count

    def unbet_coin(self, denom, count=1):
        count = min(count, self.pit.get(denom, 0))
        if count > 0:
            self.pit[denom] -= count
            self.wallet[denom] = self.wallet.get(denom, 0) + count

    def quickplay_bet(self):
        """
        A modest, no-thought bet for a player who'd rather keep playing
        than size every bet by hand: clears whatever's already wagered,
        then bets about a fifth of the bankroll. If the wallet is all big
        chips, breaks them down first so the bet doesn't have to be one
        oversized coin — favoring a longer session over a big swing.
        """
        self.clear_bet()
        target = max(1, self.coins // 5) if self.coins > 0 else 0
        if target <= 0:
            return

        held = [denom for denom, count in self.wallet.items() if count > 0]
        while held and min(held) > target:
            self.break_coin(min(held))
            held = [denom for denom, count in self.wallet.items() if count > 0]

        remaining = target
        for denom in sorted(cl.COIN_LADDER, reverse=True):
            count = min(self.wallet.get(denom, 0), remaining // denom)
            if count:
                self.bet_coin(denom, count)
                remaining -= count * denom

    def clear_bet(self):
        for denom, count in list(self.pit.items()):
            if count:
                self.wallet[denom] = self.wallet.get(denom, 0) + count
                self.pit[denom] = 0

    def break_coin(self, denom):
        """Break one coin into the coins that make up the next rung down the ladder."""
        idx = cl.COIN_LADDER.index(denom)
        if idx == 0 or self.wallet.get(denom, 0) < 1:
            return
        smaller = cl.COIN_LADDER[idx - 1]
        ratio = denom // smaller
        self.wallet[denom] -= 1
        self.wallet[smaller] = self.wallet.get(smaller, 0) + ratio

    def merge_coins(self, denom):
        """Merge enough coins to form one coin of the next rung up the ladder."""
        idx = cl.COIN_LADDER.index(denom)
        if idx == len(cl.COIN_LADDER) - 1:
            return
        larger = cl.COIN_LADDER[idx + 1]
        ratio = larger // denom
        if self.wallet.get(denom, 0) < ratio:
            return
        self.wallet[denom] -= ratio
        self.wallet[larger] = self.wallet.get(larger, 0) + 1

    def check_deck(self):
        if len(self.deck) <= 52:
            self.deck = cl.generate_deck(2)
            self.player_hand = cl.draw_cards(self.deck, 2)
            self.dealer_hand = cl.draw_cards(self.deck, 2)
        else:
            self.player_hand = cl.draw_cards(self.deck, 2)
            self.dealer_hand = cl.draw_cards(self.deck, 2)

    def conclude_bet(self):
        bet = self.bet
        # Winnings are always paid in the same denominations that were
        # wagered, just multiplied — never converted into other coins.
        if self.winner == "Draw":
            for denom, count in self.pit.items():
                if count:
                    self.wallet[denom] = self.wallet.get(denom, 0) + count
        elif self.winner == "You won":
            for denom, count in self.pit.items():
                if count:
                    self.wallet[denom] = self.wallet.get(denom, 0) + count * 2
        self.pit = {denom: 0 for denom in cl.COIN_LADDER}
        if self.biggest_bet < bet:
            self.biggest_bet = bet
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
        """Starts a fresh game with no cards dealt and an empty, not-yet-divvied wallet."""
        return cls(
            deck=[],
            player_hand=[],
            dealer_hand=[],
            wallet={denom: 0 for denom in cl.COIN_LADDER},
            pit={denom: 0 for denom in cl.COIN_LADDER},
            high_score=0,
            biggest_bet=0,
        )

    def to_session_dict(self):
        return dict(
            deck=cl.cards_to_json(self.deck),
            player_hand=cl.cards_to_json(self.player_hand),
            dealer_hand=cl.cards_to_json(self.dealer_hand),
            # JSON object keys are always strings, so denominations round-trip
            # through str() on the way out and int() on the way back in.
            wallet={str(denom): count for denom, count in self.wallet.items()},
            pit={str(denom): count for denom, count in self.pit.items()},
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
            wallet={int(denom): count for denom, count in data['wallet'].items()},
            pit={int(denom): count for denom, count in data['pit'].items()},
            high_score=data['high_score'],
            biggest_bet=data['biggest_bet'],
        )

    def save(self, session):
        session['game'] = self.to_session_dict()


def quickplay_divvy(bank):
    """
    A "reasonable" starting rack: weighted toward small change (1/5) with a
    light dusting of quarters, so a player starts out mostly holding low
    chips and works their way up to bigger denominations by merging or
    winning bets, rather than starting there already.
    """
    weights = {1: 0.35, 5: 0.35, 25: 0.30}
    divvy = {denom: 0 for denom in cl.COIN_LADDER}
    remaining = bank
    for denom in (25, 5, 1):
        count = int(bank * weights[denom]) // denom
        divvy[denom] = count
        remaining -= count * denom

    # Whatever's left after flooring each share lands on the 1 coin, so the
    # total always matches bank exactly.
    divvy[1] += remaining
    return divvy


_NUMBER_WORDS = {2: 'two', 3: 'three', 4: 'four', 5: 'five', 10: 'ten'}


def merge_options(wallet, limit=2):
    """Up to `limit` merge suggestions, largest mergeable denomination first."""
    options = []
    for idx in reversed(range(len(cl.COIN_LADDER) - 1)):
        if len(options) >= limit:
            break
        denom = cl.COIN_LADDER[idx]
        count = wallet.get(denom, 0)
        larger = cl.COIN_LADDER[idx + 1]
        ratio = larger // denom
        if count >= ratio:
            word = _NUMBER_WORDS.get(ratio, str(ratio))
            options.append(dict(action='merge', denom=denom, label=f"Merge {word} {denom} chips"))
    return options


def break_options(wallet, limit=2):
    """Up to `limit` break suggestions, largest breakable denomination first."""
    options = []
    for idx in reversed(range(1, len(cl.COIN_LADDER))):
        if len(options) >= limit:
            break
        denom = cl.COIN_LADDER[idx]
        if wallet.get(denom, 0) >= 1:
            options.append(dict(action='break', denom=denom, label=f"Break {denom}"))
    return options
