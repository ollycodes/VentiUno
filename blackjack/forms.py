from django import forms
from django.contrib.auth.models import User
from .models import *

class GuestForm(forms.ModelForm):
    class Meta:
        model = GuestTable
        fields = ["username"]

class UserUpdateForm(forms.ModelForm):
	email = forms.EmailField()

	class Meta:
		model = User
		fields = ['username', 'email']
