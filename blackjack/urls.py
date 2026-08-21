from django.urls import path
from . import views

app_name = "blackjack"
urlpatterns = [
    path("", views.home, name="home"),
    path("options/", views.options_view, name="options"),
    path("leaderboard/", views.leaderboard_view, name="leaderboard"),
    path("leaderboard/submit/", views.leaderboard_submit, name="leaderboard_submit"),
    # game views
    path("game/new/", views.new_game, name="new_game"),
    path("game/", views.table_view, name="table"),
    path("game/bet/", views.bet_view, name="bet"),
    path("game/action/", views.action, name="action"),
    path("game/lost/", views.lost, name="lost"),
]
