from django.db import models
from django.shortcuts import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Guest(models.Model):
    name = models.CharField(max_length=24, unique=True)

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
    biggest_bet = models.PositiveBigIntegerField(default=0)
    high_score = models.PositiveIntegerField(default=0)

class HighScores(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ('guest', 'userproxy')},
    )
    object_id = models.PositiveIntegerField()
    player = GenericForeignKey('content_type', 'object_id')

    table_id = models.PositiveIntegerField()
    biggest_bet = models.PositiveBigIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('content_type', 'object_id', 'table_id')
