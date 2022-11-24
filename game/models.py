from django.db import models

class Table(models.Model):
    player_name = models.CharField(max_length=24)
    game_data = models.JSONField()
