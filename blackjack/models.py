from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from .logics.gen import generate_username

# Profile Models
class Guest(models.Model):
    name = models.CharField(max_length=24, unique=True, default=generate_username())

class UserProxy(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    @property
    def name(self):
        return self.user.username

class Table(models.Model):
    deck = models.JSONField()
    history = models.JSONField(null=True)
    is_open = models.BooleanField(default=True)
    name = models.CharField(max_length=24, blank=True)
    last_played = models.TimeField(auto_now_add=True, blank=True)

class Player(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='hands')
    hand = models.JSONField()
    amount = models.PositiveIntegerField(default=2000)

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ('guest', 'userproxy')},
    )
    object_id = models.PositiveIntegerField()
    player = GenericForeignKey('content_type', 'object_id')



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
    
    card_back = models.CharField(max_length=3, choices=CardBackTypes.choices, default='RD1')
    state = models.CharField(max_length=4, choices=StateTypes.choices, default='BET')

class Dealer(models.Model):
    table = models.OneToOneField(Table, on_delete=models.CASCADE)
    hand = models.JSONField()
