from django import forms
from .models import Guest
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
            # self.fields[field_name].label = False

# This code creates a custom registration form for a user in a Django web application. The form inherits from the `UserCreationForm` class provided by Django, which provides some basic fields for username and password. The `__init__` method of the `RegistrationForm` class is overridden to customize the form fields.
#
# First, the `super` function is called to run the `__init__` method of the parent class with the given arguments. This allows the form to inherit any necessary attributes and methods from the parent class.
#
# Next, a loop is executed over all fields in the form. For each field, the `widget.attrs` dictionary is updated to add two attributes: `class` for the CSS class name and `placeholder` for the field's label. These attributes are used to style the form fields and provide a placeholder text within the field.
#
# Finally, the label for each field is set to `False` to hide the labels in the form. This is done to provide a more streamlined and modern appearance for the registration form.
        #
        # {% for field in form %}
        #     {% if field.label_tag %}
        #         {% continue %}
        #     {% endif %}
        #     <input 
        #         class="form-input" 
        #         type="{{ field.widget.input_type }}" 
        #         name="{{ field.name }}" 
        #         placeholder="{{ field.label }}">
        # {% endfor %}
