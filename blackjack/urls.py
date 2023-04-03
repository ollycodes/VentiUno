from django.urls import path, include
from . import views

app_name = "blackjack"
urlpatterns = [
    path('', views.home,name='home'),
    path('create/guest/', views.guest_form, name='guest_form'),
    path('create/user/', views.user_form, name='user_form'),

    path('guest/', views.guest_profile, name='guest'),
    path('account/profile/', views.user_profile, name='profile'),
    path('account/', include('django.contrib.auth.urls')),

    path('game/<int:pk>/', views.game_view, name='game'),
    path('game/create', views.create_new_game, name='new_game'),
    path('game/delete/', views.delete_view, name='delete_view'),
    path('game/delete/<int:pk>/', views.delete, name='delete_game'),

    path('table/<int:pk>/', views.table_view, name='table'),
    path('table/<int:pk>/bet', views.bet_view, name='bet'),
    path('table/<int:pk>/action', views.action, name='action'),
]
