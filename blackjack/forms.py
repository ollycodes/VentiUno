from django import forms
from .models import LeaderboardEntry


class LeaderboardEntryForm(forms.ModelForm):
    class Meta:
        model = LeaderboardEntry
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your name', 'autofocus': True}),
        }
