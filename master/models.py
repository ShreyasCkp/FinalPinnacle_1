"""
Definition of models.
"""

from django.db import models

from django.db import models
class UserCustom(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)

    passcode = models.CharField(max_length=10, blank=True, null=True)  # Or use max_length you want
    passcode_set = models.BooleanField(default=False)
    can_reset_password = models.BooleanField(default=False) 

    wrong_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)


    def __str__(self):
        return self.username

from django.db import models

class AcademicYear(models.Model):
    year = models.CharField(max_length=9, unique=True)  # Format: "2024-2025"
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.year


class ExcelUpload(models.Model):
    file = models.FileField(upload_to='excel_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class StudentRecord(models.Model):
    student_id = models.CharField(max_length=20)
    student_name = models.CharField(max_length=100)
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=15)
    guardian_relation = models.CharField(max_length=50)
    department = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.student_name} ({self.student_id})"
# class SentMessage(models.Model):
#     subject = models.CharField(max_length=255)
#     message = models.TextField()
#     send_sms = models.BooleanField(default=False)
#     send_whatsapp = models.BooleanField(default=False)
#     department = models.CharField(max_length=100)
#     sent_at = models.DateTimeField(auto_now_add=True)
    
#     # Add this field for status
#     status = models.CharField(max_length=255, default="sms:0 whatsapp:0")

#     # Adding foreign keys to link the message to the student and guardian phone
#     student_name = models.ForeignKey(StudentRecord, on_delete=models.CASCADE, related_name='sent_messages')
#     guardian_phone_no = models.CharField(max_length=15, blank=True, null=True)  # Added phone number field

#     def __str__(self):
#         return f"{self.subject} ({self.department})"

# class MessageDelivery(models.Model):
#     message = models.ForeignKey(SentMessage, on_delete=models.CASCADE, related_name='deliveries')
#     student = models.ForeignKey(StudentRecord, on_delete=models.CASCADE)
#     phone_number = models.CharField(max_length=15)
#     status = models.CharField(
#         max_length=20,
#         choices=[('Delivered', 'Delivered'), ('Not Delivered', 'Not Delivered'), ('Pending', 'Pending')],
#         default='Pending'
#     )

#     def __str__(self):
#         return f"{self.student.student_name} - {self.status}"

class Student(models.Model):
    id = models.AutoField(primary_key=True)
    admission_no = models.CharField(max_length=20, unique=True)
    student_name = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    phone = models.CharField(max_length=15, null=True, blank=True)
    parent_phone = models.CharField(max_length=15, null=True, blank=True)
    course_type = models.CharField(max_length=10, choices=[('PU', 'PU'), ('Degree', 'Degree')])
    category = models.CharField(max_length=10, null=True, blank=True)
    quota_type = models.CharField(max_length=20)
    admission_date = models.DateField()

    class Meta:
        db_table = 'master_student'  # tells Django to use your manually created table

    def __str__(self):
        return f"{self.student_name} ({self.admission_no})"



from master.models import AcademicYear
 # or wherever your Course model is defined
class Subject(models.Model):
    name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20, null=True, blank=True)
    credit = models.PositiveIntegerField(null=True, blank=True)
    course = models.ForeignKey('master.Course', on_delete=models.CASCADE)
    semester = models.PositiveIntegerField() 
    is_active = models.BooleanField(default=True)  # ✅ Add this field
    academic_year = models.ForeignKey(AcademicYear,on_delete=models.SET_NULL,null=True,blank=True)
    program_type = models.ForeignKey('master.CourseType', on_delete=models.CASCADE, null=True, blank=True)  # ✅ Fixed  # ✅ add this


    def __str__(self):
        return f"{self.name} {self.semester}"

       
# class Subject(models.Model):
#     name = models.CharField(max_length=100)
#     semester_number = models.PositiveIntegerField()
#     course = models.ForeignKey('Course', on_delete=models.CASCADE)
#     subject_code = models.CharField(max_length=20, null=True, blank=True)
#     credit = models.PositiveIntegerField(null=True, blank=True)
#     faculty = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True)

#     def __str__(self):
#         return f"{self.name} (Sem {self.semester_number}, {self.course.name})"

# class Subject(models.Model):
#     name = models.CharField(max_length=100)
#     semester_number = models.PositiveIntegerField()
#     course = models.ForeignKey('Course', on_delete=models.CASCADE)
#     subject_code = models.CharField(max_length=20, null=True, blank=True)
#     credit = models.PositiveIntegerField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.name} (Sem {self.semester_number}, {self.course.name})"

from django.db import models

class Semester(models.Model):
    number = models.PositiveIntegerField()
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)  # ✅ Active (1) or Inactive (0)

    def __str__(self):
        return f"Sem {self.number} - {self.course.name}"


class CourseType(models.Model):
    id = models.AutoField(primary_key=True)  # AutoIncrement field, UNSIGNED is not explicitly specified in Django
    name = models.CharField(max_length=100)
    academic_year = models.ForeignKey(AcademicYear,on_delete=models.SET_NULL,null=True,blank=True)
    def __str__(self):
        return self.name


from django.db import models
from master.models import AcademicYear
class Course(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    duration_years = models.PositiveIntegerField()
    total_semesters = models.IntegerField(null=True, blank=True)
    course_type = models.ForeignKey(
        'CourseType',
        on_delete=models.CASCADE,
        related_name='courses'
    )
    is_active = models.BooleanField(default=True)  # NEW FIELD
    academic_year = models.ForeignKey(AcademicYear,on_delete=models.SET_NULL,null=True,blank=True)

    def __str__(self):
        return self.name


class Transport(models.Model):
    route_name = models.CharField(max_length=100)
    route = models.CharField(max_length=255)
    bus_no = models.CharField(max_length=50)
    driver_name = models.CharField(max_length=100)
    driver_contact_no = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.bus_no} - {self.route_name}"

from admission.models import PUAdmission, DegreeAdmission

class StudentDatabase(models.Model):
    pu_admission = models.ForeignKey(PUAdmission, on_delete=models.CASCADE, null=True, blank=True, related_name='student_pu_admissions')
    degree_admission = models.ForeignKey(DegreeAdmission, on_delete=models.CASCADE, null=True, blank=True, related_name='student_degree_admissions')
    student_name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_database')
    quota_type = models.CharField(max_length=20, blank=True, null=True)
   
    student_userid = models.CharField(max_length=50, blank=True, null=True)
    # New fields:
    student_phone_no = models.CharField(max_length=15, blank=True, null=True)  # Match admission model
    father_name = models.CharField(max_length=100, blank=True, null=True)
    course_type = models.ForeignKey(CourseType, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_database_entries')
    academic_year = models.CharField(max_length=9)  # E.g., "2025–2026"
    current_year = models.IntegerField(null=True, blank=True)  # For PU
    semester = models.IntegerField(null=True, blank=True)  # For Degree

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Graduated', 'Graduated'),
        ('Dropped', 'Dropped'),
        ('Transferred', 'Transferred'),
        ('Suspended', 'Suspended'),
        ('Inactive', 'Inactive'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    class Meta:
        db_table = 'master_student_database'

    def __str__(self):
        return f"{self.get_admission_no()} - {self.student_name}"

    def get_admission_no(self):
        if self.pu_admission:
            return self.pu_admission.admission_no
        elif self.degree_admission:
            return self.degree_admission.admission_no
        return "Unlinked"



class EventType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.name


class AcademicEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.date}"




class SentMessage(models.Model):
    subject = models.CharField(max_length=255)
    message = models.TextField()
    send_sms = models.BooleanField(default=False)
    send_whatsapp = models.BooleanField(default=False)
    department = models.CharField(max_length=100)
    template_name = models.CharField(max_length=255, null=True, blank=True)  # <-- add this
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} ({self.department})"




class SentMessageContact(models.Model):
    sent_message = models.ForeignKey(SentMessage, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15)
    status = models.CharField(max_length=20, default='Pending')  # Sent / Failed / Pending
    sent_date = models.DateField(null=True, blank=True)  

    def __str__(self):
        return f"{self.phone} - {self.status}"


class UserPermission(models.Model):
    user = models.ForeignKey(UserCustom, on_delete=models.CASCADE)
    form_name = models.CharField(max_length=150)

    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_access = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'form_name')

    def __str__(self):
        return f"{self.user.username} - {self.form_name}"



class Employee(models.Model):
    DESIGNATION_CHOICES = [
        ('Professor', 'Professor'),
        ('Associate Professor', 'Associate Professor'),
        ('Assistant', 'Assistant'),
    ]

    EMPLOYMENT_TYPE = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
    ]

    CATEGORY_CHOICES = [
        ('Teaching Staff', 'Teaching Staff'),
        ('Non-Teaching Staff', 'Non-Teaching Staff'),
    ]
    ROLE_CHOICES = [
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary'),
    ]
    employee_userid = models.CharField(max_length=50, unique=True, blank=True, null=True)
    employee_password = models.CharField(max_length=50, blank=True, null=True)  # plain text password
    password_changed = models.BooleanField(default=False)
    passcode = models.CharField(max_length=10, blank=True, null=True)
    passcode_set = models.BooleanField(default=False)
    wrong_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES,  blank=True,  # <-- Make it optional
    null=True )  # New field
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES) 
    emp_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    designation = models.CharField(
    max_length=50,
    choices=DESIGNATION_CHOICES,
    blank=True,  # <-- Make it optional
    null=True    # <-- Optional in DB too (for MySQL)
)

   
    email = models.EmailField()
    phone = models.CharField(max_length=10)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE)


      # Employment Info
    joining_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, null=True)  # Work location or branch

    # Personal Details
    dob = models.DateField(null=True, blank=True)  # Date of Birth
    uan_number = models.CharField(max_length=12, blank=True, null=True)  # Universal Account Number
    pan_number = models.CharField(max_length=10, blank=True, null=True)  # PAN
    aadhaar_number = models.CharField(max_length=12, blank=True, null=True)  # Aadhaar
    pf_number = models.CharField(max_length=50, blank=True, null=True)  # Provident Fund number
    esi_number = models.CharField(max_length=50, blank=True, null=True)  # ESI number
    user = models.ForeignKey('UserCustom', on_delete=models.SET_NULL, null=True, blank=True)
    # Bank Details
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    bank_account_number = models.CharField(max_length=30, blank=True, null=True)
    branch_name = models.CharField(max_length=100, blank=True, null=True)
   
    # created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

from django.db import models
from .models import Course, Subject
from .models import Employee  # or wherever your Employee model is

class EmployeeSubjectAssignment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='subject_assignments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.IntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    is_class_teacher = models.BooleanField(default=False)

    class Meta:
        unique_together = ('employee', 'course', 'semester', 'subject')

    def __str__(self):
        return f"{self.employee} - {self.subject} (Sem {self.semester})"



from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"To: {self.user.username} - {self.message[:30]}"



    
from django.db import models
from master.models import AcademicYear, CourseType, Course

class FeeMaster(models.Model):
    fee_name = models.CharField(max_length=100)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2)
    program_type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    combination = models.ForeignKey(Course, on_delete=models.CASCADE)
    due_date = models.DateField()
    # ➡️ Added academic year field:
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.fee_name} ({self.program_type.name} - {self.combination.name} - {self.academic_year.year})"

    
class PromotionHistory(models.Model):
    admission_no = models.CharField(max_length=50)
    academic_year = models.CharField(max_length=9)
    promotion_cycle = models.CharField(max_length=9) # "2025–2026"
    from_year = models.IntegerField(null=True, blank=True)
    to_year = models.IntegerField(null=True, blank=True)
    from_semester = models.IntegerField(null=True, blank=True)
    to_semester = models.IntegerField(null=True, blank=True)
    promotion_date = models.DateField(null=True, blank=True)
    student_userid = models.CharField(max_length=50, null=True, blank=True) 
    student_name = models.CharField(max_length=100)
    class Meta:
        db_table = 'student_promotion_history'

    def __str__(self):
        return f"{self.admission_no} promoted in {self.academic_year}"


class FeeType(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g. Tuition, Hostel
    is_optional = models.BooleanField(default=False)      # Hostel, Transport
    is_deductible = models.BooleanField(default=False)    # For Scholarship
 
    def __str__(self):
        return self.name

class Chapter(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)  # For sorting chapters
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.subject.name}"


class Content(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('PDF', 'PDF'),
        ('Video', 'Video'),
        ('Text', 'Text'),
        ('Assignment', 'Assignment'),
        ('Link', 'Link'),
    ]

    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    file = models.FileField(upload_to='lms_content/', blank=True, null=True)  # For PDF or Video
    text = models.TextField(blank=True, null=True)  # For textual content
    external_link = models.URLField(blank=True, null=True)  # For YouTube or other resources
    is_visible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.content_type})"


#lib

from django.db import models
from django.utils.text import slugify

class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)



#exam type

from django.db import models

class ExamType(models.Model):
    title = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


#CollegeStartEndPlan

# models.py
from django.db import models
from master.models import CourseType, Course

class CollegeStartEndPlan(models.Model):
    program_type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=20)  # Batch
    course = models.ForeignKey(Course, on_delete=models.CASCADE)  # Combination
    semester_number = models.PositiveIntegerField()

    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('program_type', 'academic_year', 'course', 'semester_number')

    def __str__(self):
        return f"{self.course.name} - {self.academic_year} (Sem {self.semester_number})"




from django.db import models
from master.models import Course, CourseType, AcademicYear, Employee, Semester  # Assuming Employee is your Faculty model

class ClassTeacher(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    program_type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Employee, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('academic_year', 'program_type', 'course', 'semester')  # One class teacher per class

    def __str__(self):
        return f"{self.faculty} - {self.course.name} Sem {self.semester}"
