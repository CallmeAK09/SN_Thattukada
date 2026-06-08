from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Item

def validate_letters_only(value):
    if not re.match(r'^[a-zA-Z\s\(\)_]+$', value):
        raise ValidationError("Item name must contain only alphabets, spaces, underscores, and parentheses.")
    if not value.strip():
        raise ValidationError("Item name cannot consist of spaces only.")

class ItemForm(forms.ModelForm):
    name = forms.CharField(
        validators=[validate_letters_only],
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter item name (e.g., Idli, Dosa)',
            'class': 'form-input'
        })
    )
    price = forms.DecimalField(
        min_value=0.00,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Enter price (e.g., 10.00)',
            'class': 'form-input',
            'step': '0.01'
        })
    )

    class Meta:
        model = Item
        fields = ['name', 'price']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            # Strip trailing/leading spaces and format nicely (title case)
            name = ' '.join(name.split())
        return name
