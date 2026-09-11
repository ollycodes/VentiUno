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
    pit: Wallet     # denomination -> coins currently wagered on player_hand
    split_hand: t.List[cl.Card]  # empty unless the player has split
    split_pit: Wallet            # denomination -> coins wagered on split_hand
    active_hand: str             # 'main' or 'split' — which hand hit/stand act on
    insurance_pit: Wallet        # denomination -> coins wagered as insurance
    insurance_decided: bool      # has the up-front insurance choice been made?
    high_score: int
    biggest_bet: int

    def _total(self, cards):
        total = 0
        has_ace = False
        for card in cards:
            card_value = cl.RANKS.get(card.rank)
            if card_value == 1:
                has_ace = True
            total += card_value
        if total <= 11 and has_ace:
            total += 10
        return total

    @property
    def player_total(self):
        return self._total(self.player_hand)

    @property
    def dealer_total(self):
        return self._total(self.dealer_hand)

    @property
    def split_total(self):
        return self._total(self.split_hand)

    @property
    def active_total(self):
        return self._total(self._active_cards)

    @property
    def _active_cards(self):
        return self.split_hand if self.active_hand == 'split' else self.player_hand

    @property
    def _active_pit(self):
        return self.split_pit if self.active_hand == 'split' else self.pit

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
    def split_bet(self):
        return sum(denom * count for denom, count in self.split_pit.items())

    @property
    def total_wagered(self):
        return self.bet + self.split_bet

    @property
    def insurance_amount(self):
        return self.bet // 2

    @property
    def is_natural(self):
        """
        A blackjack dealt straight from the first two cards, not built up
        by hitting. A hand reconstituted from a split is never a natural,
        even if it lands on 21 with its one dealt card — real rules only
        give the 3:2 bonus to the original, ungapped first two cards.
        """
        return not self.split_hand and len(self.player_hand) == 2 and self.player_total == 21

    @property
    def dealer_shows_ace(self):
        """The dealer's up-card (first card — pending.html shows it face-up, the rest face-down)."""
        return bool(self.dealer_hand) and cl.RANKS[self.dealer_hand[0].rank] == 1

    def _winner_for(self, total):
        # A bust is an unconditional loss and must be checked before
        # anything else: _finish_active_hand plays the dealer out *before*
        # settling a hand that may have already busted, so a player total
        # over 21 must never be compared against a dealer total at all
        # (otherwise a dealer who also busts would make a busted player
        # "win").
        if total > 21:
            return "Dealer won"
        if self.dealer_total > 21:
            return "You won"
        if total == self.dealer_total:
            return "Draw"
        if total > self.dealer_total:
            return "You won"
        return "Dealer won"

    @property
    def winner(self):
        return self._winner_for(self.player_total)

    @property
    def split_winner(self):
        return self._winner_for(self.split_total)

    @property
    def can_hit(self):
        if len(self._active_cards) < 2:
            return False
        if self.split_hand and cl.RANKS[self._active_cards[0].rank] == 1:
            return False  # aces split: exactly one card each, no further hitting
        return self.active_total < 21

    @property
    def can_double(self):
        return len(self._active_cards) == 2 and self.coins >= sum(
            denom * count for denom, count in self._active_pit.items()
        )

    @property
    def can_split(self):
        if self.split_hand or self.active_hand == 'split' or len(self.player_hand) != 2:
            return False
        first, second = self.player_hand
        if cl.RANKS[first.rank] != cl.RANKS[second.rank]:
            return False
        return self.coins >= self.bet

    @property
    def can_insure(self):
        return self.insurance_amount > 0 and self.coins >= self.insurance_amount

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

    def _wager(self, target_pit, amount):
        """
        Moves `amount` dollars from the wallet into target_pit. Breaks
        down held coins first if nothing small enough is on hand, then
        greedily composes the amount largest-coin-first — the same
        approach quickplay_bet uses for its target bet.
        """
        held = [denom for denom, count in self.wallet.items() if count > 0]
        while held and min(held) > amount:
            self.break_coin(min(held))
            held = [denom for denom, count in self.wallet.items() if count > 0]

        remaining = amount
        for denom in sorted(cl.COIN_LADDER, reverse=True):
            count = min(self.wallet.get(denom, 0), remaining // denom)
            if count:
                self.wallet[denom] -= count
                target_pit[denom] = target_pit.get(denom, 0) + count
                remaining -= count * denom

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
        self._wager(self.pit, target)

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

    def deal_hand(self):
        """
        Deals a fresh hand and resets everything split/insurance-related
        from the previous one. Deliberately doesn't resolve a natural or a
        dealer blackjack itself — bet_view checks the state right after
        calling this and renders the outcome directly, the same way
        action() already does after a hit/stand, so the resolution reads
        as "whichever request caused it" rather than something table_view
        has to reconstruct after the fact.
        """
        self.check_deck()
        self.split_hand = []
        self.split_pit = {denom: 0 for denom in cl.COIN_LADDER}
        self.insurance_pit = {denom: 0 for denom in cl.COIN_LADDER}
        self.active_hand = 'main'
        self.insurance_decided = not self.dealer_shows_ace
        if self.insurance_decided:
            self._resolve_deal()

    def decide_insurance(self, take):
        if take and self.can_insure:
            self._wager(self.insurance_pit, self.insurance_amount)
        self.insurance_decided = True
        self._resolve_deal()

    def _resolve_deal(self):
        """
        Peeks the dealer's hole card once the insurance decision (if any)
        is settled. A dealer natural pays/forfeits insurance and ends the
        round immediately (no player turn against a dealer blackjack); if
        the dealer doesn't have one, a taken insurance bet is simply lost,
        and the player's own natural (if any) still resolves immediately.
        """
        dealer_natural = len(self.dealer_hand) == 2 and self.dealer_total == 21
        if sum(self.insurance_pit.values()):
            if dealer_natural:
                amount = sum(denom * count for denom, count in self.insurance_pit.items())
                for denom, count in self.insurance_pit.items():
                    if count:
                        self.wallet[denom] = self.wallet.get(denom, 0) + count
                self._pay_out(amount * 2)
            self.insurance_pit = {denom: 0 for denom in cl.COIN_LADDER}
        if dealer_natural or self.is_natural:
            self.conclude_bet()

    def _pay_out(self, amount):
        """Credits `amount` dollars to the wallet, broken into coins largest-first."""
        for denom in sorted(cl.COIN_LADDER, reverse=True):
            count, amount = divmod(amount, denom)
            if count:
                self.wallet[denom] = self.wallet.get(denom, 0) + count

    def _settle_hand(self, cards, pit, is_natural):
        total = self._total(cards)
        bet = sum(denom * count for denom, count in pit.items())
        winner = self._winner_for(total)
        # Winnings are always paid in the same denominations that were
        # wagered, just multiplied — never converted into other coins.
        # The one exception is a natural blackjack's 3:2 bonus, which can't
        # land on a whole-dollar multiple of the wagered coins, so that
        # bonus half is paid out fresh instead (see _pay_out).
        if winner == "Draw":
            for denom, count in pit.items():
                if count:
                    self.wallet[denom] = self.wallet.get(denom, 0) + count
        elif winner == "You won":
            if is_natural:
                for denom, count in pit.items():
                    if count:
                        self.wallet[denom] = self.wallet.get(denom, 0) + count
                self._pay_out(bet // 2)
            else:
                for denom, count in pit.items():
                    if count:
                        self.wallet[denom] = self.wallet.get(denom, 0) + count * 2
        for denom in cl.COIN_LADDER:
            pit[denom] = 0
        if self.biggest_bet < bet:
            self.biggest_bet = bet

    def conclude_bet(self):
        self._settle_hand(self.player_hand, self.pit, self.is_natural)
        if self.split_hand:
            self._settle_hand(self.split_hand, self.split_pit, is_natural=False)
        if self.high_score < self.coins:
            self.high_score = self.coins

    def hit(self):
        if not self.can_hit:
            return
        if self.active_hand == 'split':
            self.split_hand += cl.draw_cards(self.deck, 1)
        else:
            self.player_hand += cl.draw_cards(self.deck, 1)
        if self.active_total >= 21:
            self._finish_active_hand()

    def double(self):
        if not self.can_double:
            return
        pit = self._active_pit
        self._wager(pit, sum(denom * count for denom, count in pit.items()))
        if self.active_hand == 'split':
            self.split_hand += cl.draw_cards(self.deck, 1)
        else:
            self.player_hand += cl.draw_cards(self.deck, 1)
        self._finish_active_hand()

    def split(self):
        if not self.can_split:
            return
        self.split_hand = [self.player_hand.pop()]
        self._wager(self.split_pit, self.bet)
        self.player_hand += cl.draw_cards(self.deck, 1)
        self.split_hand += cl.draw_cards(self.deck, 1)

    def _finish_active_hand(self):
        """
        Called whenever the active hand's turn is over (stood, busted, hit
        to 21, or doubled). Moves to the split hand's turn if there is one
        still to play; otherwise plays the dealer out and settles every
        wagered hand.
        """
        if self.active_hand == 'main' and self.split_hand:
            self.active_hand = 'split'
            return
        while self.dealer_total < 17:
            self.dealer_hand += cl.draw_cards(self.deck, 1)
        self.conclude_bet()

    def stand(self):
        self._finish_active_hand()

    @classmethod
    def new(cls):
        """Starts a fresh game with no cards dealt and an empty, not-yet-divvied wallet."""
        return cls(
            deck=[],
            player_hand=[],
            dealer_hand=[],
            wallet={denom: 0 for denom in cl.COIN_LADDER},
            pit={denom: 0 for denom in cl.COIN_LADDER},
            split_hand=[],
            split_pit={denom: 0 for denom in cl.COIN_LADDER},
            active_hand='main',
            insurance_pit={denom: 0 for denom in cl.COIN_LADDER},
            insurance_decided=True,
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
            split_hand=cl.cards_to_json(self.split_hand),
            split_pit={str(denom): count for denom, count in self.split_pit.items()},
            active_hand=self.active_hand,
            insurance_pit={str(denom): count for denom, count in self.insurance_pit.items()},
            insurance_decided=self.insurance_decided,
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
            split_hand=cl.cards_from_json(data['split_hand']),
            split_pit={int(denom): count for denom, count in data['split_pit'].items()},
            active_hand=data['active_hand'],
            insurance_pit={int(denom): count for denom, count in data['insurance_pit'].items()},
            insurance_decided=data['insurance_decided'],
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
