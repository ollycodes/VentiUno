from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotAllowed 
from django.shortcuts import get_object_or_404, render, redirect

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from .forms import GuestForm
from .models import GuestTable, UserTable
from .logics import table as tl

# FORM VIEWS
def guestform_view(request):
    if request.user.is_authenticated:
        return redirect('blackjack:profile')
    elif request.method == 'GET':
        return render(request, 'blackjack/guest.html', dict(guest_form=GuestForm))
    elif request.method == 'POST':
        try: # attempts to find a previously abandoned game via the username
            name = request.POST.get('username')
            table = get_object_or_404(GuestTable, username=name)
            return redirect(table)
        except Http404:
            pass
        form = GuestForm(request.POST)
        if form.is_valid():
            table = form.save(commit=False) # returns GuestTable object
            game = tl.Game.create()
            game.save(table)
            request.session['game'] = [table.pk, table.username]
            return redirect('blackjack:game', pk=table.pk)
        else:
            return render(request, 'blackjack/guest.html', dict(guest_form=GuestForm))
    else:
        return HttpResponseNotAllowed(['GET','POST'])

def userform_view(request):
    if request.user.is_authenticated:
        return redirect('blackjack:profile')
    elif request.method == 'GET':
        return render(request, 'registration/create_user.html', dict(form=UserCreationForm))
    elif request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # returns user object
            login(request, user)
            return redirect('blackjack:profile')
        else:
            return render(request, 'registration/create_account.html', dict(form=form))
    else:
        return HttpResponseNotAllowed(['GET','POST'])

# GAME VIEWS & HELPER FUNCTIONS
def permission_denied_redirect(func):
    '''redirects to 'guestform' if session does not match; requires table_model_pick'''
    def decorated(*args, **kwargs):
        try: # runs the function here, exits if permissiondenied
            return func(*args, **kwargs)
        except PermissionDenied:
            return redirect('blackjack:guestform')
    return decorated

def table_model_pick(request, pk):
    model = UserTable if request.user.is_authenticated else GuestTable
    table = get_object_or_404(model, pk=pk)
    if request.session.get('game') != [table.pk, table.username]:
        raise PermissionDenied()
    game = tl.Game.load(table)
    return game, table

def game(request, pk):
    return render(request, 'blackjack/game.html', dict(id=pk))

@permission_denied_redirect
def table(request, pk):
    game, table = table_model_pick(request, pk)
    return render(request, 'blackjack/table.html', dict(table=table, game=game))

@permission_denied_redirect
def stand(request, pk):
    game, table = table_model_pick(request, pk)
    game.stand(table)
    game.save(table)
    return render(request, 'blackjack/stand.html', dict(table=table, game=game))

@permission_denied_redirect
def hit_or_bust(request, pk):
    game, table = table_model_pick(request, pk)
    game.hit()
    game.save(table)
    if game.player_total >= 21:
        return render(request, 'blackjack/bust.html', dict(table=table, game=game))
    else:
        return redirect(table)

@permission_denied_redirect
def play_again(request, pk):
    game, table = table_model_pick(request, pk)
    game.check_deck()
    game.save(table)
    return redirect(table)

def quit(request, pk):
    game, table = table_model_pick(request, pk)
    table.game_data = {}
    game.save(table)
    return redirect('blackjack:guestform')

# USER VIEWS
@login_required
def profile(request):
    return render(request, 'registration/profile.html', dict(user=request.user))

@login_required
def newgame(request):
    try:
        table = get_object_or_404(UserTable, user=request.user)
    except Http404:
        table = UserTable.objects.create(user=request.user, game_data={})
    game = tl.Game.create()
    game.save(table)
    request.session['game'] = [table.pk, table.username]
    return redirect('blackjack:game', pk=table.pk)

