from django.urls import path

from . import views

app_name = "bj"
urlpatterns = [
    path('', views.index, name="index"),
    path('game/', views.setup, name="setup"),
    path('game/<int:pk>/', views.game, name="game"),
    path('game/<int:pk>/hit/', views.hit, name="hit"),
    path('game/<int:pk>/stand/', views.stand, name="stand"),
]
