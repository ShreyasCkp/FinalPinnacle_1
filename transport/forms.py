
from django import forms
from .models import *

class MasterTransportForm(forms.ModelForm):
    class Meta:
        model = MasterTransport
        fields = '__all__'
        widgets = {
            'route_name': forms.TextInput(attrs={'placeholder': 'e.g. Hoskote Route'}),
        }

class TransportRouteForm(forms.ModelForm):
    class Meta:
        model = TransportRoute
        fields = '__all__'
        widgets = {
            'route_name': forms.TextInput(attrs={'placeholder': 'e.g. North Campus Route'}),
        }

class TransportStopForm(forms.ModelForm):
    class Meta:
        model = TransportStop
        fields = '__all__'
        widgets = {
            'pickup_time': forms.TimeInput(attrs={'type': 'time'}),
            'drop_time': forms.TimeInput(attrs={'type': 'time'}),
            'latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001'}),
        }

class StudentTransportMappingForm(forms.ModelForm):
    class Meta:
        model = StudentTransportMapping
        fields = '__all__'
        widgets = {
            'transport_fee': forms.NumberInput(attrs={'step': '0.01'}),
            'assigned_on': forms.DateInput(attrs={'type': 'date'}),
        }

class TransportFeeStructureForm(forms.ModelForm):
    class Meta:
        model = TransportFeeStructure
        fields = '__all__'
        widgets = {
            'monthly_fee': forms.NumberInput(attrs={'step': '0.01'}),
        }
