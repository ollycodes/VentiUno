from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotAllowed 
from django.shortcuts import get_object_or_404, render, redirect

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from .forms import GuestForm, TableNameForm
from .models import Table, Player, Guest, Hand
from .logics import blackjack as tl

# FORM VIEWS
def create_guest(request):
    if request.user.is_authenticated:
        return redirect('blackjack:profile')
    elif request.method == 'GET':
        return render(request, 'registration/create_guest.html', dict(form=GuestForm))
    elif request.method == 'POST':
        try: # retrieves guest user, generate_username in models will never re-use the same name
            name = request.POST.get('username')
            guest = get_object_or_404(Guest, username=name)
            request.session['guest'] = dict(pk=guest.pk, name=guest.username)
            return redirect('blackjack:guest_profile')
        except Http404:
            pass
        form = GuestForm(request.POST)
        if form.is_valid():
            guest = form.save()
            request.session['guest'] = dict(pk=guest.pk, name=guest.username)
            return redirect('blackjack:guest_profile')
        else:
            return render(request, 'registration/create_guest.html', dict(form=GuestForm))
    else:
        return HttpResponseNotAllowed(['GET','POST'])

def create_user(request):
    if request.user.is_authenticated:
        return redirect('blackjack:profile')
    elif request.method == 'GET':
        return render(request, 'registration/create_account.html', dict(form=UserCreationForm))
    elif request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # returns user object
            login(request, user)
            request.session['user'] = dict(pk=user.pk, name=user.username)
            return redirect('blackjack:profile')
        else:
            return render(request, 'registration/create_account.html', dict(form=form))
    else:
        return HttpResponseNotAllowed(['GET','POST'])

# GUEST VIEWS
def guest_profile(request):
    if request.user.is_authenticated:
        return redirect('blackjack:profile')
    try:
        guest = request.sessions.get('guest')
        profile = get_object_or_404(Guest, username=guest['name'], pk=guest['pk'])
        return render(request, 'profile.html', dict(user=profile))
    except Http404:
        return render(request, 'registration/create_guest.html', dict(form=GuestForm))

# USER VIEWS
@login_required
def profile(request):
    name = request.user.username
    hands = Hand.objects.filter(name=name, profile_type='PL')
    return render(request, 'profile.html', dict(user=request.user, hands=hands))

# GAME VIEWS
@login_required
def create_new_game(request):
    db_table_obj = Table.objects.create(deck={})
    db_table_obj.name = f"Table {db_table_obj.pk}"
    db_table_obj.save()
    db_dealer_obj = Hand.objects.create(table=db_table_obj, profile_type='DL', name='Dealer', hand={})
    db_dealer_obj.save()
    name = request.user.username
    db_player_obj = Hand.objects.create(table=db_table_obj, profile_type='PL', name=name, hand={})
    db_player_obj.save()
    return redirect('blackjack:initial_draw', pk=db_table_obj.pk)
        

@login_required
def delete_view(request):
    name = request.user.username
    hands = Hand.objects.filter(name=name, profile_type='PL').order_by('table__last_played')
    return render(request, 'blackjack/table/delete.html', dict(user=request.user, hands=hands))

def delete(request, pk):
    Table.objects.filter(pk=pk).delete()
    return redirect('blackjack:delete_view')

def load_game_instance(name, pk):
    table = get_object_or_404(Table, pk=pk)
    player = get_object_or_404(Hand, name=name, profile_type='PL', table=table) 
    dealer = get_object_or_404(Hand, name='Dealer', profile_type='DL', table=table)
    game = tl.GameLogic.load(table, player, dealer)
    db_objects = dict(table=table, player=player, dealer=dealer)
    return game, db_objects

def initial_draw(request, pk):
    name = request.user.username
    game, db_objects = load_game_instance(name, pk)
    game.create_and_deal()
    game.save_action(db_objects)
    return redirect('blackjack:game', pk=pk)

def game_view(request, pk):
    return render(request, 'blackjack/game.html', dict(pk=pk))

def table_view(request, pk):
    name = request.user.username
    game, _ = load_game_instance(name, pk)
    if game.player_total >= 21:
        return render(request, 'blackjack/table/bust.html', dict(game=game, pk=pk))
    return render(request, 'blackjack/table/pending.html', dict(game=game, pk=pk))

def change_name(request, pk):
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

def action(request, pk):
    name = request.user.username
    game, db_objects = load_game_instance(name, pk)
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
    name = request.user.username
    game, db_table_obj = load_game_instance(name, pk)
    game.check_deck()
    game.save_action(db_table_obj)
    return redirect('blackjack:table', pk)
