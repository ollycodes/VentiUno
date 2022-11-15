from django.forms import ModelForm
from .models import *

class TableForm(ModelForm):
    class Meta:
        model = Table
        fields = ["player_name"]
