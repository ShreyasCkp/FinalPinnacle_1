from django.db import models
from master.models  import AcademicYear,CourseType,Course,FeeType

class FeeDeclaration(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    course_type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.IntegerField(null=True, blank=True)
    current_year = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f"{self.academic_year.year} - {self.course.name} - Sem {self.semester or self.current_year}"
 
class FeeDeclarationDetail(models.Model):
    declaration = models.ForeignKey(FeeDeclaration, related_name='fee_details', on_delete=models.CASCADE)
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
 
    def __str__(self):
        return f"{self.fee_type.name} - {self.amount}"


    from django.db import models

from master.models import FeeType,StudentDatabase

class OptionalFee(models.Model):
    student = models.ForeignKey(StudentDatabase, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=200)
    admission_no = models.CharField(max_length=100)
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()

    def __str__(self):
        return f"{self.student_name} - {self.fee_type.name} - ₹{self.amount}"







class StudentFeeCollection(models.Model):
    admission_no = models.CharField(max_length=30)
    due_date = models.DateField(null=True, blank=True)
    student_userid = models.CharField(max_length=50, blank=True, null=True)
    academic_year = models.CharField(max_length=9)
    semester = models.IntegerField(null=True, blank=True)
    fee_type = models.ForeignKey('master.FeeType', on_delete=models.CASCADE)
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
    applied_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    receipt_no = models.CharField(max_length=100, null=True, blank=True, unique=True)
    receipt_date = models.DateField(null=True, blank=True)  

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
        return f"{self.admission_no} - {self.fee_type.fee_name} - {self.status}"