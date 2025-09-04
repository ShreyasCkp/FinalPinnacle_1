from django import forms
from .models import FeeDeclaration, FeeDeclarationDetail
from django.forms.models import inlineformset_factory
from master.models import FeeType
from django.utils import timezone

class FeeDeclarationForm(forms.ModelForm):
    class Meta:
        model = FeeDeclaration
        fields = ['academic_year', 'course_type', 'course', 'semester', 'current_year']
        widgets = {
            'semester': forms.NumberInput(attrs={'placeholder': 'Optional'}),
            'current_year': forms.NumberInput(attrs={'placeholder': 'Optional'}),
        }
 

class FeeDeclarationDetailForm(forms.ModelForm):
    class Meta:
        model = FeeDeclarationDetail
        fields = ['fee_type', 'amount', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'min': timezone.now().date().isoformat()  # prevents past dates on frontend
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fee_type'].queryset = FeeType.objects.filter(is_optional=False)
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date

FeeDeclarationDetailFormSet = inlineformset_factory(
    FeeDeclaration,
    FeeDeclarationDetail,
    form=FeeDeclarationDetailForm,
    extra=1,
    can_delete=True
)

from django import forms
from .models import OptionalFee
from master.models import FeeType

class OptionalFeeForm(forms.ModelForm):
    class Meta:
        model = OptionalFee
        fields = ['fee_type', 'amount','due_date']
        widgets = {
            'fee_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
              'due_date': forms.DateInput(attrs={
                'type': 'date',
                'min': timezone.now().date().isoformat()  # prevents past dates on frontend
            })
        }

    def __init__(self, *args, **kwargs):
        academic_year = kwargs.pop('academic_year', None)
        super().__init__(*args, **kwargs)
        self.fields['fee_type'].queryset = FeeType.objects.filter(is_optional=True)

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date



from django import forms
from .models import StudentFeeCollection
from .models import StudentFeeCollection

class StudentFeeCollectionForm(forms.ModelForm):
    class Meta:
        model = StudentFeeCollection
        fields = [
            "admission_no",
            "fee_type",
            "amount",
            "paid_amount",
            "balance_amount",
            "applied_discount",
            "receipt_no",
            "receipt_date",
            "payment_mode",
            "payment_id",
            "payment_date",
            "status",
        ]
        widgets = {
            "admission_no": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "fee_type": forms.Select(attrs={"class": "form-select", "readonly": True}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
            "paid_amount": forms.NumberInput(attrs={"class": "form-control"}),
            "balance_amount": forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
           
            "payment_mode": forms.Select(
                attrs={"class": "form-select"},
                choices=[
                    ("Cash", "Cash"),
                    
                    

                     ("Online", "Online"),
                    ("Bank Transfer", "Bank Transfer"),
                ]
            ),
            "payment_id": forms.TextInput(attrs={"class": "form-control"}),
            "payment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(
                attrs={"class": "form-select"},
                choices=[
                    ("Pending", "Pending"),
                    ("Partial", "Partial"),
                    ("Paid", "Paid"),
                ]
            ),
        }

    def clean_paid_amount(self):
        paid_amount = self.cleaned_data.get("paid_amount")
        amount = self.cleaned_data.get("amount")
        if paid_amount and amount and paid_amount > amount:
            raise forms.ValidationError("Paid amount cannot be greater than total amount.")
        return paid_amount

    def clean(self):
        cleaned_data = super().clean()
        paid_amount = cleaned_data.get("paid_amount") or 0
        
        amount = cleaned_data.get("amount") or 0

        total_paid = paid_amount + discount
        balance_amount = max(amount - total_paid, 0)
        cleaned_data["balance_amount"] = balance_amount

        if balance_amount == 0:
            cleaned_data["status"] = "Paid"
        elif paid_amount > 0:
            cleaned_data["status"] = "Partial"
        else:
            cleaned_data["status"] = "Pending"

        return cleaned_data

