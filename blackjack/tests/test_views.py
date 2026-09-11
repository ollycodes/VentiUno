"""
Integration tests driven through Django's test Client, seeding
request.session directly (a supported Django testing pattern) so hands are
deterministic instead of depending on the shuffled deck.
"""
from django.test import TestCase
from django.urls import reverse

from blackjack.logics import blackjack as tl
from blackjack.logics import card as cl


def _card_dict(rank, suit='spades'):
    return cl.Card(0, rank, suit, f'{rank} of {suit}', f'{suit}_{rank}.svg').to_dict()


def seed_game(client, player_hand, dealer_hand, wallet=None, pit=None,
              deck=None, high_score=0, biggest_bet=0):
    wallet = wallet or {}
    pit = pit or {}
    session = client.session
    session['game'] = dict(
        deck=[_card_dict(rank) for rank in (deck or [])],
        player_hand=[_card_dict(rank) for rank in player_hand],
        dealer_hand=[_card_dict(rank) for rank in dealer_hand],
        wallet={str(denom): wallet.get(denom, 0) for denom in cl.COIN_LADDER},
        pit={str(denom): pit.get(denom, 0) for denom in cl.COIN_LADDER},
        high_score=high_score,
        biggest_bet=biggest_bet,
    )
    session.save()


class TableViewTests(TestCase):
    def test_pending_hand_offers_hit_and_stand(self):
        seed_game(self.client, ['five', 'six'], ['ten', 'seven'], pit={25: 1})
        response = self.client.get(reverse('blackjack:table'))
        self.assertContains(response, 'id="hit"')
        self.assertContains(response, 'id="stand"')

    def test_natural_blackjack_resolves_without_dealer_drawing(self):
        seed_game(self.client, ['ace', 'king'], ['ten', 'six'], pit={25: 1})
        response = self.client.get(reverse('blackjack:table'))
        self.assertContains(response, 'You won')
        game = tl.GameLogic.from_session(self.client.session)
        self.assertEqual(len(game.dealer_hand), 2)

    def test_hitting_to_21_still_lets_the_dealer_play_out(self):
        # Regression test: table_view used to conclude the bet the instant
        # the player's total hit 21, even when that 21 came from hitting
        # (not a natural) — freezing the dealer's hand mid-draw.
        seed_game(
            self.client,
            player_hand=['ten', 'nine', 'two'],  # 21 via a hit, not natural
            dealer_hand=['ten', 'two'],  # 12, must still draw
            deck=['five'],  # -> 17
            pit={25: 1}, wallet={1: 10},
        )
        response = self.client.get(reverse('blackjack:table'))
        self.assertEqual(response.status_code, 200)
        game = tl.GameLogic.from_session(self.client.session)
        self.assertGreater(len(game.dealer_hand), 2)
        self.assertEqual(game.dealer_total, 17)

    def test_no_bet_and_no_coins_shows_lost(self):
        seed_game(self.client, [], [], wallet={}, pit={})
        response = self.client.get(reverse('blackjack:table'))
        self.assertContains(response, 'Quit')

    def test_no_bet_with_coins_redirects_to_bet(self):
        seed_game(self.client, [], [], wallet={1: 10}, pit={})
        response = self.client.get(reverse('blackjack:table'))
        self.assertRedirects(response, reverse('blackjack:bet'))


class ActionViewTests(TestCase):
    def test_hit_that_busts_resolves_immediately(self):
        seed_game(
            self.client, ['ten', 'nine'], ['ten', 'seven'],
            deck=['five'], pit={25: 1}, wallet={1: 10},
        )
        response = self.client.post(reverse('blackjack:action'), {'action': 'hit'})
        self.assertContains(response, 'Dealer won')

    def test_stand_plays_out_the_dealer(self):
        seed_game(
            self.client, ['ten', 'nine'], ['ten', 'two'],
            deck=['five'], pit={25: 1}, wallet={1: 10},
        )
        response = self.client.post(reverse('blackjack:action'), {'action': 'stand'})
        self.assertContains(response, 'You won')


class BetViewTests(TestCase):
    def setUp(self):
        game = tl.GameLogic.new()
        game.wallet[25] = 4
        game.wallet[5] = 5
        session = self.client.session
        session['game'] = game.to_session_dict()
        session.save()

    def test_bet_coin_moves_a_coin_into_the_pit(self):
        response = self.client.post(reverse('blackjack:bet'), {'action': 'bet_coin', 'denom': '25', 'count': '1'})
        self.assertEqual(response.status_code, 200)
        game = tl.GameLogic.from_session(self.client.session)
        self.assertEqual(game.pit[25], 1)
        self.assertEqual(game.wallet[25], 3)

    def test_place_bet_without_coins_shows_error(self):
        response = self.client.post(reverse('blackjack:bet'), {'action': 'place_bet'})
        self.assertContains(response, 'Put at least one coin in')

    def test_place_bet_redirects_to_table(self):
        self.client.post(reverse('blackjack:bet'), {'action': 'bet_coin', 'denom': '25', 'count': '1'})
        response = self.client.post(reverse('blackjack:bet'), {'action': 'place_bet'})
        self.assertRedirects(response, reverse('blackjack:table'))

    def test_quickplay_bets_and_places(self):
        response = self.client.post(reverse('blackjack:bet'), {'action': 'quickplay'})
        self.assertRedirects(response, reverse('blackjack:table'))

    def test_merge_combines_coins(self):
        self.client.post(reverse('blackjack:bet'), {'action': 'merge', 'denom': '5'})
        game = tl.GameLogic.from_session(self.client.session)
        self.assertEqual(game.wallet[25], 5)
        self.assertEqual(game.wallet[5], 0)

    def test_break_splits_a_coin(self):
        self.client.post(reverse('blackjack:bet'), {'action': 'break', 'denom': '25'})
        game = tl.GameLogic.from_session(self.client.session)
        self.assertEqual(game.wallet[25], 3)
        self.assertEqual(game.wallet[5], 10)

    def test_clear_returns_the_pit(self):
        self.client.post(reverse('blackjack:bet'), {'action': 'bet_coin', 'denom': '25', 'count': '2'})
        self.client.post(reverse('blackjack:bet'), {'action': 'clear'})
        game = tl.GameLogic.from_session(self.client.session)
        self.assertEqual(game.pit[25], 0)
        self.assertEqual(game.wallet[25], 4)


class DivvyViewTests(TestCase):
    def setUp(self):
        session = self.client.session
        session['divvy'] = {str(denom): 0 for denom in cl.COIN_LADDER}
        session.save()

    def test_add_increases_a_denom(self):
        response = self.client.post(reverse('blackjack:divvy'), {'action': 'add', 'denom': '25'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['divvy']['25'], 1)

    def test_add_rejects_over_the_bank(self):
        for _ in range(4):
            self.client.post(reverse('blackjack:divvy'), {'action': 'add', 'denom': '25'})
        self.client.post(reverse('blackjack:divvy'), {'action': 'add', 'denom': '25'})
        self.assertEqual(self.client.session['divvy']['25'], 4)

    def test_remove_decreases_a_denom(self):
        self.client.post(reverse('blackjack:divvy'), {'action': 'add', 'denom': '25'})
        self.client.post(reverse('blackjack:divvy'), {'action': 'remove', 'denom': '25'})
        self.assertEqual(self.client.session['divvy']['25'], 0)

    def test_reset_clears_everything(self):
        self.client.post(reverse('blackjack:divvy'), {'action': 'add', 'denom': '25'})
        self.client.post(reverse('blackjack:divvy'), {'action': 'reset'})
        self.assertEqual(self.client.session['divvy']['25'], 0)

    def test_confirm_requires_exact_bank(self):
        response = self.client.post(reverse('blackjack:divvy'), {'action': 'confirm'})
        self.assertContains(response, 'has to add up to exactly')

    def test_confirm_starts_the_game_when_exact(self):
        for _ in range(4):
            self.client.post(reverse('blackjack:divvy'), {'action': 'add', 'denom': '25'})
        response = self.client.post(reverse('blackjack:divvy'), {'action': 'confirm'})
        self.assertRedirects(response, reverse('blackjack:bet'))

    def test_quickplay_divvies_and_starts_the_game(self):
        response = self.client.post(reverse('blackjack:divvy'), {'action': 'quickplay'})
        self.assertRedirects(response, reverse('blackjack:bet'))
        game = tl.GameLogic.from_session(self.client.session)
        self.assertEqual(game.coins, cl.STARTING_BANK)
