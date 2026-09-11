"""
Unit tests for blackjack.logics.blackjack, built against hands and wallets
constructed directly (never random.shuffle) so every scenario is exact and
repeatable.
"""
from django.test import SimpleTestCase

from blackjack.logics import blackjack as tl
from blackjack.logics import card as cl


def make_card(rank, suit='spades'):
    return cl.Card(0, rank, suit, f'{rank} of {suit}', f'{suit}_{rank}.svg')


def make_game(player_hand=None, dealer_hand=None, deck=None, wallet=None,
              pit=None, high_score=0, biggest_bet=0):
    game = tl.GameLogic.new()
    if player_hand is not None:
        game.player_hand = [make_card(rank) for rank in player_hand]
    if dealer_hand is not None:
        game.dealer_hand = [make_card(rank) for rank in dealer_hand]
    if deck is not None:
        game.deck = [make_card(rank) for rank in deck]
    if wallet is not None:
        game.wallet = {denom: 0 for denom in cl.COIN_LADDER}
        game.wallet.update(wallet)
    if pit is not None:
        game.pit = {denom: 0 for denom in cl.COIN_LADDER}
        game.pit.update(pit)
    game.high_score = high_score
    game.biggest_bet = biggest_bet
    return game


class CoinActionTests(SimpleTestCase):
    def test_bet_coin_moves_from_wallet_to_pit(self):
        game = make_game(wallet={1: 3})
        game.bet_coin(1)
        self.assertEqual(game.wallet[1], 2)
        self.assertEqual(game.pit[1], 1)

    def test_bet_coin_clamps_to_available(self):
        game = make_game(wallet={1: 2})
        game.bet_coin(1, count=10)
        self.assertEqual(game.wallet[1], 0)
        self.assertEqual(game.pit[1], 2)

    def test_bet_coin_noop_when_denom_absent(self):
        game = make_game(wallet={1: 0})
        game.bet_coin(1)
        self.assertEqual(game.wallet[1], 0)
        self.assertEqual(game.pit.get(1, 0), 0)

    def test_unbet_coin_moves_from_pit_to_wallet(self):
        game = make_game(pit={5: 2})
        game.unbet_coin(5)
        self.assertEqual(game.pit[5], 1)
        self.assertEqual(game.wallet[5], 1)

    def test_unbet_coin_clamps_to_available(self):
        game = make_game(pit={5: 1})
        game.unbet_coin(5, count=99)
        self.assertEqual(game.pit[5], 0)
        self.assertEqual(game.wallet[5], 1)

    def test_clear_bet_returns_everything(self):
        game = make_game(pit={1: 3, 25: 2})
        game.clear_bet()
        self.assertEqual(game.pit, {denom: 0 for denom in cl.COIN_LADDER})
        self.assertEqual(game.wallet[1], 3)
        self.assertEqual(game.wallet[25], 2)


class BreakMergeTests(SimpleTestCase):
    def test_break_coin_splits_into_smaller_denom(self):
        game = make_game(wallet={25: 1})
        game.break_coin(25)
        self.assertEqual(game.wallet[25], 0)
        self.assertEqual(game.wallet[5], 5)

    def test_break_coin_noop_at_bottom_of_ladder(self):
        game = make_game(wallet={1: 5})
        game.break_coin(1)
        self.assertEqual(game.wallet[1], 5)

    def test_break_coin_noop_without_a_coin_to_break(self):
        game = make_game()
        game.break_coin(25)
        self.assertEqual(game.wallet, {denom: 0 for denom in cl.COIN_LADDER})

    def test_merge_coins_combines_into_larger_denom(self):
        game = make_game(wallet={5: 5})
        game.merge_coins(5)
        self.assertEqual(game.wallet[5], 0)
        self.assertEqual(game.wallet[25], 1)

    def test_merge_coins_noop_at_top_of_ladder(self):
        game = make_game(wallet={1000: 3})
        game.merge_coins(1000)
        self.assertEqual(game.wallet[1000], 3)

    def test_merge_coins_noop_without_enough_coins(self):
        game = make_game(wallet={5: 3})
        game.merge_coins(5)
        self.assertEqual(game.wallet[5], 3)
        self.assertEqual(game.wallet[25], 0)


class ConcludeBetTests(SimpleTestCase):
    def test_draw_returns_the_wager(self):
        game = make_game(
            player_hand=['ten', 'nine'], dealer_hand=['ten', 'nine'],
            wallet={25: 0}, pit={25: 2},
        )
        game.conclude_bet()
        self.assertEqual(game.wallet[25], 2)
        self.assertEqual(game.pit[25], 0)

    def test_normal_win_pays_double_in_the_same_denomination(self):
        # 21 via a hit (three cards), not a natural.
        game = make_game(
            player_hand=['ten', 'nine', 'two'], dealer_hand=['ten', 'six'],
            wallet={25: 0}, pit={25: 2},
        )
        game.conclude_bet()
        self.assertEqual(game.wallet[25], 4)
        self.assertEqual(game.pit[25], 0)

    def test_loss_forfeits_the_wager(self):
        game = make_game(
            player_hand=['ten', 'six'], dealer_hand=['ten', 'nine'],
            wallet={25: 0}, pit={25: 2},
        )
        game.conclude_bet()
        self.assertEqual(game.wallet.get(25, 0), 0)
        self.assertEqual(game.pit[25], 0)

    def test_natural_blackjack_pays_three_to_two_rounded_down(self):
        game = make_game(
            player_hand=['ace', 'king'], dealer_hand=['ten', 'six'],
            pit={5: 1},  # bet = 5; floor(5 * 1.5) = 7
        )
        self.assertTrue(game.is_natural)
        game.conclude_bet()
        self.assertEqual(game.coins, 7)
        self.assertEqual(game.wallet.get(5, 0), 1)
        self.assertEqual(game.wallet.get(1, 0), 2)

    def test_natural_blackjack_bonus_uses_available_denominations(self):
        game = make_game(
            player_hand=['ace', 'king'], dealer_hand=['ten', 'six'],
            pit={100: 1},  # bet = 100; bonus of 50 fits a single 50 coin
        )
        game.conclude_bet()
        self.assertEqual(game.coins, 150)
        self.assertEqual(game.wallet.get(50, 0), 1)

    def test_a_21_built_from_hits_is_not_natural(self):
        game = make_game(player_hand=['seven', 'seven', 'seven'], dealer_hand=['ten', 'six'])
        self.assertFalse(game.is_natural)

    def test_high_score_and_biggest_bet_tracking(self):
        game = make_game(
            player_hand=['ten', 'nine'], dealer_hand=['ten', 'six'],
            pit={25: 4}, high_score=0, biggest_bet=0,
        )
        game.conclude_bet()
        self.assertEqual(game.biggest_bet, 100)
        self.assertEqual(game.high_score, game.coins)


class StandTests(SimpleTestCase):
    def test_dealer_keeps_hitting_below_17_even_when_already_ahead_of_player(self):
        # Dealer holds a hard 12, already beating the player's 10 — real
        # rules force a hit on anything below 17 regardless of the
        # player's total (regression test: stand() used to stop early
        # here because of a `dealer_total < player_total` clause).
        game = make_game(
            player_hand=['five', 'five'], dealer_hand=['ten', 'two'],
            deck=['five'], pit={1: 1},
        )
        game.stand()
        self.assertEqual(len(game.dealer_hand), 3)
        self.assertEqual(game.dealer_total, 17)

    def test_dealer_stops_at_17_or_above(self):
        game = make_game(
            player_hand=['ten', 'two'], dealer_hand=['ten', 'eight'],
            deck=['ace'], pit={1: 1},
        )
        game.stand()
        self.assertEqual(len(game.dealer_hand), 2)
        self.assertEqual(game.dealer_total, 18)


class QuickplayDivvyTests(SimpleTestCase):
    def test_sums_to_bank_for_various_banks(self):
        for bank in (1, 17, 100, 999):
            with self.subTest(bank=bank):
                divvy = tl.quickplay_divvy(bank)
                total = sum(denom * count for denom, count in divvy.items())
                self.assertEqual(total, bank)

    def test_uses_only_small_denominations(self):
        divvy = tl.quickplay_divvy(100)
        for denom in (50, 100, 500, 1000):
            self.assertEqual(divvy[denom], 0)


class QuickplayBetTests(SimpleTestCase):
    def test_bets_about_a_fifth_of_the_bankroll(self):
        game = make_game(wallet={1: 100})
        game.quickplay_bet()
        self.assertEqual(game.bet, 20)

    def test_breaks_down_a_wallet_of_only_big_chips(self):
        game = make_game(wallet={100: 1})
        game.quickplay_bet()
        self.assertEqual(game.bet, 20)
        self.assertEqual(game.coins, 80)

    def test_never_bets_more_than_available(self):
        game = make_game(wallet={1: 3})
        game.quickplay_bet()
        self.assertEqual(game.bet, 1)
        self.assertLessEqual(game.bet, 3)

    def test_noop_when_wallet_empty(self):
        game = make_game(wallet={})
        game.quickplay_bet()
        self.assertEqual(game.bet, 0)

    def test_clears_any_existing_bet_first(self):
        game = make_game(wallet={1: 100}, pit={1000: 1})
        game.quickplay_bet()
        self.assertEqual(game.pit.get(1000, 0), 0)


class ExchangeOptionsTests(SimpleTestCase):
    def test_merge_options_prefers_largest_denomination_first(self):
        options = tl.merge_options({5: 5, 25: 2}, limit=2)
        self.assertEqual([o['denom'] for o in options], [25, 5])

    def test_merge_options_respects_limit(self):
        options = tl.merge_options({1: 5, 5: 5, 25: 2}, limit=1)
        self.assertEqual(len(options), 1)

    def test_break_options_needs_at_least_one_coin(self):
        options = tl.break_options({100: 1}, limit=5)
        denoms = [o['denom'] for o in options]
        self.assertIn(100, denoms)
        self.assertNotIn(50, denoms)

    def test_break_options_excludes_smallest_denomination(self):
        self.assertEqual(tl.break_options({1: 100}), [])
