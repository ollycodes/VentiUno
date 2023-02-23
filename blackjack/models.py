from django.db import models
from django.contrib.auth.models import User
from .logics.gen import generate_username

class Table(models.Model):

    class CardBackTypes(models.TextChoices):
        ABSTRACT = 'ABS', 'abstract'
        CLOUDS = 'CLD', 'abstract_clouds'
        SCENE = 'SCE', 'abstract_clouds'
        ASTRONAUT = 'AST', 'astronaut'
        BLUE = 'BL1', 'blue'
        BlUETWO = 'BL2', 'blue2'
        CARS = 'CAR', 'cars'
        CASTLE = 'CAS', 'castle'
        FISH = 'FSH', 'fish'
        FROG = 'FRG', 'frog'
        RED = 'RD1', 'red'
        REDTWO = 'RD2', 'red2'

    class StateTypes(models.TextChoices):
        PLAYER_TURN = 'PLYR', 'player'
        DEALER_TURN = 'DLER', 'Dealer'
        BET = 'BET', 'bet'
    
    table_name = models.CharField(max_length=24, blank=True)
    last_played = models.TimeField(auto_now_add=True, blank=True)
    is_open = models.BooleanField(default=True)
    history = models.JSONField(null=True)
    deck = models.JSONField()
    card_back = models.CharField(max_length=3, choices=CardBackTypes.choices, default='RD1')
    state = models.CharField(max_length=4, choices=StateTypes.choices, default='BET')


class Dealer(models.Model):
    table = models.OneToOneField(Table, on_delete=models.CASCADE)
    hand = models.JSONField()

# Profile Models
class Guest(models.Model):
    tables = models.ManyToManyField(Table)
    username = models.CharField(max_length=24, unique=True, default=generate_username())

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
        PLAYER = 'PLYR', 'Player'
        GUEST = 'GUES', 'Guest'

    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='hands')
    profile_type = models.CharField(max_length=4, choices=AccountTypes.choices)
    name = models.CharField(max_length=48)
    hand = models.JSONField()
    amount = models.PositiveIntegerField(default=2000)
