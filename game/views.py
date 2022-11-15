from django.shortcuts import render, redirect, get_object_or_404

from . import forms, table_logics, models

def index(request):
    form = forms.TableForm()
    return render(request, 'game/index.html', {'form': form})

def setup(request):
    if request.method == 'POST':
        partial_form = forms.TableForm(request.POST)
        if partial_form.is_valid():
            table = partial_form.save(commit=False)
            game = table_logics.Game.create()
            game.save(table)
            return redirect("bj:game", pk=table.pk)
    else:
        form = forms.TableForm()
        return render(request, 'game/index.html', {'form': form})

def game(request, pk):
    table = get_object_or_404(models.Table, pk=pk)
    game = table_logics.Game.load(table)
    return render(request, 'game/game.html', dict(table=table, game=game))

def hit(request, pk):
    table = get_object_or_404(models.Table, pk=pk)
    game = table_logics.Game.load(table)
    # game is a class intance now residing as a local var
    game.hit()
    game.save(table)
    return redirect("bj:game", pk=pk)

def stand(request, pk):
    table = get_object_or_404(models.Table, pk=pk)
    game = table_logics.Game.load(table)
    game.is_finished = True
    game.stand(table)
    game.save(table)
    return redirect("bj:game", pk=pk)
