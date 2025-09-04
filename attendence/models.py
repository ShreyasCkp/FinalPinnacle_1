from django.db import models
from django.db import models
from master.models import Employee  # Adjust if Employee is in another app

class attendancesettings(models.Model):
    check_in_time = models.TimeField(default="09:00")
    grace_period = models.IntegerField(default=15)  # in minutes
    late_threshold = models.IntegerField(default=40)  # in minutes

    class Meta:
        db_table = 'attendence_attendancesettings'

import datetime

from django.db import models
import datetime

from master.models import Employee
from .models import attendancesettings  # Ensure this is correct

class attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in = models.TimeField()
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20)  # 'Present', 'Late', 'Absent'
    lop = models.BooleanField(default=False)  # Checkbox in admin/form

    def save(self, *args, **kwargs):
        settings = attendancesettings.objects.first()
        if settings and self.check_in:
            check_in_time = datetime.datetime.combine(self.date, settings.check_in_time)
            actual = datetime.datetime.combine(self.date, self.check_in)
            diff = (actual - check_in_time).total_seconds() / 60
            if diff <= settings.grace_period:
                self.status = "Present"
            elif diff <= settings.late_threshold:
                self.status = "Late"
            else:
                self.status = "Absent"
        else:
            self.status = "Absent"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.name} - {self.date}"



from django.db import models
from master.models import StudentDatabase, Subject,Course , CourseType
from timetable.models import TimeSlot

class StudentAttendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('late', 'Late'),
        ('absent', 'Absent'),
    ]
    admission_number = models.CharField(max_length=50, blank=True, null=True)  # NEW FIELD
    program_type = models.ForeignKey(CourseType, on_delete=models.SET_NULL, null=True, blank=True)  # NEW FIELD

    student = models.ForeignKey(StudentDatabase, on_delete=models.CASCADE)
    student_userid = models.CharField(max_length=50, blank=True, null=True)
    student_name = models.CharField(max_length=100, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    semester_number = models.PositiveIntegerField(null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True)
    faculty = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    attendance_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    # time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True)  # ✅ New field
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    academic_year = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'subject', 'attendance_date','time_slot')
 
    def __str__(self):
        return f"{self.student.student_name} - {self.subject.name} (Sem {self.semester_number}) on {self.attendance_date}: {self.status}"
 

