from django.db import models
from . import table_logics

class Table(models.Model):
    player_name = models.CharField(
        max_length=24,
        unique=True,
        default= table_logics.generate_username())
    game_data = models.JSONField()
