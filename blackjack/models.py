from django.db import models # models.signals import post_save
from django.contrib.auth.models import User
from .logics.gen import generate_username
from django.urls import reverse

class GuestTable(models.Model):
    username = models.CharField(max_length=24, unique=True, default=generate_username())
    game_data = models.JSONField()
    #coin = models.PositiveIntegerField()

    def get_absolute_url(self):
        return reverse('blackjack:table', kwargs={'pk':self.pk})

class UserTable(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    game_data = models.JSONField()

    def get_absolute_url(self):
        return reverse('blackjack:table', kwargs={'pk':self.pk})

    @property
    def username(self):
        return self.user.username

# The idea:
#     1. table holds the dealer's hand
#     2. each player is a model that has a username, hand, and table they are assigned to
#         a. each player only has one table assigned to them
#         b. each table can have multiple players assigned to it
# The questions:
#     1. foreignkey must be on the players right?
#     2. how would I go about creating the views if each player might be on a different page?
#         a. player one has hit, player two has not acted


'''
class TablePlayer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    deck = models.JSONField()
    dealer_hand = models.JSONField()
    turn = models.JSONField()
    history = models.JSONField()

class Table(models.Model):
    dealer_hand = models.JSONField()
    tableplayers = models.ManyToManyField(TablePlayer)
'''
