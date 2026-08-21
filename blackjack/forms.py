from django import forms
from .models import LeaderboardEntry


class BetForm(forms.Form):
    coin_list = [1, 5, 25, 50, 100, 500, 1000]

    def __init__(self, *args, max_bet=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bet'] = forms.IntegerField(
            min_value=1,
            max_value=max_bet,
            widget=forms.NumberInput(attrs={'onmousedown': 'coinVisibility()'})
        )


class LeaderboardEntryForm(forms.ModelForm):
    class Meta:
        model = LeaderboardEntry
        fields = ['name']
