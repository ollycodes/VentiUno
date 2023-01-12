from django.urls import path, include
from . import views

app_name = "blackjack"
urlpatterns = [
    # path('home/', views.HomeView.as_view(), name='home'),
    path('', views.guestform_view, name='index'),
    path('guest/', views.guestform_view, name='guestform'),
    path('game/<int:pk>/', views.game, name='game'),
    path('table/<int:pk>/', views.table, name='table'),
    path('table/<int:pk>/stand/', views.stand, name='stand'),
    path('table/<int:pk>/hit/', views.hit_or_bust, name='hit_or_bust'),
    path('table/<int:pk>/play_again', views.play_again, name='play_again'),
    path('table/new_game/', views.newgame, name='new_game'),
    path('table/quit/', views.quit, name='quit'),
    path('account/', include('django.contrib.auth.urls')),
    path('account/create_profile/', views.userform_view, name='create_account'),
    path('account/profile/', views.profile, name='profile'),
]
