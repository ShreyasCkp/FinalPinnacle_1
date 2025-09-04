# forms.py
from django import forms



from django import forms
from .models import attendance, Employee
from django.core.exceptions import ValidationError
from datetime import date


from django import forms
from datetime import date
from .models import attendance, Employee

class AttendanceForm(forms.ModelForm):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.Select(attrs={
            'onchange': 'fetchEmployeeCode()',
            'id': 'id_employee',
        })
    )

    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'id': 'id_date'}),
        initial=date.today
    )

    check_in = forms.TimeField(
        widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'id': 'id_check_in'}),
        required=False,  # updated to optional
    )

    check_out = forms.TimeField(
        widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'id': 'id_check_out'}),
        required=False
    )

    status = forms.CharField(widget=forms.HiddenInput(), required=False)  # Hidden field

    # ✅ Loss of Pay checkbox
    lop = forms.BooleanField(
        required=False,
        label="Loss of Pay",
        widget=forms.CheckboxInput(attrs={'id': 'id_lop'})
    )

    class Meta:
        model = attendance
        fields = ['employee', 'date', 'check_in', 'check_out', 'status', 'lop']

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        selected_date = cleaned_data.get('date')

        if employee and selected_date:
            qs = attendance.objects.filter(employee=employee, date=selected_date)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                self.add_error(
                    None,
                    f"Attendance for {employee.name} has already been recorded on {selected_date}."
                )
        return cleaned_data


    class Meta:
        model = attendance
        fields = ['employee', 'date', 'check_in', 'check_out', 'status', 'lop']

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        selected_date = cleaned_data.get('date')

        if employee and selected_date:
            qs = attendance.objects.filter(employee=employee, date=selected_date)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                self.add_error(
                    None,
                    f"Attendance for {employee.name} has already been recorded on {selected_date}."
                )
        return cleaned_data









from django import forms
from .models import attendancesettings

class AttendanceSettingsForm(forms.ModelForm):
    class Meta:
        model = attendancesettings
        fields = ['check_in_time', 'grace_period', 'late_threshold']
        widgets = {
            'check_in_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class AttendanceSettingsForm(forms.ModelForm):
    class Meta:
        model = attendancesettings
        fields = ['check_in_time', 'grace_period', 'late_threshold']
        widgets = {
            'check_in_time': forms.TimeInput(attrs={'type': 'time'}),
        }



from django import forms
from .models import StudentAttendance
from django import forms
from .models import StudentAttendance
from master.models import Course, Subject, Employee, StudentDatabase
 
class StudentAttendanceForm(forms.ModelForm):
    class Meta:
        model = StudentAttendance
        fields = [
            'course',
            'semester_number',
            'subject',
            'faculty',
            'student',
            'attendance_date',
            'status',
            'remarks',
        ]
 
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'semester_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'faculty': forms.Select(attrs={'class': 'form-control'}),
            'student': forms.Select(attrs={'class': 'form-control'}),
            'attendance_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.RadioSelect(choices=StudentAttendance.STATUS_CHOICES),
            'remarks': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
        }
 
    def __init__(self, *args, **kwargs):
        super(StudentAttendanceForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False  # optional, depending on your form logic


