import re
from django import forms
from django.core.exceptions import ValidationError
from .models import PUAdmission, CourseType, Course
from master.models import Transport
from django.db.models import Q
from transport.models import MasterTransport
class PUAdmissionForm(forms.ModelForm):
    education_boards = forms.ChoiceField(choices=PUAdmission.BOARD_CHOICES,widget=forms.Select,required=False)

    admission_source = forms.ChoiceField(
     choices=PUAdmission._meta.get_field('admission_source').choices,
     required=False,
     widget=forms.Select(attrs={'class': 'form-select'})
 )


    class Meta:
        model = PUAdmission
        exclude = [ 'status', 'final_fee_after_advance']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
            'student_declaration_date': forms.DateInput(attrs={'type': 'date'}),
            'parent_declaration_date': forms.DateInput(attrs={'type': 'date'}),
            'blood_group': forms.Select(choices=PUAdmission.BLOOD_GROUP_CHOICES),
            'permanent_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'current_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'student_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'caste': forms.Select(attrs={'class': 'form-select'}),
            'document_submitted': forms.CheckboxInput(),
            'hostel_required': forms.CheckboxInput(),
            'wants_transport': forms.CheckboxInput(),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'course_type': forms.Select(attrs={'class': 'form-select'}),
            'admitted_to': forms.Select(attrs={'class': 'form-select'}),
            'transport': forms.Select(attrs={'class': 'form-select'}),
            'father_mobile_no': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_phone_no': forms.TextInput(attrs={'class': 'form-control'}),
            'student_phone_no': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'birthplace': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'register_no_course': forms.TextInput(attrs={'class': 'form-control'}),
            'month_year_passed': forms.TextInput(attrs={'class': 'form-control'}),
            'subject1': forms.TextInput(attrs={'class': 'form-control'}),
            'marks_obtained1': forms.TextInput(attrs={'class': 'form-control'}),
            'total_marks_percentage1': forms.TextInput(attrs={'class': 'form-control'}),
            'subject2': forms.TextInput(attrs={'class': 'form-control'}),
            'marks_obtained2': forms.TextInput(attrs={'class': 'form-control'}),
            'total_marks_percentage2': forms.TextInput(attrs={'class': 'form-control'}),
            'subject3': forms.TextInput(attrs={'class': 'form-control'}),
            'marks_obtained3': forms.TextInput(attrs={'class': 'form-control'}),
            'total_marks_percentage3': forms.TextInput(attrs={'class': 'form-control'}),
            'subject4': forms.TextInput(attrs={'class': 'form-control'}),
            'marks_obtained4': forms.TextInput(attrs={'class': 'form-control'}),
            'total_marks_percentage4': forms.TextInput(attrs={'class': 'form-control'}),
            'subject5': forms.TextInput(attrs={'class': 'form-control'}),
            'marks_obtained5': forms.TextInput(attrs={'class': 'form-control'}),
            'total_marks_percentage5': forms.TextInput(attrs={'class': 'form-control'}),
            'subject6': forms.TextInput(attrs={'class': 'form-control'}),
            'marks_obtained6': forms.TextInput(attrs={'class': 'form-control'}),
            'total_marks_percentage6': forms.TextInput(attrs={'class': 'form-control'}),
            'max_marks1': forms.TextInput(attrs={'class': 'form-control'}),
            'max_marks2': forms.TextInput(attrs={'class': 'form-control'}),
            'max_marks3': forms.TextInput(attrs={'class': 'form-control'}),
            'max_marks4': forms.TextInput(attrs={'class': 'form-control'}),
            'max_marks5': forms.TextInput(attrs={'class': 'form-control'}),
            'max_marks6': forms.TextInput(attrs={'class': 'form-control'}),
            'total_marks_obtained': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_max_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'overall_percentage': forms.TextInput(attrs={'class': 'form-control'}),
            'co_curricular_activities': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'application_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'tuition_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'books_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'uniform_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'tuition_advance_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'hostel_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'transport_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'scholarship_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'final_fee_after_advance': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_mode': forms.Select(attrs={'class': 'form-select'}),
            'receipt_no': forms.TextInput(attrs={'class': 'form-control'}),
            'receipt_date': forms.DateInput(attrs={'type': 'date'}),
            'utr_no': forms.TextInput(attrs={'class': 'form-control'}),
            'school_name_laststudied': forms.TextInput(attrs={'class': 'form-control'}),
            'school_addresslaststudied': forms.TextInput(attrs={'class': 'form-control'}),
            'sats_number': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_address': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control'}),
            'annual_income': forms.NumberInput(attrs={'class': 'form-control'}),
            'mother_annual_income': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_annual_income': forms.NumberInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'mother_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'student_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'father_occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'aadhar_no': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_aadhar_no': forms.TextInput(attrs={'class': 'form-control'}),
            'student_aadhar_no': forms.TextInput(attrs={'class': 'form-control'}),
            'sub_caste': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'religion': forms.TextInput(attrs={'class': 'form-control'}),
            'medium_of_instruction': forms.TextInput(attrs={'class': 'form-control'}),
            'converstion_fee': forms.TextInput(attrs={'class': 'form-control'}),
            'enquiry_no': forms.TextInput(attrs={'class': 'form-control'}),
            'student_name': forms.TextInput(attrs={'class': 'form-control capitalize-on-input'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control capitalize-on-input'}),
            'medium': forms.TextInput(attrs={'class': 'form-control'}),
            'second_language': forms.TextInput(attrs={'class': 'form-control'}),
            'first_language': forms.TextInput(attrs={'class': 'form-control'}),
            # 'academic_year': forms.Select(attrs={'class': 'form-select'}),

        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Show all Course Types
        self.fields['course_type'].queryset = CourseType.objects.all()

        # Set default course_type if not provided
        default_course_type = CourseType.objects.filter(
            Q(name__icontains="School of Commerce") |
            Q(name__icontains="Commerce") |
            Q(name__icontains="BCom")
        ).first()

        if (
            default_course_type
            and not self.data
            and not self.initial.get('course_type')
            and not (self.instance.pk and self.instance.course_type)
        ):
            self.fields['course_type'].initial = default_course_type

        # Filter Courses based on form input or instance/initial values
        if 'course_type' in self.data:
            try:
                course_type_id = int(self.data.get('course_type'))
                filtered_courses = Course.objects.filter(course_type_id=course_type_id).order_by('name')
            except (ValueError, TypeError):
                filtered_courses = Course.objects.none()
        elif self.initial.get('course_type'):
            course_type_id = self.initial.get('course_type')
            filtered_courses = Course.objects.filter(course_type_id=course_type_id).order_by('name')
        elif self.instance.pk and self.instance.course_type:
            filtered_courses = Course.objects.filter(course_type=self.instance.course_type).order_by('name')
        elif default_course_type:
            filtered_courses = Course.objects.filter(course_type=default_course_type).order_by('name')
        else:
            filtered_courses = Course.objects.none()

        # Set filtered course queryset
        self.fields['course'].queryset = filtered_courses

        # Set admitted_to queryset based on course_type (same filtering as 'course')
        if 'admitted_to' in self.fields:
            self.fields['admitted_to'].queryset = filtered_courses

        # Set transport queryset
        self.fields['transport'].queryset = MasterTransport.objects.all()


        required_fields = [
            'mother_name', 'father_name', 'student_phone_no', 
            'current_address', 'category', 'caste', 'payment_mode','student_declaration_date','student_declaration_place'
        ]
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True


        # Add form-control and capitalize-on-input class to specific fields
        fields_to_capitalize = [
            'student_name', 'father_name', 'religion',
            'nationality', 'permanent_address', 'current_address'
        ]
        for field in fields_to_capitalize:
            if field in self.fields:
                self.fields[field].widget.attrs.update({'class': 'form-control capitalize-on-input'})


    def clean_student_name(self):
        name = self.cleaned_data.get('student_name', '')
        name = name.upper()

        if not re.match(r'^[A-Z ]+$', name):
            raise ValidationError("Name must contain only capital letters and spaces. Numbers and lowercase letters are not allowed.")

        return name



   

from django import forms
from .models import DegreeAdmission
from master.models import CourseType, Course
from django.core.exceptions import ValidationError
from django.db.models import Q
from django import forms
from .models import DegreeAdmission  # Make sure this import is corr
from transport.models import MasterTransport
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import DegreeAdmission, CourseType, Course

class DegreeAdmissionForm(forms.ModelForm):
    education_boards = forms.ChoiceField(
        choices=DegreeAdmission.BOARD_CHOICES,
        widget=forms.Select,
        required=False
    )

    admission_source = forms.ChoiceField(
        choices=DegreeAdmission._meta.get_field('admission_source').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = DegreeAdmission
        exclude = ['status', 'final_fee_after_advance']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
            'student_declaration_date': forms.DateInput(attrs={'type': 'date'}),
            'parent_declaration_date': forms.DateInput(attrs={'type': 'date'}),
            'receipt_date': forms.DateInput(attrs={'type': 'date'}),
            'transport': forms.Select(),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'caste': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(),
            'blood_group': forms.Select(),
            'quota_type': forms.Select(),
            'payment_mode': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'permanent_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'current_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'co_curricular_activities': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'student_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(DegreeAdmissionForm, self).__init__(*args, **kwargs)

        # Set required for selected fields
        required_fields = [
            'father_name', 'mother_name', 'student_phone_no',
            'permanent_address', 'category', 'caste', 'payment_mode','student_declaration_date','student_declaration_place'
        ]
        for field in required_fields:
            if field in self.fields:
                self.fields[field].required = True

        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.FileInput, forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                css_class = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f'{css_class} form-control'.strip()

        # Populate transport
        self.fields['transport'].queryset = MasterTransport.objects.all()

        # Capitalize input fields
        capitalize_fields = [
            'student_name', 'father_name', 'mother_name', 'religion',
            'nationality', 'permanent_address', 'current_address',
        ]
        for field in capitalize_fields:
            if field in self.fields:
                old_class = self.fields[field].widget.attrs.get('class', '')
                self.fields[field].widget.attrs['class'] = f'{old_class} capitalize-on-input'.strip()

        # Set default course_type
        default_course_type = CourseType.objects.filter(
            Q(name__icontains="Commerce") |
            Q(name__icontains="School of Commerce") |
            Q(name__icontains="BCom")
        ).first()

        if (
            default_course_type and
            not self.data and
            not self.initial.get('course_type') and
            not (self.instance.pk and self.instance.course_type)
        ):
            self.fields['course_type'].initial = default_course_type

        # Determine course_type_id
        course_type_id = None
        if 'course_type' in self.data:
            try:
                course_type_id = int(self.data.get('course_type'))
            except (ValueError, TypeError):
                pass
        elif self.initial.get('course_type'):
            course_type_id = self.initial.get('course_type')
        elif self.instance.pk and self.instance.course_type:
            course_type_id = self.instance.course_type.id
        elif default_course_type:
            course_type_id = default_course_type.id

        # Filter course and admitted_to
        if course_type_id:
            filtered_courses = Course.objects.filter(course_type_id=course_type_id).order_by('name')
            self.fields['course'].queryset = filtered_courses
            self.fields['admitted_to'].queryset = filtered_courses
        else:
            self.fields['course'].queryset = Course.objects.none()
            self.fields['admitted_to'].queryset = Course.objects.none()

        # Phone validations
        phone_fields = ['father_mobile_no', 'student_phone_no', 'emergency_contact']
        for field_name in phone_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'pattern': r'^[0-9]{10}$',
                    'maxlength': '10',
                    'title': 'Enter a valid 10-digit phone number',
                })

    # Clean methods
    def _validate_phone_number(self, field_name):
        phone = self.cleaned_data.get(field_name)
        if phone:
            phone_str = str(phone).strip()
            if not phone_str.isdigit() or len(phone_str) != 10:
                raise ValidationError("Please enter a valid 10-digit phone number.")
            return phone_str
        return phone

    def clean_father_mobile_no(self):
        return self._validate_phone_number('father_mobile_no')

    def clean_student_phone_no(self):
        return self._validate_phone_number('student_phone_no')

    def clean_emergency_contact(self):
        return self._validate_phone_number('emergency_contact')

    def clean_father_name(self):
        father_name = self.cleaned_data.get('father_name')
        if not father_name:
            raise ValidationError("Father name is required.")
        return father_name

    def clean_mother_name(self):
        mother_name = self.cleaned_data.get('mother_name')
        if not mother_name:
            raise ValidationError("Mother name is required.")
        return mother_name





from .models import Enquiry1, Course, CourseType,AcademicYear
from django.utils import timezone

class Enquiry1Form(forms.ModelForm):
    enquiry_date = forms.DateField(
        label="Enquiry Date",
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
 
    class Meta:
        model = Enquiry1
        fields = [
            'enquiry_no', 'student_name', 'gender', 'parent_relation', 'parent_name', 'parent_phone',
            'permanent_address', 'current_address', 'city', 'pincode', 'state',
            'course_type', 'course', 'percentage_10th', 'percentage_12th', 'guardian_relation',
            'email', 'source', 'other_source', 'enquiry_date',
        ]
        widgets = {
            'source': forms.Select(attrs={'onchange': 'toggleOtherSource(this)'}),
            'permanent_address': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
            'current_address': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }
        labels = {
            'parent_relation': 'Relation',
        }
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
 
        self.fields['enquiry_no'].widget.attrs['readonly'] = True
 
        # Filter course types that start with 'puc'
        course_type_qs = CourseType.objects.filter(name__istartswith='puc')
        self.fields['course_type'].queryset = course_type_qs
 
        # Use first matching course type as default fallback
        default_course_type = course_type_qs.first() if course_type_qs.exists() else None
 
        if 'course_type' in self.data:
            try:
                selected_id = int(self.data.get('course_type'))
                self.fields['course'].queryset = Course.objects.filter(course_type_id=selected_id).order_by('name')
            except (ValueError, TypeError):
                self.fields['course'].queryset = Course.objects.none()
        elif self.instance.pk and self.instance.course_type_id:
            try:
                self.fields['course'].queryset = Course.objects.filter(
                    course_type_id=self.instance.course_type_id
                ).order_by('name')
            except CourseType.DoesNotExist:
                self.fields['course'].queryset = Course.objects.none()
        elif default_course_type:
            self.fields['course'].queryset = Course.objects.filter(course_type=default_course_type).order_by('name')
        else:
            self.fields['course'].queryset = Course.objects.none()
 
 
 
from django import forms
from django.utils import timezone
from django.db.models import Q
from .models import Enquiry2
from master.models import CourseType, Course  # Adjust if models are in different app
 
class Enquiry2Form(forms.ModelForm):
    enquiry_date = forms.DateField(
        label="Enquiry Date",
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
 
    class Meta:
        model = Enquiry2
        fields = [
            'enquiry_no', 'student_name', 'gender', 'parent_relation', 'parent_name', 'parent_phone',
            'permanent_address', 'current_address', 'city', 'pincode', 'state',
            'course_type', 'course', 'percentage_10th', 'percentage_12th', 'guardian_relation',
            'email', 'source', 'other_source', 'enquiry_date', 
        ]
        widgets = {
            'source': forms.Select(attrs={'onchange': 'toggleOtherSource(this)'}),
            'permanent_address': forms.Textarea(attrs={'rows': 2}),
            'current_address': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'parent_relation': 'Relation',
        }
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
 
        # Filter course types
        course_type_qs = CourseType.objects.filter(
            Q(name__istartswith='school of commerce') | Q(name__istartswith='bcom regular')
        )
        self.fields['course_type'].queryset = course_type_qs
 
        # Default to first available course_type in filtered list
        default_course_type = course_type_qs.first() if course_type_qs.exists() else None
 
        if 'course_type' in self.data:
            try:
                selected_id = int(self.data.get('course_type'))
                self.fields['course'].queryset = Course.objects.filter(course_type_id=selected_id).order_by('name')
            except (ValueError, TypeError):
                self.fields['course'].queryset = Course.objects.none()
        elif self.instance.pk and self.instance.course_type_id:
            try:
                self.fields['course'].queryset = Course.objects.filter(
                    course_type_id=self.instance.course_type_id
                ).order_by('name')
            except CourseType.DoesNotExist:
                self.fields['course'].queryset = Course.objects.none()
        elif default_course_type:
            self.fields['course'].queryset = Course.objects.filter(course_type=default_course_type).order_by('name')
        else:
            self.fields['course'].queryset = Course.objects.none()
 


from django import forms
from .models import FollowUp, Enquiry1, Enquiry2


class FollowUpForm(forms.ModelForm):
    combined_enquiry = forms.ChoiceField(
        label='Enquiry',
        choices=[],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    student_name_display = forms.CharField(
        label='Student Name',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    class Meta:
        model = FollowUp
        exclude = ['status', 'pu_enquiry', 'degree_enquiry']
        widgets = {
            'follow_up_type': forms.Select(
                choices=[('Call', 'Call'), ('Email', 'Email'), ('Visit', 'Visit')],
                attrs={'class': 'form-control'}
            ),
            'follow_up_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'min': timezone.now().strftime('%Y-%m-%dT%H:%M')
            }),
            'priority': forms.Select(
                choices=[('', 'Select priority'), ('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')],
                attrs={'class': 'form-control'}
            ),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Add notes about the follow-up',
                'style': 'height: 57px;'
            }),
            'next_action_required': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Send brochure, Schedule campus visit'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically set enquiry choices
        pu_converted = PUAdmission.objects.exclude(enquiry_no__isnull=True).exclude(enquiry_no='').values_list('enquiry_no', flat=True)
        deg_converted = DegreeAdmission.objects.exclude(enquiry_no__isnull=True).exclude(enquiry_no='').values_list('enquiry_no', flat=True)

        pu_enquiries = Enquiry1.objects.exclude(enquiry_no__in=pu_converted)
        deg_enquiries = Enquiry2.objects.exclude(enquiry_no__in=deg_converted)

        pu_choices = [('pu_' + str(e.id), e.enquiry_no) for e in pu_enquiries]
        deg_choices = [('deg_' + str(e.id), e.enquiry_no) for e in deg_enquiries]

        self.fields['combined_enquiry'].choices = pu_choices + deg_choices

        if self.instance and self.instance.pk:
# Editing mode: disable field
          self.fields['combined_enquiry'].disabled = True

        # Set initial values when editing
        if self.instance and (self.instance.pu_enquiry or self.instance.degree_enquiry):
            if self.instance.pu_enquiry:
                self.fields['combined_enquiry'].initial = 'pu_' + str(self.instance.pu_enquiry.id)
                self.fields['student_name_display'].initial = f"{self.instance.pu_enquiry.enquiry_no} - {self.instance.pu_enquiry.student_name}"
            elif self.instance.degree_enquiry:
                self.fields['combined_enquiry'].initial = 'deg_' + str(self.instance.degree_enquiry.id)
                self.fields['student_name_display'].initial = f"{self.instance.degree_enquiry.enquiry_no} - {self.instance.degree_enquiry.student_name}"

    def clean(self):
        cleaned_data = super().clean()
        combined_value = cleaned_data.get('combined_enquiry')

        if not combined_value:
            self.add_error('combined_enquiry', 'This field is required.')
            return cleaned_data

        try:
            prefix, obj_id = combined_value.split('_')
            cleaned_data['enquiry_type'] = prefix
            cleaned_data['enquiry_id'] = int(obj_id)
        except ValueError:
            self.add_error('combined_enquiry', 'Invalid enquiry format.')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        enquiry_type = self.cleaned_data.get('enquiry_type')
        enquiry_id = self.cleaned_data.get('enquiry_id')

        if enquiry_type == 'pu':
            instance.pu_enquiry = Enquiry1.objects.get(id=enquiry_id)
            instance.degree_enquiry = None
        elif enquiry_type == 'deg':
            instance.degree_enquiry = Enquiry2.objects.get(id=enquiry_id)
            instance.pu_enquiry = None

        if commit:
            instance.save()
        return instance



from django import forms
from .models import PUFeeDetail, DegreeFeeDetail

class PUFeeDetailForm(forms.ModelForm):
    class Meta:
        model = PUFeeDetail
        fields = [
            'tuition_fee',
            'scholarship',
            'tuition_advance_amount',
            'transport_fee',
            'hostel_fee',
            'books_fee',
            'uniform_fee',
            'payment_mode',
            'final_fee_after_advance',
        ]


    def clean(self):
        cleaned_data = super().clean()
        hostel_fee = cleaned_data.get('hostel_fee') or 0
        transport_fee = cleaned_data.get('transport_fee') or 0

        if hostel_fee > 0:
            cleaned_data['transport_fee'] = 0
        elif transport_fee > 0:
            cleaned_data['hostel_fee'] = 0

        return cleaned_data

class DegreeFeeDetailForm(forms.ModelForm):
    class Meta:
        model = DegreeFeeDetail
        fields = [
            'tuition_fee',
            'scholarship',
            'tuition_advance_amount',
            'transport_fee',
            'hostel_fee',
            'books_fee',
            'uniform_fee',
            'payment_mode',
            'final_fee_after_advance',

        ]

    def clean(self):
        cleaned_data = super().clean()
        hostel_fee = cleaned_data.get('hostel_fee') or 0
        transport_fee = cleaned_data.get('transport_fee') or 0

        # Enforce: if hostel_fee is entered, transport_fee = 0 and vice versa
        if hostel_fee > 0:
            cleaned_data['transport_fee'] = 0
        elif transport_fee > 0:
            cleaned_data['hostel_fee'] = 0

        return cleaned_data


from django import forms
from .models import StudentLogin

class StudentLoginForm(forms.ModelForm):
    class Meta:
        model = StudentLogin
        fields = ['admission_no', 'password']  # user enters only these



from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'
        widgets = {
            'next_due_date': forms.DateInput(attrs={'type': 'date'}),
            'tuition_due_date': forms.DateInput(attrs={'type': 'date'}),
            'transport_due_date': forms.DateInput(attrs={'type': 'date'}),
            'hostel_due_date': forms.DateInput(attrs={'type': 'date'}),
            'books_due_date': forms.DateInput(attrs={'type': 'date'}),
            'uniform_due_date': forms.DateInput(attrs={'type': 'date'}),
            'other_due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        if not self.instance.pk:
            self.fields['branch_code'].initial = 'PSCM/001/AY/2025-26'



from django import forms
from .models import ConfirmedAdmission
 
class ConfirmedAdmissionForm(forms.ModelForm):
    class Meta:
        model = ConfirmedAdmission
        fields = [
            'pu_admission',
            'degree_admission',
            'course',
            'documents_complete',
            'status',
            'student_userid',
            'student_password',
            'tuition_advance_amount',
            'student_name',
        ]


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

