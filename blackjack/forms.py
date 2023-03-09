from django import forms
from .models import Guest, Table

class GuestForm(forms.ModelForm):
    class Meta:
        model = Guest
        fields = ["name"]

class TableNameForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ["name"]
