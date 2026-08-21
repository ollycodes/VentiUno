from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect

from .forms import BetForm, LeaderboardEntryForm
from .models import LeaderboardEntry
from .logics import blackjack as tl
from .logics import card as cl

LEADERBOARD_SIZE = 10


def render_table(request, template_name, context):
    """
    Renders a game-state partial. An htmx-triggered action gets just the
    partial swapped into #table; a plain browser navigation gets the same
    partial wrapped in a full page, in a single request.
    """
    if request.headers.get('HX-Request') == 'true':
        return render(request, template_name, context)
    return render(request, 'blackjack/table.html', {**context, 'inner_template': template_name})


def get_deck_style(request):
    style = request.session.get('deck_style', cl.DEFAULT_DECK_STYLE)
    return style if style in cl.DECK_STYLES else cl.DEFAULT_DECK_STYLE


def game_context(request, game, **extra):
    context = dict(game=game, deck_style=get_deck_style(request))
    context.update(extra)
    return context


def leaderboard_qualifies(score):
    if score <= 0:
        return False
    entries = LeaderboardEntry.objects.order_by('-score')[:LEADERBOARD_SIZE]
    if len(entries) < LEADERBOARD_SIZE:
        return True
    return score > entries[LEADERBOARD_SIZE - 1].score


def home(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    return render(request, 'blackjack/home.html', dict(has_game='game' in request.session))


def options_view(request):
    if request.method == 'POST':
        style = request.POST.get('deck_style')
        if style in cl.DECK_STYLES:
            request.session['deck_style'] = style
    elif request.method != 'GET':
        return HttpResponseNotAllowed(['GET', 'POST'])

    styles = [(style, style.replace('_', ' ').title()) for style in cl.DECK_STYLES]
    context = dict(styles=styles, current=get_deck_style(request))
    if request.headers.get('HX-Request') == 'true':
        return render(request, 'blackjack/table/deck_style_grid.html', context)
    return render(request, 'blackjack/options.html', context)


def leaderboard_view(request):
    entries = LeaderboardEntry.objects.order_by('-score')[:LEADERBOARD_SIZE]
    return render(request, 'blackjack/leaderboard.html', dict(entries=entries))


def leaderboard_submit(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    game = tl.GameLogic.from_session(request.session)
    if game is None or not leaderboard_qualifies(game.high_score) or request.session.get('leaderboard_submitted'):
        return redirect('blackjack:table')

    form = LeaderboardEntryForm(request.POST)
    if form.is_valid():
        entry = form.save(commit=False)
        # score/biggest_bet always come from the server-held session state,
        # never from the submitted form, so a score can't be spoofed.
        entry.score = game.high_score
        entry.biggest_bet = game.biggest_bet
        entry.save()
        request.session['leaderboard_submitted'] = True

    context = game_context(request, game, qualifies=False, submitted=True)
    return render_table(request, 'blackjack/table/lost.html', context)


def new_game(request):
    request.session['game'] = tl.GameLogic.new().to_session_dict()
    request.session.pop('leaderboard_submitted', None)
    return redirect('blackjack:table')


def table_view(request):
    game = tl.GameLogic.from_session(request.session)
    if game is None:
        return redirect('blackjack:home')

    if game.bet == 0:
        if game.coins == 0:
            context = _lost_context(request, game)
            return render_table(request, 'blackjack/table/lost.html', context)
        return redirect('blackjack:bet')
    elif game.player_total >= 21 or game.dealer_card_count > 2:
        game.conclude_bet()
        game.save(request.session)
        if game.coins == 0:
            context = _lost_context(request, game)
            return render_table(request, 'blackjack/table/lost.html', context)
        return render_table(request, 'blackjack/table/bust.html', game_context(request, game))
    return render_table(request, 'blackjack/table/pending.html', game_context(request, game))


def bet_view(request):
    game = tl.GameLogic.from_session(request.session)
    if game is None:
        return redirect('blackjack:home')

    if request.method == 'GET':
        form = BetForm(max_bet=max(game.coins, 1))
        return render_table(request, 'blackjack/table/bet.html', game_context(request, game, form=form))
    elif request.method == 'POST':
        form = BetForm(request.POST, max_bet=max(game.coins, 1))
        if form.is_valid():
            game.player_bet(form.cleaned_data['bet'])
            game.check_deck()
            game.save(request.session)
            return redirect('blackjack:table')
        return render_table(request, 'blackjack/table/bet.html', game_context(request, game, form=form))
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])


def action(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    game = tl.GameLogic.from_session(request.session)
    if game is None:
        return redirect('blackjack:home')

    move = request.POST.get('action')
    if move == 'stand':
        game.stand()
        game.save(request.session)
        if game.coins == 0 and game.winner == 'Dealer won':
            context = _lost_context(request, game)
            return render_table(request, 'blackjack/table/lost.html', context)
        return render_table(request, 'blackjack/table/stand.html', game_context(request, game))
    elif move == 'hit':
        game.hit()
        game.save(request.session)
        if game.player_total > 21:
            game.conclude_bet()
            game.save(request.session)
            if game.coins == 0:
                context = _lost_context(request, game)
                return render_table(request, 'blackjack/table/lost.html', context)
            return render_table(request, 'blackjack/table/bust.html', game_context(request, game))
    return redirect('blackjack:table')


def lost(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    game = tl.GameLogic.from_session(request.session)
    if game is None:
        return redirect('blackjack:home')

    move = request.POST.get('action')
    if move == 'Continue?':
        game.conclude_bet()
        game.coins += 1000
        game.save(request.session)
        request.session.pop('leaderboard_submitted', None)
        return redirect('blackjack:table')
    elif move == 'Quit':
        request.session.pop('game', None)
        request.session.pop('leaderboard_submitted', None)
        return redirect('blackjack:home')
    return redirect('blackjack:table')


def _lost_context(request, game):
    qualifies = (
        not request.session.get('leaderboard_submitted')
        and leaderboard_qualifies(game.high_score)
    )
    return game_context(request, game, qualifies=qualifies, form=LeaderboardEntryForm())
