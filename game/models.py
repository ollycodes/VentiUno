from django.db import models

class Table(models.Model):
    player_name = models.CharField(max_length=24)
    deck = models.JSONField()
    player_hand = models.JSONField()
    dealer_hand = models.JSONField()
    is_finished = models.BooleanField(default=False)
    coin = models.PositiveIntegerField(default=1000)
