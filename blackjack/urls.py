from django.urls import path, include
from . import views

app_name = "blackjack"
urlpatterns = [
    path('', views.create_guest, name='index'),
    path('guest/create', views.create_guest, name='guestform'),
    path('guest/profile', views.guest_profile, name='guest_profile'),
    path('account/create/', views.create_user, name='create_account'),
    path('account/profile/', views.profile, name='profile'),
    path('account/', include('django.contrib.auth.urls')),
    path('game/create', views.create_new_game, name='new_game'),
    path('game/delete/', views.delete_view, name='delete_view'),
    path('game/delete/<int:pk>/', views.delete, name='delete_game'),
    path('game/table/draw/<int:pk>/', views.initial_draw, name='initial_draw'),
    path('game/<int:pk>/', views.game_view, name='game'),
    path('table/<int:pk>/', views.table_view, name='table'),
    path('table/<int:pk>/action', views.action, name='action'),
    path('table/<int:pk>/play_again/', views.play_again, name='play_again'),
    path('table/<int:pk>/change_name/', views.change_name, name='change_name'),
]