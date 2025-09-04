# forms.py
from django import forms

class LicenseForm(forms.Form):
    license_key = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Enter License Key'}))
    # agree_to_terms = forms.BooleanField(required=True)


