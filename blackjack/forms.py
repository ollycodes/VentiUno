from django import forms
from django.forms import widgets
from .models import Guest, Player
from django.contrib.auth.forms import UserCreationForm
from .logics.gen import generate_username

class GuestForm(forms.ModelForm):
    class Meta:
        model = Guest
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholder = generate_username()
        self.fields["name"].widget.attrs.update({'placeholder': placeholder})

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
            initial=self.fields['bet'].initial,
            min_value=1, 
            max_value=max_bet, 
            widget=forms.NumberInput(attrs={'onmousedown': 'coinVisibility()'})
        )
        self.coin_list = [1, 5, 25, 50, 100, 500, 1000]
