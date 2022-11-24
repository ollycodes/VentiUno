from django.db import models

class Table(models.Model):
    player_name = models.CharField(max_length=24)
    game = models.JSONField()

    # deck = models.JSONField()
    # player_hand = models.JSONField()
    # dealer_hand = models.JSONField()
    # action = models.PositiveSmallIntegerField(default=0)
    # coin = models.PositiveIntegerField(default=1000)
