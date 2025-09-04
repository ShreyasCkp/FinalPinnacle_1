from django.db import models
import os
from django.utils.text import slugify

def assignment_upload_path(instance, filename):
    course_name = slugify(instance.subject.name) if instance.course else "unknown-course"
    return os.path.join('assignments', course_name, filename)

from django.db import models
from master.models import Course, Subject, CourseType,Employee , ExamType
from timetable.models import TimeSlot
import os
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_delete
import shutil

class Assignment(models.Model):
    program_type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=20)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester_number = models.PositiveIntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True)
    faculty = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)  # <-- NEW field
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    marks = models.PositiveIntegerField()

    attachment = models.FileField(upload_to=assignment_upload_path, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.subject.name}"


@receiver(post_delete, sender=Assignment)
def delete_assignment_file_and_folder(sender, instance, **kwargs):
    if instance.attachment:
        file_path = instance.attachment.path
        if os.path.isfile(file_path):
            os.remove(file_path)

            # Get the directory where the file was saved
            folder = os.path.dirname(file_path)

            # Check and delete folder if it's empty
            if not os.listdir(folder):  # Folder is empty
                try:
                    os.rmdir(folder)
                except OSError:
                    pass  # Folder not empty or can't be removed


#lib
# models.py
from django.db import models
from master.models import BookCategory
 
 
class Book(models.Model):
    title = models.CharField(max_length=255)
    authors = models.CharField(max_length=255)
    category = models.ForeignKey(BookCategory, on_delete=models.SET_NULL, null=True)
    publication_date = models.DateField()
    edition = models.CharField(max_length=50, blank=True)
    available_copies = models.PositiveIntegerField(default=1)
    summary = models.TextField(blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=13, unique=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords")
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    link_pass = models.URLField(max_length=500, blank=True, help_text="Optional link related to the book")

    # models.py
    STATUS_CHOICES = [
        ('active', 'Available'),
        ('inactive', 'Unavailable'),
    ]
 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
 
    def __str__(self):
        return self.title
 


from master.models import StudentDatabase  # Updated import

class BorrowRecord(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentDatabase, on_delete=models.CASCADE)  # Updated foreign key
    borrow_date = models.DateField(auto_now_add=True)
    return_due_date = models.DateField()
    returned = models.BooleanField(default=False)
    return_date = models.DateField(null=True, blank=True)  # add this field

    def __str__(self):
        return f"{self.student.student_name} borrowed {self.book.title}"

    def save(self, *args, **kwargs):
    # Only run logic if this is a new borrow (i.e. not already saved)
        if not self.pk:
            self.book.available_copies -= 1  # Reduce one copy on borrow
            if self.book.available_copies <= 0:
                self.book.status = 'inactive'
            self.book.save()
    
        super().save(*args, **kwargs)



#this is pdf 

# lms/models.py

# models.py
from django.db import models
from master.models import Course, Subject, CourseType, Employee
import os
from django.utils.text import slugify

def study_material_upload_path(instance, filename):
    subject_name = slugify(instance.subject.name) if instance.subject else "unknown-subject"
    return os.path.join('study_materials', subject_name, filename)

class EmployeeStudyMaterial(models.Model):
    MATERIAL_TYPES = [
        ('pdf', 'PDF'),
        ('link', 'Link'),
        ('ebook', 'Ebook'),
        ('video', 'Video'),
    ]

    program_type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=20)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester_number = models.PositiveIntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    faculty = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPES)
    attachment = models.FileField(upload_to=study_material_upload_path, blank=True, null=True)
    link_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.subject.name})"


#This is exam
from django.db import models
from master.models import CourseType, Course, Subject, Employee , ExamType 

class Exam(models.Model):
    program_type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=20)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester_number = models.PositiveIntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)  # <-- NEW field
    exam_title = models.CharField(max_length=255, null=True, blank=True)
    exam_date = models.DateField()
    duration_minutes = models.PositiveIntegerField()  # store as integer (e.g., minutes)
    marks = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.exam_title} - {self.subject.name}"





class AssignmentSubmission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('review', 'Under Review'),
        ('graded', 'Graded'),
        ('rejected', 'Rejected'),
    ]


    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student_userid = models.CharField(max_length=50)
    submitted_file = models.FileField(upload_to='submissions/', blank=True, null=True)
    submitted_on = models.DateTimeField(auto_now_add=True)

    student_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    faculty_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Submission by {self.student_userid} for {self.assignment.title}"


from django.db import models
from master.models import StudentDatabase, Subject, Course, CourseType, Employee, ExamType

class StudentExamMarks(models.Model):
    program_type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=20)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester_number = models.PositiveIntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    faculty = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)

    student = models.ForeignKey(StudentDatabase, on_delete=models.CASCADE)

    # Instead of choices, use a ForeignKey to ExamType
    mark_type = models.ForeignKey(ExamType, on_delete=models.SET_NULL, null=True)

    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject', 'mark_type', 'academic_year')

    def __str__(self):
        return f"{self.student.student_name} - {self.subject.name} ({self.mark_type})"



from django.db import models
from master.models import StudentDatabase  # Assuming you already have a Student model
import os
from django.utils.text import slugify

def certificate_upload_path(instance, filename):
    student_slug = slugify(instance.student.student_name)
    return os.path.join('certificates', student_slug, filename)

class Certificate(models.Model):
    student = models.ForeignKey(StudentDatabase, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=certificate_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.student.student_name}"


from django.db import models
from lms.models import Assignment, BorrowRecord  # adjust imports as needed
from fees.models import StudentFeeCollection
from lms.models import Exam

class CalendarEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)

    # Foreign keys to link specific models (nullable so not all required)
    assignment = models.ForeignKey(Assignment, null=True, blank=True, on_delete=models.CASCADE)
    borrow_record = models.ForeignKey(BorrowRecord, null=True, blank=True, on_delete=models.CASCADE)
    student_fee = models.ForeignKey(StudentFeeCollection, null=True, blank=True, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, null=True, blank=True, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.date}"


# lms/models.py
from django.db import models
from master.models import StudentDatabase, Employee

class StudentLeave(models.Model):
    LEAVE_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled'),
    ('cancelled', 'Cancelled'),
    ]

    student = models.ForeignKey(StudentDatabase, on_delete=models.CASCADE)
    reason = models.TextField()
    from_date = models.DateField()
    to_date = models.DateField()
    status = models.CharField(max_length=10, choices=LEAVE_STATUS, default='pending')
    applied_on = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    is_seen_by_teacher = models.BooleanField(default=False)
    # ? Key field to track which class teacher should review this
    class_teacher = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        name = self.student.student_name if self.student else "Unknown Student"
        return f"{name} ({self.from_date} to {self.to_date})"

    class Meta:
        ordering = ['-applied_on']



# lms/models.py
from django.db import models

class FinalExamMarks(models.Model):
    program_type = models.ForeignKey('master.CourseType', on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.ForeignKey('master.AcademicYear', on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey('master.Course', on_delete=models.CASCADE, null=True, blank=True)
    sem_year = models.PositiveIntegerField(null=True, blank=True)

    student = models.ForeignKey('master.StudentDatabase', on_delete=models.CASCADE)
    subject = models.ForeignKey('master.Subject', on_delete=models.CASCADE)

    assignment = models.ForeignKey(
        'lms.Assignment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exam_marks"
    )

    internal_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    internal_obtained = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    max_marks = models.PositiveIntegerField(default=75)   # external max
    marks_obtained = models.PositiveIntegerField(null=True, blank=True)  # external obtained
    grade = models.CharField(max_length=5, null=True, blank=True)

    @property
    def final_obtained(self):
        internal = self.internal_obtained or 0
        external = self.marks_obtained or 0
        return internal + external

    def __str__(self):
        return f"{self.student.student_name} - {self.subject.name}"



# lms/models.py

from django.db import models
from master.models import StudentDatabase

class StudentNotification(models.Model):
    student = models.ForeignKey(StudentDatabase, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    url = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return f"Notification for {self.student.student_name}: {self.title}"