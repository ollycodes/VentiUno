from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect

from .forms import LeaderboardEntryForm
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
    context = dict(has_game='game' in request.session, has_divvy='divvy' in request.session)
    return render(request, 'blackjack/home.html', context)


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
    request.session.pop('game', None)
    request.session.pop('leaderboard_submitted', None)
    request.session['divvy'] = {str(denom): 0 for denom in cl.COIN_LADDER}
    return redirect('blackjack:divvy')


def divvy_view(request):
    """
    Bank setup: before the first bet, the player picks how their starting
    bank is divided into physical coins. Nothing here touches game.wallet
    directly — it builds up request.session['divvy'] until it adds up to
    exactly STARTING_BANK, only then does a GameLogic (and session['game'])
    get created.
    """
    stored = request.session.get('divvy')
    if stored is None:
        return redirect('blackjack:home')
    divvy = {denom: stored.get(str(denom), 0) for denom in cl.COIN_LADDER}
    error = None

    if request.method == 'POST':
        action_name = request.POST.get('action')
        denom = request.POST.get('denom')
        denom = int(denom) if denom and denom.isdigit() and int(denom) in cl.COIN_LADDER else None
        total = sum(d * c for d, c in divvy.items())

        if action_name == 'add' and denom is not None and total + denom <= cl.STARTING_BANK:
            divvy[denom] += 1
        elif action_name == 'remove' and denom is not None and divvy[denom] > 0:
            divvy[denom] -= 1
        elif action_name == 'reset':
            divvy = {denom: 0 for denom in cl.COIN_LADDER}
        elif action_name == 'quickplay':
            # Quickplay is a single "just get me playing" action: it fills
            # the divvy and immediately starts the game, same as picking a
            # reasonable split by hand and then confirming it.
            game = tl.GameLogic.new()
            game.wallet = tl.quickplay_divvy(cl.STARTING_BANK)
            game.save(request.session)
            request.session.pop('divvy', None)
            return redirect('blackjack:bet')
        elif action_name == 'confirm':
            if total == cl.STARTING_BANK:
                game = tl.GameLogic.new()
                game.wallet = divvy
                game.save(request.session)
                request.session.pop('divvy', None)
                return redirect('blackjack:bet')
            error = f"Your bank has to add up to exactly {cl.STARTING_BANK}."

        request.session['divvy'] = {str(denom): count for denom, count in divvy.items()}

    total = sum(d * c for d, c in divvy.items())
    context = dict(
        divvy=divvy, total=total, remaining=cl.STARTING_BANK - total,
        # A coin bigger than the whole bank can never be added, so it's left
        # off the ladder entirely instead of shown permanently disabled.
        coin_ladder=[denom for denom in cl.COIN_LADDER if denom <= cl.STARTING_BANK],
        starting_bank=cl.STARTING_BANK, error=error,
    )
    return render_table(request, 'blackjack/table/divvy.html', context)


def table_view(request):
    """
    A pure GET — nothing here mutates the game, so the round is either
    already fully wrapped up (in which case the outcome screen was already
    shown by whichever POST concluded it) or still genuinely open.
    """
    game = tl.GameLogic.from_session(request.session)
    if game is None:
        return redirect('blackjack:home')

    if game.bet == 0 and game.split_bet == 0:
        if game.coins == 0:
            context = _lost_context(request, game)
            return render_table(request, 'blackjack/table/lost.html', context)
        return redirect('blackjack:bet')
    if not game.insurance_decided:
        return render_table(request, 'blackjack/table/insurance.html', game_context(request, game))
    return render_table(request, 'blackjack/table/pending.html', game_context(request, game))


def _render_round_state(request, game):
    """
    Renders whatever the hand calls for right after a move that may have
    changed it: the round just concluded, an insurance decision is still
    pending, or play continues. Shared by bet_view (right after dealing)
    and action() (right after hit/stand/double/split/insurance) so the
    response always reflects state as of that same request.
    """
    if game.bet == 0 and game.split_bet == 0:
        if game.coins == 0:
            context = _lost_context(request, game)
            return render_table(request, 'blackjack/table/lost.html', context)
        return render_table(request, 'blackjack/table/resolved.html', game_context(request, game))
    if not game.insurance_decided:
        return render_table(request, 'blackjack/table/insurance.html', game_context(request, game))
    return render_table(request, 'blackjack/table/pending.html', game_context(request, game))


def bet_view(request):
    game = tl.GameLogic.from_session(request.session)
    if game is None:
        return redirect('blackjack:home')

    error = None
    if request.method == 'POST':
        action_name = request.POST.get('action')
        denom = request.POST.get('denom')
        denom = int(denom) if denom and denom.isdigit() and int(denom) in cl.COIN_LADDER else None
        count = request.POST.get('count')
        # A shift/ctrl-click sends a huge sentinel count meaning "as many as
        # I have"; bet_coin/unbet_coin already clamp to what's on hand.
        count = int(count) if count and count.isdigit() else 1

        if action_name == 'bet_coin' and denom is not None:
            game.bet_coin(denom, count)
        elif action_name == 'unbet_coin' and denom is not None:
            game.unbet_coin(denom, count)
        elif action_name == 'clear':
            game.clear_bet()
        elif action_name == 'break' and denom is not None:
            game.break_coin(denom)
        elif action_name == 'merge' and denom is not None:
            game.merge_coins(denom)
        elif action_name in ('place_bet', 'quickplay'):
            if action_name == 'quickplay':
                game.quickplay_bet()
            if game.bet > 0:
                game.deal_hand()
                game.save(request.session)
                return _render_round_state(request, game)
            error = "Put at least one coin in before placing your bet."

        game.save(request.session)

    context = game_context(
        request, game, merge_options=tl.merge_options(game.wallet),
        break_options=tl.break_options(game.wallet), error=error,
    )
    return render_table(request, 'blackjack/table/bet.html', context)


def action(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    game = tl.GameLogic.from_session(request.session)
    if game is None:
        return redirect('blackjack:home')

    move = request.POST.get('action')
    if move == 'hit':
        game.hit()
    elif move == 'stand':
        game.stand()
    elif move == 'double':
        game.double()
    elif move == 'split':
        game.split()
    elif move == 'insurance_yes':
        game.decide_insurance(True)
    elif move == 'insurance_no':
        game.decide_insurance(False)
    else:
        return redirect('blackjack:table')
    game.save(request.session)
    return _render_round_state(request, game)


def lost(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    game = tl.GameLogic.from_session(request.session)
    if game is None:
        return redirect('blackjack:home')

    move = request.POST.get('action')
    if move == 'Continue?':
        game.conclude_bet()
        game.wallet[1000] = game.wallet.get(1000, 0) + 1
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
