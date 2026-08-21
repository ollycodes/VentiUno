from django.contrib import admin
from .models import LeaderboardEntry


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ('name', 'score', 'biggest_bet', 'created_at')
    ordering = ('-score',)
