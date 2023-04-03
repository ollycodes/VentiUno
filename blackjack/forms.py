from django import forms
from .models import Guest, Player
from django.contrib.auth.forms import UserCreationForm

class GuestForm(forms.ModelForm):
    class Meta:
        model = Guest
        fields = ["name"]

class RegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'placeholder': self.fields[field_name].label})

class BetForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ["bet"]

    def __init__(self, *args, **kwargs):
        super(BetForm, self).__init__(*args, **kwargs)
        max_bet = self.instance.coins
        self.fields['bet'] = forms.IntegerField(
            min_value=100, 
            max_value=max_bet, 
            widget=forms.NumberInput(attrs={'step': '100', 'onfocus': 'this.blur()'}))

    # might be nice on mobile?
    # def __init__(self, *args, **kwargs):
    #     super(BetForm, self).__init__(*args, **kwargs)
    #     max_bet = self.instance.coins
    #     choices = [(i, i) for i in range(100, max_bet+1, 100)]
    #     self.fields['bet'] = forms.ChoiceField(choices=choices)
