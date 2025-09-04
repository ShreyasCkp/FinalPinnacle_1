


from django import forms
from .models import Leave

class LeaveForm(forms.ModelForm):
    """Form for applying or approving employee leave."""

    class Meta:
        model = Leave
        fields = ['leave_type', 'reason', 'start_date', 'end_date']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    # Optional: show calculated fields as readonly
    leave_days = forms.IntegerField(
        label="Total Leave Days",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    next_working_day = forms.DateField(
        label="Next Working Day",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'readonly': 'readonly'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate readonly fields if instance exists
        if self.instance:
            self.fields['leave_days'].initial = self.instance.leave_days
            self.fields['next_working_day'].initial = self.instance.next_working_day








from django import forms
from .models import EmployeeSalaryDeclaration

class EmployeeSalaryDeclarationForm(forms.ModelForm):
    class Meta:
        model = EmployeeSalaryDeclaration
        fields = [
            'employee',
            'basic_salary',
            'special_allowance',
            'professional_tax',
            'lwf_contribution',
            'income_tax',
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control', 'id': 'id_employee'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_basic_salary'}),
            'special_allowance': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_special_allowance'}),
            'professional_tax': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_professional_tax'}),
            'lwf_contribution': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_lwf_contribution'}),
            'income_tax': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_income_tax'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🔹 If editing, pre-fill employee details from DB
        if self.instance and self.instance.pk:
            emp = self.instance.employee
            self.emp_code = emp.emp_code
            self.emp_name = emp.name
            self.designation = emp.designation
            self.employment_type = emp.employment_type
            self.category = emp.category
            self.role = emp.role
