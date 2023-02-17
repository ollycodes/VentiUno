from django.db import models
from django.contrib.auth.models import User
from .logics.gen import generate_username
from django.urls import reverse

class Table(models.Model):
    name = models.CharField(max_length=24, blank=True)
    deck = models.JSONField()
    last_played = models.TimeField(auto_now_add=True, blank=True)


# rename create_new_game view into 'solo play'
# create a new link to host a new game, ask how many will be joining
# create a shareable link to join players to game
# create a list of pending_players, based on those who join
# allow host to lock entry or keep open

# new feature ideas
# provide options to change rules of solo/multiplayer game
# provide options to play as dealer maybe!
# provide options to view history of games

# Guest Models
class Guest(models.Model):
    username = models.CharField(max_length=24, unique=True, default=generate_username())
    tables = models.ManyToManyField(Table)

# User Models
class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tables = models.ManyToManyField(Table)

    @property
    def username(self):
        return self.user.username

class Hand(models.Model):

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['table', 'name', 'profile_type'], name='unique_players'),
        ]

    class AccountTypes(models.TextChoices):
        PLAYER = 'PL', 'Player'
        DEALER = 'DL', 'Dealer'

    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='hands')
    profile_type = models.CharField(max_length=2, choices=AccountTypes.choices)
    name = models.CharField(max_length=48)
    hand = models.JSONField()
