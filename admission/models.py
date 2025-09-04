from django.db import models
from master.models import CourseType, Course, AcademicYear # adjust if your app name is different
import datetime
from django.utils.timezone import now
from core.utils import get_logged_in_user,log_activity

class Enquiry1(models.Model):
    enquiry_no = models.CharField(max_length=10, unique=True, blank=True)
    student_name = models.CharField(max_length=100)
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    PARENT_CHOICES = [
        ('Father', 'Father'),
        ('Mother', 'Mother'),
        ('Guardian', 'Guardian'),
    ]
    enquiry_date = models.DateField(default=now)
    parent_relation = models.CharField(max_length=10, choices=PARENT_CHOICES)
    guardian_relation = models.CharField(max_length=100, blank=True, null=True)  # new field
    parent_name = models.CharField(max_length=100)
    parent_phone = models.CharField(max_length=15)

    course_type = models.ForeignKey('master.CourseType', on_delete=models.PROTECT, default=13)
    course = models.ForeignKey('master.Course', on_delete=models.PROTECT)

    percentage_10th = models.FloatField()
    percentage_12th = models.FloatField(null=True, blank=True)
    
    email = models.EmailField(max_length=254)
    created_by = models.CharField(max_length=150, null=True, blank=True)

    permanent_address = models.TextField(blank=True, null=True)
    current_address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    is_converted = models.BooleanField(default=False)
    SOURCE_CHOICES = [
    ('Messages/Calls', 'Messages/Calls'),
    ('Social Media', 'Social Media'),
    ('Friends', 'Friends'),
    ('Other', 'Other'),
]

    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    other_source = models.CharField(max_length=100, blank=True, null=True)
    whatsapp_sent_date = models.DateField(null=True, blank=True)

    whatsapp_status = models.CharField(
    max_length=15,
    choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ],
    blank=True,
    null=True
)


    def save(self, *args, **kwargs):
        if not self.enquiry_no:
            last_enquiry = Enquiry1.objects.order_by('-id').first()
            if last_enquiry and last_enquiry.enquiry_no and last_enquiry.enquiry_no.startswith('PU-ENQ-'):
                try:
                    last_number = int(last_enquiry.enquiry_no.split('-')[-1])
                except (IndexError, ValueError):
                    last_number = 0
            else:
                last_number = 0
            self.enquiry_no = f"PU-ENQ-{last_number+1:02d}"

            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.enquiry_no} - {self.student_name}"


from django.db import models
from django.utils.timezone import now

class Enquiry2(models.Model):
    enquiry_no = models.CharField(max_length=10, unique=True, blank=True)
    student_name = models.CharField(max_length=100)
    
    # ✅ Added academic year field

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    PARENT_CHOICES = [
        ('Father', 'Father'),
        ('Mother', 'Mother'),
        ('Guardian', 'Guardian'),
    ]
    parent_relation = models.CharField(max_length=10, choices=PARENT_CHOICES)
    enquiry_date = models.DateField(default=now)

    guardian_relation = models.CharField(max_length=100, blank=True, null=True)
    parent_name = models.CharField(max_length=100)
    parent_phone = models.CharField(max_length=15)

    course_type = models.ForeignKey('master.CourseType', on_delete=models.PROTECT, default=17)
    course = models.ForeignKey('master.Course', on_delete=models.PROTECT)

    percentage_10th = models.FloatField()
    percentage_12th = models.FloatField(null=True, blank=True)
    
    email = models.EmailField(max_length=254)
    created_by = models.CharField(max_length=150, null=True, blank=True)

    permanent_address = models.TextField(blank=True, null=True)
    current_address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    is_converted = models.BooleanField(default=False)

    SOURCE_CHOICES = [
        ('Messages/Calls', 'Messages/Calls'),
        ('Social Media', 'Social Media'),
        ('Friends', 'Friends'),
        ('Other', 'Other'),
    ]
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    other_source = models.CharField(max_length=100, blank=True, null=True)
    
    whatsapp_sent_date = models.DateField(null=True, blank=True)
    whatsapp_status = models.CharField(
        max_length=15,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('failed', 'Failed')
        ],
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        if not self.enquiry_no:
            last_enquiry = Enquiry2.objects.order_by('-id').first()
            if last_enquiry and last_enquiry.enquiry_no and last_enquiry.enquiry_no.startswith('DEG-ENQ-'):
                try:
                    last_number = int(last_enquiry.enquiry_no.split('-')[2])
                except (IndexError, ValueError):
                    last_number = 0
            else:
                last_number = 0

            self.enquiry_no = f"DEG-ENQ-{last_number + 1:02d}"

        # ✅ Removed course_type auto-selection logic

        super().save(*args, **kwargs)





class FollowUp(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
    ]

    pu_enquiry = models.ForeignKey(Enquiry1, null=True, blank=True, on_delete=models.CASCADE)
    degree_enquiry = models.ForeignKey(Enquiry2, null=True, blank=True, on_delete=models.CASCADE)

    follow_up_type = models.CharField(max_length=100, blank=False, null=False)
    follow_up_date = models.DateTimeField(blank=False, null=False)
    priority = models.CharField(max_length=100, blank=False, null=False)
    notes = models.TextField(blank=False, null=False)
    next_action_required = models.CharField(max_length=255, blank=False, null=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        verbose_name="Follow-up Status"
    )

    def __str__(self):
        enquiry = self.pu_enquiry or self.degree_enquiry
        return f"{enquiry} - {self.follow_up_type} - {self.status}"

       


from master.models import CourseType, Course , AcademicYear # adjust import as per your app structure

 
class PUAdmission(models.Model):

    medium_of_instruction = models.CharField(max_length=100, blank=True, null=True)

    converstion_fee = models.CharField(max_length=10, blank=True, null=True)

    enquiry_no = models.CharField(max_length=20, blank=True, null=True)

    admission_no = models.CharField(max_length=20, blank=True, null=True)

    student_name = models.CharField(max_length=100)

    dob = models.DateField(null=True, blank=True)


    gender = models.CharField(

        max_length=10,

        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],

    )

    father_name = models.CharField(max_length=100)

    guardian_name = models.CharField(max_length=30, blank=True, null=True)

    guardian_address = models.CharField(max_length=100, blank=True, null=True)

    mother_name = models.CharField(max_length=30, blank=True, null=True)

    annual_income = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    mother_annual_income = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    total_annual_income = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    father_mobile_no = models.CharField(max_length=15, blank=True, null=True)  # Updated to match HTML

    mother_phone_no = models.CharField(max_length=15)

    father_email = models.EmailField(max_length=100, blank=True, null=True)

    mother_email = models.EmailField(max_length=100, blank=True, null=True)

    student_email = models.EmailField(max_length=100, blank=True, null=True)

    father_occupation = models.CharField(max_length=15)

    mother_occupation = models.CharField(max_length=15)

    student_phone_no = models.CharField(max_length=15, blank=True, null=True)

    aadhar_no = models.CharField(max_length=12, blank=True, null=True)

    mother_aadhar_no = models.CharField(max_length=12, blank=True, null=True)

    student_aadhar_no = models.CharField(max_length=12, blank=True, null=True)

    CASTE_CHOICES = [

    ('GENERAL', 'General'),

    ('OBC', 'OBC'),

    ('SC', 'SC'),

    ('ST', 'ST'),

    ]
 
    CATEGORY_CHOICES = [

        ('1', '1'),

        ('2A', '2A'),

        ('2B', '2B'),

        ('3A', '3A'),

        ('3B', '3B'),

        ('SC', 'SC'),

        ('ST', 'ST'),

        ('GM', 'General Merit'),

    ]

    BOARD_CHOICES = (
    ('IGCSE', 'IGCSE'),
    ('CBSE', 'CBSE'),
    ('ICSE', 'ICSE'),
    ('STATE', 'State Board'),
    ('OTHER', 'Other'),
)

    education_boards = models.CharField(max_length=20,choices=BOARD_CHOICES,blank=True,null=True)
 
    # Field names swapped

    caste = models.CharField(max_length=10, choices=CASTE_CHOICES)

    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)

    sub_caste = models.CharField(max_length=50, blank=True, null=True)

    BLOOD_GROUP_CHOICES = [

        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),

        ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')

    ]

    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)

    nationality = models.CharField(max_length=50, blank=True, null=True)

    country = models.CharField(max_length=50, blank=True, null=True)

    religion = models.CharField(max_length=50, blank=True, null=True)

    permanent_address = models.TextField(blank=True, null=True)

    current_address = models.TextField(blank=True, null=True)

    student_address = models.TextField(blank=True, null=True)

    city = models.CharField(max_length=100, blank=True, null=True)

    pincode = models.CharField(max_length=6, blank=True, null=True)

    state = models.CharField(max_length=100, blank=True, null=True)

    birthplace = models.CharField(max_length=100,blank=True, null=True)

    district = models.CharField(max_length=100,blank=True, null=True)
 
    # parents_occupation = models.CharField(max_length=100, blank=True, null=True)

    emergency_contact = models.CharField(max_length=15, blank=True, null=True)

    emergency_contact_name = models.CharField(max_length=15, blank=True, null=True)

    emergency_contact_relation = models.CharField(max_length=15, blank=True, null=True)

    # document_submitted = models.BooleanField(default=False)

    hostel_required = models.BooleanField(default=False)

    hostel_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # ✅ New field

    transport = models.ForeignKey('master.Transport', on_delete=models.SET_NULL, null=True, blank=True)

     # Academic details

    # year_of_passing = models.CharField(max_length=7, blank=True, null=True)

    # sslc_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    medium = models.CharField(max_length=50, blank=True, null=True)

    second_language = models.CharField(max_length=50, blank=True, null=True)

    first_language = models.CharField(max_length=50, blank=True, null=True)

    # Foreign keys for course

    course_type = models.ForeignKey('master.CourseType', on_delete=models.SET_NULL, null=True, blank=True, related_name='pu_admissions')

    course = models.ForeignKey('master.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='pu_admissions')


    # Quota type

    QUOTA_TYPE_CHOICES = [

        ('Regular', 'Regular'),

        ('Management', 'Management'),

        ('NRI', 'NRI'),

        ('RTE','RTE'),

    ]

    quota_type = models.CharField(

        max_length=20,

        blank=True, null=True)

    admission_taken_by = models.IntegerField(null=True, blank=True)

    admission_date = models.DateField(default=datetime.date.today)

    # Last studied course details (subjects/marks)

    register_no_course = models.CharField(max_length=100, blank=True, null=True)

    month_year_passed = models.CharField(max_length=50, blank=True, null=True)

    subject1 = models.CharField(max_length=100, blank=True, null=True)

    marks_obtained1 = models.CharField(max_length=50, blank=True, null=True)

    total_marks_percentage1 = models.CharField(max_length=50, blank=True, null=True)

    subject2 = models.CharField(max_length=100, blank=True, null=True)

    marks_obtained2 = models.CharField(max_length=50, blank=True, null=True)

    total_marks_percentage2 = models.CharField(max_length=50, blank=True, null=True)

    subject3 = models.CharField(max_length=100, blank=True, null=True)

    marks_obtained3 = models.CharField(max_length=50, blank=True, null=True)

    total_marks_percentage3 = models.CharField(max_length=50, blank=True, null=True)

    subject4 = models.CharField(max_length=100, blank=True, null=True)

    marks_obtained4 = models.CharField(max_length=50, blank=True, null=True)

    total_marks_percentage4 = models.CharField(max_length=50, blank=True, null=True)

    subject5 = models.CharField(max_length=100, blank=True, null=True)

    marks_obtained5 = models.CharField(max_length=50, blank=True, null=True)

    total_marks_percentage5 = models.CharField(max_length=50, blank=True, null=True)

    subject6 = models.CharField(max_length=100, blank=True, null=True)

    marks_obtained6 = models.CharField(max_length=50, blank=True, null=True)

    total_marks_percentage6 = models.CharField(max_length=50, blank=True, null=True)

    max_marks1 = models.CharField(max_length=50, blank=True, null=True)  # NEW    

    max_marks2 = models.CharField(max_length=50, blank=True, null=True)  # NEW

    max_marks3 = models.CharField(max_length=50, blank=True, null=True)  # NEW

    max_marks4 = models.CharField(max_length=50, blank=True, null=True)  # NEW

    max_marks5 = models.CharField(max_length=50, blank=True, null=True)  # NEW

    max_marks6 = models.CharField(max_length=50, blank=True, null=True)  # NEW
 
    total_marks_obtained = models.IntegerField(null=True, blank=True)

    total_max_marks = models.IntegerField(null=True, blank=True)

    overall_percentage = models.CharField(max_length=10, null=True, blank=True)
 
    co_curricular_activities = models.TextField(blank=True, null=True)

    # Fee related fields

    application_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    books_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    uniform_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    tuition_advance_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    final_fee_after_advance = models.DecimalField(max_digits=10, decimal_places=2)
 


    # Declaration

    student_declaration_date = models.DateField(blank=True, null=True)

    student_declaration_place = models.CharField(max_length=100, blank=True, null=True)

    parent_declaration_date = models.DateField(blank=True, null=True)

    parent_declaration_place = models.CharField(max_length=100, blank=True, null=True)

    admitted_to = models.ForeignKey('master.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='pu_admitted_students')

    # Office use

    receipt_no = models.CharField(max_length=50, blank=True, null=True)

    receipt_date = models.DateField(blank=True, null=True)

    payment_mode = models.CharField(

        max_length=20,

        choices=[('Online', 'Online'), ('Cash', 'Cash')]

    )    

    utr_no = models.CharField(max_length=50, blank=True, null=True)

    # accountant_signature = models.CharField(max_length=255, blank=True, null=True)

    # Document submission flags

    doc_aadhar = models.BooleanField(default=False)

    doc_marks_card = models.BooleanField(default=False)

    doc_caste_certificate = models.BooleanField(default=False)  # ✅ New field

    doc_income_certificate = models.BooleanField(default=False)  # ✅ New field

    doc_transfer = models.BooleanField(default=False)

    doc_migration = models.BooleanField(default=False)

    doc_study = models.BooleanField(default=False)

    doc_participation_documents  = models.BooleanField(default=False)

        # Scholarship details

    has_scholarship = models.BooleanField(default=False)

    scholarship_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    status = models.CharField(

    max_length=20,

    choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Review', 'Review')],

    default='Pending'

)

    sats_number = models.CharField(max_length=50, blank=True, null=True)

    wants_transport = models.BooleanField(default=False)

    transport_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    school_name_laststudied = models.CharField(max_length=255, blank=True, null=True)

    school_addresslaststudied = models.CharField(max_length=100, blank=True, null=True)

    # Photo

    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)
    admission_source = models.CharField(
    max_length=20,
    choices=[('enquiry', 'Enquiry'), ('direct', 'Direct'), ('bulk_import', 'Bulk Import')],
    default=None,
    null=True,
    blank=True
)
    @property
    def document_submitted(self):
        return (
            self.doc_aadhar and
            self.doc_marks_card and
            self.doc_caste_certificate and
            self.doc_income_certificate and
            self.doc_transfer
        )


    def __str__(self):
        return f"{self.admission_no} - {self.student_name}"


 


import datetime
from django.db import models
from master.models import Transport
class DegreeAdmission(models.Model):
    medium_of_instruction = models.CharField(max_length=100, blank=True, null=True)
    converstion_fee = models.CharField(max_length=10, blank=True, null=True)
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    QUOTA_TYPE_CHOICES = [
        ('Regular', 'Regular'),
        ('Management', 'Management'),
        ('NRI', 'NRI'),
        ('RTE','RTE'),
    ]
    quota_type = models.CharField(
        max_length=20,
        choices=QUOTA_TYPE_CHOICES,
        default='Regular'
    )
    CASTE_CHOICES = [
    ('GENERAL', 'General'),
    ('OBC', 'OBC'),
    ('SC', 'SC'),
    ('ST', 'ST'),
    ]

    CATEGORY_CHOICES = [
        ('1', '1'),
        ('2A', '2A'),
        ('2B', '2B'),
        ('3A', '3A'),
        ('3B', '3B'),
        ('SC', 'SC'),
        ('ST', 'ST'),
        ('GM', 'General Merit'),
    ]
   
    BOARD_CHOICES = (
    ('IGCSE', 'IGCSE'),
    ('CBSE', 'CBSE'),
    ('ICSE', 'ICSE'),
    ('STATE', 'State Board'),
    ('OTHER', 'Other'),
    )

    education_boards = models.CharField(max_length=20,choices=BOARD_CHOICES,blank=True,null=True)
    # Field names swapped
    caste = models.CharField(max_length=10, choices=CASTE_CHOICES)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    sub_caste = models.CharField(max_length=50, blank=True, null=True)

    # Primary key 'id' is auto-created by Django unless you specify otherwise
    admission_no = models.CharField(max_length=20, blank=True, null=True)

    student_name = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    
    student_phone_no = models.CharField(max_length=15, blank=True, null=True)
    father_mobile_no = models.CharField(max_length=15, blank=True, null=True)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_annual_income = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    mother_annual_income = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    mother_name = models.CharField(max_length=30, blank=True, null=True)
    guardian_name = models.CharField(max_length=30, blank=True, null=True)
    guardian_address = models.CharField(max_length=100, blank=True, null=True)
    mother_occupation = models.CharField(max_length=15)
    mother_phone_no = models.CharField(max_length=15)
    mother_aadhar_no = models.CharField(max_length=12, blank=True, null=True)
    father_occupation = models.CharField(max_length=15)
    year_of_passing = models.CharField(max_length=7, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    admission_date = models.DateField(default=datetime.date.today)
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)
    application_status = models.CharField(max_length=30, default='Pending', blank=True, null=True)
    enquiry_no = models.CharField(max_length=10, blank=True, null=True)
    has_scholarship = models.BooleanField(default=False)
    scholarship_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    course_type = models.ForeignKey(
        'master.CourseType', on_delete=models.SET_NULL, null=True, blank=True, related_name='degree_admissions'
    )
    course = models.ForeignKey(
        'master.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='degree_admissions'
    )

    nationality = models.CharField(max_length=50, blank=True, null=True)
    religion = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    permanent_address = models.TextField(blank=True, null=True)
    current_address = models.TextField(blank=True, null=True)
    student_address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    birthplace = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)

    # parents_occupation = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_relation = models.CharField(max_length=15, blank=True, null=True)
    # document_submitted = models.BooleanField(default=False)
    hostel_required = models.BooleanField(default=False)
    hostel_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # ✅ New field
    transport = models.ForeignKey(Transport, on_delete=models.SET_NULL, null=True, blank=True)

    pincode = models.CharField(max_length=6, blank=True, null=True)
    father_name = models.CharField(max_length=100, blank=True, null=True)
    aadhar_no = models.CharField(max_length=12, blank=True, null=True)
    student_aadhar_no = models.CharField(max_length=12, blank=True, null=True)
    admission_taken_by = models.IntegerField(blank=True, null=True)
    mother_email = models.EmailField(max_length=100, blank=True, null=True)
    father_email = models.EmailField(max_length=100, blank=True, null=True)
    student_email = models.EmailField(max_length=100, blank=True, null=True)
    sslc_reg_no = models.CharField(max_length=30, blank=True, null=True)
    sslc_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    pu_college_name = models.CharField(max_length=255, blank=True, null=True)
    medium = models.CharField(max_length=50, blank=True, null=True)
    first_language = models.CharField(max_length=50, blank=True, null=True)
    second_language = models.CharField(max_length=50, blank=True, null=True)
    college_last_attended = models.CharField(max_length=255, blank=True, null=True)
    college_addresslaststudied = models.CharField(max_length=100, blank=True, null=True)
    register_no_course = models.CharField(max_length=100, blank=True, null=True)
    month_year_passed = models.CharField(max_length=50, blank=True, null=True)
    co_curricular_activities = models.TextField(blank=True, null=True)
    student_declaration_date = models.DateField(blank=True, null=True)
    student_declaration_place = models.CharField(max_length=100, blank=True, null=True)
    parent_declaration_date = models.DateField(blank=True, null=True)
    parent_declaration_place = models.CharField(max_length=100, blank=True, null=True)
    receipt_no = models.CharField(max_length=50, blank=True, null=True)
    receipt_date = models.DateField(blank=True, null=True)
    payment_mode = models.CharField(
        max_length=20,
        choices=[('Online', 'Online'), ('Cash', 'Cash')]
    )    
    utr_no = models.CharField(max_length=50, blank=True, null=True)
    accountant_signature = models.CharField(max_length=255, blank=True, null=True)

    subject1 = models.CharField(max_length=100, blank=True, null=True)
    marks_obtained1 = models.CharField(max_length=50, blank=True, null=True)
    total_marks_percentage1 = models.CharField(max_length=50, blank=True, null=True)

    subject2 = models.CharField(max_length=100, blank=True, null=True)
    marks_obtained2 = models.CharField(max_length=50, blank=True, null=True)
    total_marks_percentage2 = models.CharField(max_length=50, blank=True, null=True)

    subject3 = models.CharField(max_length=100, blank=True, null=True)
    marks_obtained3 = models.CharField(max_length=50, blank=True, null=True)
    total_marks_percentage3 = models.CharField(max_length=50, blank=True, null=True)

    subject4 = models.CharField(max_length=100, blank=True, null=True)
    marks_obtained4 = models.CharField(max_length=50, blank=True, null=True)
    total_marks_percentage4 = models.CharField(max_length=50, blank=True, null=True)

    subject5 = models.CharField(max_length=100, blank=True, null=True)
    marks_obtained5 = models.CharField(max_length=50, blank=True, null=True)
    total_marks_percentage5 = models.CharField(max_length=50, blank=True, null=True)

    subject6 = models.CharField(max_length=100, blank=True, null=True)
    marks_obtained6 = models.CharField(max_length=50, blank=True, null=True)
    total_marks_percentage6 = models.CharField(max_length=50, blank=True, null=True)
    max_marks1 = models.CharField(max_length=50, blank=True, null=True)  # NEW    
    max_marks2 = models.CharField(max_length=50, blank=True, null=True)  # NEW
    max_marks3 = models.CharField(max_length=50, blank=True, null=True)  # NEW
    max_marks4 = models.CharField(max_length=50, blank=True, null=True)  # NEW
    max_marks5 = models.CharField(max_length=50, blank=True, null=True)  # NEW
    max_marks6 = models.CharField(max_length=50, blank=True, null=True)  # NEW


    total_marks_obtained = models.IntegerField(null=True, blank=True)
    total_max_marks = models.IntegerField(null=True, blank=True)
    overall_percentage = models.CharField(max_length=10, null=True, blank=True)


            # Fee related fields
    application_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    books_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    uniform_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tuition_advance_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    transport_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    final_fee_after_advance = models.DecimalField(max_digits=10, decimal_places=2)


    # Document submission checkboxes
    doc_aadhar = models.BooleanField(default=False)
    doc_marks_card = models.BooleanField(default=False)
    doc_caste_certificate = models.BooleanField(default=False)  # ✅ New field
    doc_income_certificate = models.BooleanField(default=False)  # ✅ New field
    doc_transfer = models.BooleanField(default=False)
    doc_migration = models.BooleanField(default=False)
    doc_study = models.BooleanField(default=False)
    doc_participation_documents  = models.BooleanField(default=False)

    status = models.CharField(
    max_length=20,
    choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Review', 'Review')],
    default='Pending'
)
    # STATS Number field
    sats_number = models.CharField(max_length=50, blank=True, null=True)

    admitted_to = models.ForeignKey(
        'master.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='admitted_students'
    )
    admission_source = models.CharField(
    max_length=20,
    choices=[('enquiry', 'Enquiry'), ('direct', 'Direct'), ('bulk_import', 'Bulk Import')],
    default=None,
    null=True,
    blank=True
)
    @property
    def document_submitted(self):
        return (
            self.doc_aadhar and
            self.doc_marks_card and
            self.doc_caste_certificate and
            self.doc_income_certificate and
            self.doc_transfer
        )


    def __str__(self):
        return f"{self.admission_no} - {self.student_name}"



    # For PUAdmission
from django.db import models
class PUAdmissionshortlist(models.Model):
    admission_no = models.CharField(max_length=20)
    parent_mobile_no = models.CharField(max_length=15)
    email = models.EmailField()
    student_name = models.CharField(max_length=100)
    quota_type = models.CharField(
        max_length=20,
        choices=[
            ('Regular', 'Regular'),
            ('Management', 'Management'),
        ]
    )
    application_status = models.CharField(
        max_length=50,
        choices=[
            ('Pending', 'Pending'),
            ('Shortlisted', 'Shortlisted'),
            ('Rejected', 'Rejected'),
            ('Shortlisted(M)', 'Shortlisted Management'),  # Short code stored, label shown
        ],
        default='Pending'
    )
    admin_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.student_name


class DegreeAdmissionshortlist(models.Model):
    admission_no = models.CharField(max_length=20)
    parent_mobile_no = models.CharField(max_length=15)
    email = models.EmailField()
    student_name = models.CharField(max_length=100)
    quota_type = models.CharField(
        max_length=20,
        choices=[
            ('Regular', 'Regular'),
            ('Management', 'Management'),
        ]
    )
    application_status = models.CharField(
        max_length=50,
        choices=[
            ('Pending', 'Pending'),
            ('Shortlisted', 'Shortlisted'),
            ('Rejected', 'Rejected'),
            ('Shortlisted(M)', 'Shortlisted Management'),  # Short code stored, label shown
        ],
        default='Pending'
    )
    admin_approved = models.BooleanField(default=False)



    def __str__(self):
        return self.student_name

from django.db import models

from django.db import models

class PUFeeDetail(models.Model):
    student_name = models.CharField(max_length=100)
    admission_no = models.CharField(max_length=20)
    course = models.CharField(max_length=100)

    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    scholarship = models.DecimalField(max_digits=10, decimal_places=2)
    final_fee_after_advance = models.DecimalField(max_digits=10, decimal_places=2)
    tuition_advance_amount = models.DecimalField(max_digits=10, decimal_places=2)
    gross_fee = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    payment_mode = models.CharField(
        max_length=20,
        choices=[('Online', 'Online'), ('Offline', 'Offline')]
    )

    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hostel_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    books_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    uniform_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
     # 🔁 Automatically updates on save

    def __str__(self):
        return f"{self.admission_no} - {self.student_name}"





from django.db import models
from .models import DegreeAdmission  # Make sure this import is correct

class DegreeFeeDetail(models.Model):
    student_name = models.CharField(max_length=100)
    admission_no = models.CharField(max_length=20)
    course = models.CharField(max_length=10)

    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    scholarship = models.DecimalField(max_digits=10, decimal_places=2)
    final_fee_after_advance = models.DecimalField(max_digits=10, decimal_places=2)
    tuition_advance_amount = models.DecimalField(max_digits=10, decimal_places=2)
    gross_fee = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    # Newly added fields
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hostel_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    books_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    uniform_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    payment_mode = models.CharField(
        max_length=20,
        choices=[('Online', 'Online'), ('Offline', 'Offline')]
    )
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)


    def __str__(self):
        return f"{self.admission_no} - {self.student_name}"

class StudentLogin(models.Model):
    admission_no = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=128)
    is_default_password = models.BooleanField(default=True)
    # student_type = models.CharField(max_length=10, choices=[('PU', 'PU'), ('Degree', 'Degree')])
    parent_mobile_no = models.CharField(max_length=15)
    email = models.EmailField()
    student_name = models.CharField(max_length=100)

    def __str__(self):
        return self.admission_no



from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now

from django.db import models


from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now

from django.db import models

from django.db import models

class Student(models.Model):
    STATUS_CHOICES = [
        ('Regular', 'Regular'),
        ('Paid', 'Paid'),
        ('Partial', 'Partial'),
        ('Due', 'Due'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Online', 'Online'),
        ('Bank Transfer', 'Bank Transfer'),
    ]

    # ─────────── Core Fields ───────────
    academic_year = models.CharField(max_length=9)
    admission_no = models.CharField(max_length=20, unique=True)
    name         = models.CharField(max_length=100)
    course       = models.CharField(max_length=100)

    # ─────────── Scholarships / Advance ───────────

    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    scholarship = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tuition_advance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_fee_after_advance = models.DecimalField(max_digits=10, decimal_places=2)
       
   # ─────────── Tuition Fee ───────────

    tuition_fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tuition_pending_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tuition_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tuition_due_date = models.DateField(null=True, blank=True)

    # ─────────── Transport Fee ───────────
    transport_fee = models.CharField(max_length=100)
    transport_fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_pending_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    transport_due_date = models.DateField(null=True, blank=True)

    # ─────────── Hostel Fee ───────────
    hostel_fee = models.CharField(max_length=100)
    hostel_fee_paid = models.DecimalField(max_digits=10, decimal_places=2)
    hostel_pending_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hostel_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    hostel_due_date = models.DateField(null=True, blank=True)

    # ─────────── Books Fee ───────────
    books_fee = models.CharField(max_length=100)
    books_fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    books_pending_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    books_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    books_due_date = models.DateField(null=True, blank=True)

    # ─────────── Uniform Fee ───────────
    uniform_fee = models.CharField(max_length=100)
    uniform_fee_paid = models.DecimalField(max_digits=10, decimal_places=2)
    uniform_pending_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uniform_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    uniform_due_date = models.DateField(null=True, blank=True)

    # ─────────── Other Fee ───────────
    other_fee = models.CharField(max_length=100, blank=True, null=True)
    other_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # ─────────── Meta / Receipt Info ───────────
    receipt_no = models.CharField(max_length=50, blank=True, null=True)
    receipt_date = models.DateField(blank=True, null=True)
    branch_code = models.CharField(max_length=30, default='PSCM/001/AY/2025-26', blank=True)

    # ─────────── Payment Meta ───────────
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.admission_no} - {self.name}"


from django.db import models
from django.db import models

class StudentPaymentHistory(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Online', 'Online'),
        ('Bank Transfer', 'Bank Transfer'),
    ]

    # ─────────── Core Student Info ───────────
    admission_no    = models.CharField(max_length=20)
    name            = models.CharField(max_length=100)
    course          = models.CharField(max_length=100)

    # ─────────── Scholarships / Advance ───────────
    scholarship             = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tuition_advance_amount  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_fee_after_advance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


    # ─────────── Tuition Fee ───────────
    tuition_fee             = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tuition_fee_paid        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tuition_pending_fee     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tuition_amount          = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tuition_due_date        = models.DateField(null=True, blank=True)

    # ─────────── Transport Fee ───────────
    transport_fee           = models.CharField(max_length=100, null=True, blank=True)
    transport_fee_paid      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_pending_fee   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_amount        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    transport_due_date      = models.DateField(null=True, blank=True)

    # ─────────── Hostel Fee ───────────
    hostel_fee              = models.CharField(max_length=100, null=True, blank=True)
    hostel_fee_paid         = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hostel_pending_fee      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hostel_amount           = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hostel_due_date         = models.DateField(null=True, blank=True)

    # ─────────── Books Fee ───────────
    books_fee               = models.CharField(max_length=100, null=True, blank=True)
    books_fee_paid          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    books_pending_fee       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    books_amount            = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    books_due_date          = models.DateField(null=True, blank=True)

    # ─────────── Uniform Fee ───────────
    uniform_fee             = models.CharField(max_length=100, null=True, blank=True)
    uniform_fee_paid        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uniform_pending_fee     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uniform_amount          = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    uniform_due_date        = models.DateField(null=True, blank=True)

    # ─────────── Other Fee ───────────
    other_fee               = models.CharField(max_length=100, null=True, blank=True)
    other_amount            = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


    # ─────────── Receipt and Branch Info ───────────
    receipt_no              = models.CharField(max_length=50, blank=True, null=True)
    receipt_date            = models.DateField(blank=True, null=True)
    branch_code             = models.CharField(max_length=30, default='PSCM/001/AY/2025-26')

    # ─────────── Meta Info ───────────
    payment_method          = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    payment_date            = models.DateField(null=True, blank=True)

    # ─────────── String Representation ───────────
    def __str__(self):
        return f"{self.admission_no} - ₹{self.total_amount_paid()}"

    def total_amount_paid(self):
        return (
            self.tuition_fee_paid +
            self.transport_fee_paid +
            self.hostel_fee_paid +
            self.books_fee_paid +
            self.uniform_fee_paid +
            (self.other_amount or 0)
        )



from master.models import CourseType
from admission.models import PUAdmission, DegreeAdmission  # Make sure you import these

class ConfirmedAdmission(models.Model):
    # ForeignKeys to either PUAdmission or DegreeAdmission
    pu_admission = models.ForeignKey( PUAdmission, on_delete=models.CASCADE,null=True, blank=True,related_name='confirmed_pu_admissions')
    degree_admission = models.ForeignKey(DegreeAdmission, on_delete=models.CASCADE,null=True, blank=True,related_name='confirmed_degree_admissions')

    # Common fields
    student_name = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    admission_date = models.DateField()
    documents_complete = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='confirmed')
    student_userid = models.CharField(max_length=50, blank=True, null=True)
    student_password = models.CharField(max_length=128, blank=True, null=True)
    tuition_advance_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)
    current_year = models.IntegerField(default=1, null=True, blank=True)  # For PU
    semester = models.IntegerField(default=1, null=True, blank=True)     # For Degree
    # In ConfirmedAdmission model
    password_changed = models.BooleanField(default=False)
    passcode = models.CharField(max_length=10, blank=True, null=True)
    passcode_set = models.BooleanField(default=False)
    wrong_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)



    def __str__(self):
        if self.pu_admission:
            return f"{self.pu_admission.admission_no} (PU)"
        elif self.degree_admission:
            return f"{self.degree_admission.admission_no} (Degree)"
        return "Unlinked Admission"


    from django.db import models

class FeeCollection(models.Model):
    admission_no = models.CharField(max_length=50)
    fee_name = models.CharField(max_length=100)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    payment_mode = models.CharField(max_length=50, null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fine = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.admission_no} - {self.fee_name} - {self.paid_amount}"










from django.db import models

class StudentFeeCollection(models.Model):
    admission_no = models.CharField(max_length=30)
    student_userid = models.CharField(max_length=50, blank=True, null=True)
    academic_year = models.CharField(max_length=9)
    semester = models.IntegerField(null=True, blank=True)
    fee_type = models.ForeignKey('master.FeeMaster', on_delete=models.CASCADE)
    installment_number = models.IntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    payment_mode = models.CharField(
        max_length=30,
        choices=[
            ('Cash', 'Cash'),
            
            ('Online', 'Online'),
           
            ('Bank Transfer', 'Bank Transfer')
        ],
        null=True,
        blank=True
    )
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Partial', 'Partial'),
            ('Paid', 'Paid')
        ],
        default='Pending'
    )

    def __str__(self):
        return f"{self.admission_no} - {self.fee_type.fee_name} - Inst {self.installment_number} - {self.status}"



