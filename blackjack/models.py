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
    last_played = models.TimeField(auto_now_add=True, blank=True)

class Dealer(models.Model):
    table = models.OneToOneField(Table, on_delete=models.CASCADE, related_name='dealer')
    hand = models.JSONField()

class Player(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='players') 
    # where t = table object, t.player_hands.all() or t.player_hands.filter()
    hand = models.JSONField()

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ('guest', 'userproxy')},
    )
    object_id = models.PositiveIntegerField()
    player = GenericForeignKey('content_type', 'object_id')
    coins = models.PositiveIntegerField(default=2000)
    bet = models.PositiveIntegerField(default=0)
