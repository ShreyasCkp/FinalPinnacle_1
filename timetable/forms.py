
from django import forms
from .models import  TimeSlot, TimetableEntry

class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['start_time', 'end_time']


# class TimetableEntryForm(forms.ModelForm):
#     class Meta:
#         model = TimetableEntry
#         fields = ['day', 'time_slot', 'semester', 'subject', 'faculty', 'room']


from django import forms
from .models import TimetableEntry
from master.models import Employee
from django.core.exceptions import ValidationError




class TimetableEntryForm(forms.ModelForm):
    semester_number = forms.ChoiceField(
        choices=[('', 'Select Combination First')],
        required=True,
        label="Sem/Year",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_semester_number'})
    )

    class Meta:
        model = TimetableEntry
        fields = [
            'day',
            'time_slot',
            'course_type',
            'academic_year',
            'course',
            'semester_number',
            'subject',
            'faculty',
            'room'
        ]
        widgets = {
            'day': forms.Select(attrs={'class': 'form-select'}),
            'time_slot': forms.Select(attrs={'class': 'form-select'}),
            'course_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_course_type'}),
            'academic_year': forms.Select(attrs={'class': 'form-select', 'id': 'id_academic_year'}),
            'course': forms.Select(attrs={'class': 'form-select', 'id': 'id_course'}),
            'subject': forms.Select(attrs={'class': 'form-select', 'id': 'id_subject'}),
            'faculty': forms.Select(attrs={'class': 'form-select', 'id': 'id_faculty'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'day': 'Day',
            'time_slot': 'Time Slot',
            'course_type': 'Program Type',
            'academic_year': 'Batch',
            'course': 'Combination',
            'semester_number': 'Sem/Year',
            'subject': 'Subject',
            'faculty': 'Faculty',
            'room': 'Room',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['faculty'].queryset = Employee.objects.all()

        if 'course' in self.data and 'semester_number' in self.data and 'subject' in self.data:
            try:
                course_id = int(self.data.get('course'))
                semester_number = int(self.data.get('semester_number'))
                subject_id = int(self.data.get('subject'))

                assigned_employees = Employee.objects.filter(
                    subject_assignments__course_id=course_id,
                    subject_assignments__semester=semester_number,
                    subject_assignments__subject_id=subject_id
                ).distinct()

                self.fields['faculty'].queryset = assigned_employees

                if assigned_employees.exists():
                    self.initial['faculty'] = assigned_employees.first().id

            except (ValueError, TypeError):
                pass

        elif self.instance.pk:
            self.fields['faculty'].queryset = Employee.objects.filter(
                subject_assignments__course=self.instance.course,
                subject_assignments__semester=self.instance.semester_number,
                subject_assignments__subject=self.instance.subject
            ).distinct()

    
from django import forms
from .models import  TimeSlot, TimetableEntry

class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['start_time', 'end_time']


# class TimetableEntryForm(forms.ModelForm):
#     class Meta:
#         model = TimetableEntry
#         fields = ['day', 'time_slot', 'semester', 'subject', 'faculty', 'room']


from django import forms
from .models import TimetableEntry
from master.models import Employee
from django.core.exceptions import ValidationError




class TimetableEntryForm(forms.ModelForm):
    semester_number = forms.ChoiceField(
        choices=[('', 'Select Combination First')],
        required=True,
        label="Sem/Year",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_semester_number'})
    )

    class Meta:
        model = TimetableEntry
        fields = [
            'day',
            'time_slot',
            'course_type',
            'academic_year',
            'course',
            'semester_number',
            'subject',
            'faculty',
            'room'
        ]
        widgets = {
            'day': forms.Select(attrs={'class': 'form-select'}),
            'time_slot': forms.Select(attrs={'class': 'form-select'}),
            'course_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_course_type'}),
            'academic_year': forms.Select(attrs={'class': 'form-select', 'id': 'id_academic_year'}),
            'course': forms.Select(attrs={'class': 'form-select', 'id': 'id_course'}),
            'subject': forms.Select(attrs={'class': 'form-select', 'id': 'id_subject'}),
            'faculty': forms.Select(attrs={'class': 'form-select', 'id': 'id_faculty'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'day': 'Day',
            'time_slot': 'Time Slot',
            'course_type': 'Program Type',
            'academic_year': 'Batch',
            'course': 'Combination',
            'semester_number': 'Sem/Year',
            'subject': 'Subject',
            'faculty': 'Faculty',
            'room': 'Room',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initially empty or full list (based on use case)
        self.fields['faculty'].queryset = Employee.objects.all()

        # Check if data is passed via POST (or GET via AJAX)
        data = self.data or None

        if data and all(key in data for key in ['course', 'semester_number', 'subject']):
            try:
                course_id = int(data.get('course'))
                semester_number = int(data.get('semester_number'))
                subject_id = int(data.get('subject'))

                # Filter employees based on subject assignments
                assigned_employees = Employee.objects.filter(
                    subject_assignments__course_id=course_id,
                    subject_assignments__semester=semester_number,
                    subject_assignments__subject_id=subject_id
                ).distinct()

                self.fields['faculty'].queryset = assigned_employees

                if assigned_employees.exists():
                    self.initial['faculty'] = assigned_employees.first().id

            except (ValueError, TypeError):
                pass  # ignore invalid form input

        elif self.instance and self.instance.pk:
            # Editing an existing instance
            self.fields['faculty'].queryset = Employee.objects.filter(
                subject_assignments__course=self.instance.course,
                subject_assignments__semester=self.instance.semester_number,
                subject_assignments__subject=self.instance.subject
            ).distinct()

            # Pre-fill current faculty
            self.initial['faculty'] = self.instance.faculty_id

    def clean(self):
        cleaned_data = super().clean()
        day = cleaned_data.get('day')
        time_slot = cleaned_data.get('time_slot')
        faculty = cleaned_data.get('faculty')

        if day and time_slot and faculty:
            # Conflict: same faculty, same time and day, regardless of course or semester
            conflict_qs = TimetableEntry.objects.filter(
                day=day,
                time_slot=time_slot,
                faculty=faculty
            )

            if self.instance.pk:
                conflict_qs = conflict_qs.exclude(pk=self.instance.pk)

            if conflict_qs.exists():
                entry = conflict_qs.first()  # Get one matching entry
                error_message = (
                    f"This faculty is already assigned to "
                    f"{entry.course} -  {entry.course} {entry.semester_number} - {entry.subject} "
                    f"on {entry.day} during {entry.time_slot}."
                )
                self.add_error(None, error_message)

        return cleaned_data



