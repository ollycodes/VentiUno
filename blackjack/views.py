# from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotAllowed 
from django.shortcuts import get_object_or_404, get_list_or_404, render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType

from .forms import GuestForm, TableNameForm
from .models import Table, UserProxy, Player, Guest, Dealer
from .logics import blackjack as tl

# FORM VIEWS
def landing_page(request):
    if request.user.is_authenticated:
        return redirect('blackjack:profile')
    elif request.method == 'GET':
        return render(request, 'blackjack/landing_page.html', dict(form=GuestForm))
    elif request.method == 'POST':
        try:
            name = request.POST.get('name')
            guest = get_object_or_404(Guest, name=name)
            request.session['guest_info'] = dict(pk=guest.pk, name=guest.name)
            return redirect('blackjack:guest_profile')
        except Http404:
            pass
        form = GuestForm(request.POST)
        if form.is_valid():
            guest = form.save()
            request.session['guest_info'] = dict(pk=guest.pk, name=guest.name)
            return redirect('blackjack:guest_profile')
        else:
            return render(request, 'blackjack/landing_page.html', dict(form=GuestForm))
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

def create_user(request):
    if request.user.is_authenticated:
        return redirect('blackjack:profile')
    elif request.method == 'GET':
        return render(request, 'registration/create_account.html', dict(form=UserCreationForm))
    elif request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # returns user object
            proxy = UserProxy.objects.create(user=user)
            proxy.save()
            login(request, user)
            return redirect('blackjack:profile')
        else:
            return render(request, 'registration/create_account.html', dict(form=form))
    else:
        return HttpResponseNotAllowed(['GET','POST'])

def change_table_name(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if request.method == 'GET':
        form = TableNameForm(request.POST, instance=table)
        return render(request, 'blackjack/table/change_name/form.html', dict(form=form, pk=pk))
    elif request.method == 'POST':
        form = TableNameForm(request.POST, instance=table)
        if form.is_valid():
            table = form.save()
            return render(request, 'blackjack/table/change_name/success.html', dict(table=table, pk=pk))
        else:
            return render(request, 'blackjack/table/change_name/form.html', dict(form=form, pk=pk))

# PROFILE VIEWS
def guest_profile(request):
    if request.user.is_authenticated:
        return redirect('blackjack:profile')
    try:
        guest_info = request.session.get('guest_info')
        guest = get_object_or_404(Guest, name=guest_info['name'], pk=guest_info['pk'])
        player = get_object_or_404(
            Player, 
            content_type=ContentType.objects.get_for_model(guest), 
            object_id=guest.id
        )
        print('here')
        return render(request, 'guest/profile.html', dict(guest=guest, game=player.table))
    except Http404:
        return render(request, 'blackjack/landing_page.html')

@login_required
def user_profile(request):
    proxy = get_object_or_404(UserProxy, user=request.user)
    try:
        players = Player.objects.filter(
            content_type=ContentType.objects.get_for_model(proxy), 
            object_id=proxy.id
        )
        tables = Table.objects.filter(id__in=players.values_list('table', flat=True))
        return render(request, 'user/profile.html', dict(user=request.user, games=tables))
    except Http404:
        pass
    return render(request, 'user/profile.html', dict(user=request.user))

# GAME VIEWS
def guest_or_player(request):
    if request.user.is_authenticated:
        player = get_object_or_404(UserProxy, user=request.user)
    else:
        name = request.session.get('guest_info')['name']
        player = get_object_or_404(Guest, username=name)
    return player

def load_game_instance(request, pk):
    table = get_object_or_404(Table, pk=pk)
    dealer = get_object_or_404(Dealer, table=table)
    user_guest = guest_or_player(request)
    player = get_object_or_404(
        Player, 
        content_type=ContentType.objects.get_for_model(user_guest), 
        object_id=user_guest.id,
        table=table
    )
    game = tl.GameLogic.load(table, player, dealer)
    db_objects = dict(table=table, player=player, dealer=dealer)
    return game, db_objects

def create_new_game(request):
    table = Table.objects.create(deck={})
    table.name = f"Table {table.pk}"
    table.save()

    dealer = Dealer.objects.create(table=table, hand={})
    dealer.save()

    user_guest = guest_or_player(request)
    player = Player.objects.create(
        table=table, 
        content_type=ContentType.objects.get_for_model(user_guest), 
        object_id=user_guest.id,
        hand={}
    )
    player.save()
    return redirect('blackjack:initial_draw', pk=table.pk)

def initial_draw(request, pk):
    game, db_objects = load_game_instance(request, pk)
    game.create_and_deal()
    game.save_action(db_objects)
    return redirect('blackjack:game', pk=pk)

def game_view(request, pk):
    return render(request, 'blackjack/game.html', dict(pk=pk))

def table_view(request, pk):
    game, _ = load_game_instance(request, pk)
    if game.player_total >= 21:
        return render(request, 'blackjack/table/bust.html', dict(game=game, pk=pk))
    return render(request, 'blackjack/table/pending.html', dict(game=game, pk=pk))

def action(request, pk):
    game, db_objects = load_game_instance(request, pk)
    if request.POST.get('action') == 'stand':
        game.stand()
        game.save_action(db_objects)
        return render(request, 'blackjack/table/stand.html', dict(game=game, pk=pk))
    elif request.POST.get('action') == 'hit':
        game.hit()
        game.save_action(db_objects)
        if game.player_total >= 21:
            return render(request, 'blackjack/table/bust.html', dict(game=game, pk=pk))
    return redirect('blackjack:table', pk)

def play_again(request, pk):
    game, db_table_obj = load_game_instance(request, pk)
    game.check_deck()
    game.save_action(db_table_obj)
    return redirect('blackjack:table', pk)

def delete_view(request):
    name, profile_type = guest_or_player(request)
    hands = Hand.objects.filter(name=name, profile_type=profile_type).order_by('table__last_played')
    return render(request, 'blackjack/table/delete.html', dict(user=request.user, hands=hands))

def delete(request, pk):
    Table.objects.filter(pk=pk).delete()
    return redirect('blackjack:delete_view')
