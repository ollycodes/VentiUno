# from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotAllowed 
from django.shortcuts import get_object_or_404, get_list_or_404, render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.template import context

from .forms import GuestForm, RegistrationForm, BetForm
from .models import Table, UserProxy, Player, Guest, Dealer
from .logics import blackjack as tl

def home(request):
    if request.user.is_authenticated:
        return redirect('blackjack:profile')
    elif request.method == 'GET':
        return render(request, 'blackjack/home.html')
    else:
        return HttpResponseNotAllowed(['GET'])

# FORM VIEWS
def guest_form(request):
    if request.method == 'GET':
        return render(request, 'guest/form.html', dict(form=GuestForm))
    elif request.method == 'POST':
        try:
            name = request.POST.get('name')
            guest = get_object_or_404(Guest, name=name)
            request.session['guest_info'] = dict(pk=guest.pk, name=guest.name)
            return redirect('blackjack:guest')
        except Http404:
            pass
        form = GuestForm(request.POST)
        if form.is_valid():
            guest = form.save()
            request.session['guest_info'] = dict(pk=guest.pk, name=guest.name)
            return redirect('blackjack:new_game')
        else:
            return render(request, 'guest/form.html', dict(form=form))
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

def user_form(request):
    if request.method == 'GET':
        return render(request, 'registration/form.html', dict(form=RegistrationForm))
    elif request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save() # returns user object
            proxy = UserProxy.objects.create(user=user)
            proxy.save()
            login(request, user)
            return redirect('blackjack:profile')
        else:
            return render(request, 'registration/form.html', dict(form=form))
    else:
        return HttpResponseNotAllowed(['GET','POST'])

# PROFILE VIEWS
def guest_or_user(request):
    if request.user.is_authenticated:
        player = get_object_or_404(UserProxy, user=request.user)
    else:
        name = request.session.get('guest_info')['name']
        player = get_object_or_404(Guest, name=name)
    return player

def guest_profile(request):
    if request.user.is_authenticated:
        return redirect('blackjack:profile')
    try:
        guest = guest_or_user(request)
        games = Player.objects.filter(
            content_type=ContentType.objects.get_for_model(guest), 
            object_id=guest.id,
        ).order_by('table__last_played')
        return render(request, 'guest/profile.html', dict(player=guest, games=games))
    except Http404:
        return render(request, 'guest/profile.html')

@login_required
def user_profile(request):
    proxy = get_object_or_404(UserProxy, user=request.user)
    try:
        games = Player.objects.filter(
            content_type=ContentType.objects.get_for_model(proxy), 
            object_id=proxy.id,
        ).order_by('table__last_played')
        return render(request, 'user/profile.html', dict(user=request.user, games=games))
    except Http404:
        pass
    return render(request, 'user/profile.html', dict(user=request.user))

# GAME VIEWS
def load_game_instance(request, pk):
    table = get_object_or_404(Table, pk=pk)
    user_guest = guest_or_user(request)
    player = get_object_or_404(
        Player,
        content_type=ContentType.objects.get_for_model(user_guest),
        object_id=user_guest.id,
        table=table
    )
    dealer = table.dealer
    game = tl.GameLogic.load(table, player, dealer)
    db_objects = dict(table=table, player=player, dealer=dealer, user_guest=user_guest)
    return game, db_objects

def create_new_game(request):
    table = Table.objects.create(deck={})
    table.save()

    dealer = Dealer.objects.create(table=table, hand={})
    dealer.save()

    user_guest = guest_or_user(request)
    player = Player.objects.create(
        table=table, 
        content_type=ContentType.objects.get_for_model(user_guest), 
        object_id=user_guest.id,
        hand={}
    )
    player.save()
    return redirect('blackjack:game', pk=table.pk)

def bet_view(request, pk):
    if request.method == "GET":
        game, db_objects = load_game_instance(request, pk)
        context = dict(form=BetForm(instance=db_objects['player']), pk=pk, game=game)
        if game.bet != 0:
            game.conclude_bet()
            game.save_action(db_objects)
        return render(request, "blackjack/table/bet.html", context)
    elif request.method == 'POST':
        form = BetForm(request.POST)
        if form.is_valid():
            game, db_objects = load_game_instance(request, pk)
            game.player_bet(form.cleaned_data['bet'])
            game.check_deck()
            game.save_action(db_objects)
            return redirect("blackjack:game", pk)
        else:
            game, db_objects = load_game_instance(request, pk)
            context = dict(form=form, pk=pk, game=game)
            return render(request, "blackjack/table/bet.html", context)
    else:
        return HttpResponseNotAllowed(['GET','POST'])

def game_view(request, pk):
    return render(request, 'blackjack/game.html', dict(pk=pk))

def table_view(request, pk):
    game, db_objects = load_game_instance(request, pk)
    context = dict(game=game, player=db_objects['user_guest'], pk=pk)
    if game.bet == 0:
        return redirect("blackjack:bet", pk)
    elif game.player_total >= 21 or game.dealer_card_count > 2:
        return render(request, 'blackjack/table/bust.html', context)
    return render(request, 'blackjack/table/pending.html', context)

def action(request, pk):
    game, db_objects = load_game_instance(request, pk)
    context = dict(game=game, player=db_objects['user_guest'], pk=pk)
    if request.POST.get('action') == 'stand':
        game.stand()
        game.save_action(db_objects)
        return render(request, 'blackjack/table/stand.html', context)
    elif request.POST.get('action') == 'hit':
        game.hit()
        game.save_action(db_objects)
        if game.player_total >= 21:
            return render(request, 'blackjack/table/bust.html', context)
    return redirect('blackjack:table', pk)

def delete_view(request):
    user_guest = guest_or_user(request)
    tables = Player.objects.filter(
        content_type=ContentType.objects.get_for_model(user_guest), 
        object_id=user_guest.id,
    ).order_by('table__last_played')
    context = dict(player=user_guest, games=tables)
    return render(request, 'blackjack/table/delete.html', context) 

def delete(request, pk):
    Table.objects.filter(pk=pk).delete()
    return redirect('blackjack:delete_view')
