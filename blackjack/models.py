from django.db import models


class LeaderboardEntry(models.Model):
    name = models.CharField(max_length=24)
    score = models.PositiveIntegerField()
    biggest_bet = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score']

    def __str__(self):
        return f'{self.name}: {self.score}'
