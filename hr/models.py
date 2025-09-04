from django.db import models



class HolidayCalendar(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Independence Day"
    date = models.DateField(unique=True)
    holiday_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Public Holiday"
    is_working_day = models.BooleanField(default=False)  # True if celebration day but still working

    def __str__(self):
        return f"{self.name} ({self.date})"



from datetime import timedelta
from master.models import Employee


class Leave(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('CL', 'Casual Leave'),
        ('SL', 'Sick Leave / Medical Leave'),
        ('EL', 'Earned Leave / Privilege Leave'),
        ('LOP', 'Loss of Pay / Unpaid Leave'),
        ('ML', 'Maternity Leave'),
        ('PL', 'Paternity Leave'),
        ('BL', 'Bereavement / Compassionate Leave'),
        ('Marriage', 'Marriage Leave'),
        ('Sabbatical', 'Sabbatical / Study Leave'),
        ('Optional', 'Optional / Privilege Holiday'),
        ('CO', 'Compensatory Off / Comp Off'),
        ('Volunteer', 'Volunteer / CSR Leave'),
        ('WFH', 'Work From Home Days'),
        ('Adoption', 'Adoption Leave'),
        ('Special', 'Special Leave / Festival Leave'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    admin_reason = models.TextField(blank=True, null=True)

    # Calculated fields
    leave_days = models.PositiveIntegerField(default=0)
    next_working_day = models.DateField(null=True, blank=True)

    approved_by = models.CharField(max_length=150, null=True, blank=True)
    is_approved = models.BooleanField(null=True, blank=True, default=None)
    applied_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hr_leave'

    def __str__(self):
        return f"{self.employee.name} - {self.leave_type}"

    def save(self, *args, **kwargs):
        # Calculate total leave days
        if self.start_date and self.end_date:
            self.leave_days = (self.end_date - self.start_date).days + 1

        # Calculate next working day (skip weekends)
        if self.end_date:
            next_day = self.end_date + timedelta(days=1)
            while next_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
                next_day += timedelta(days=1)
            self.next_working_day = next_day

        super().save(*args, **kwargs)



from django.db import models
from master.models import Employee
from django.db import models


class EmployeeSalaryDeclaration(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_declarations')

    # Auto-filled Employee info
    emp_code = models.CharField(max_length=10, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=50, blank=True, null=True)
    employment_type = models.CharField(max_length=20, blank=True, null=True)
    category = models.CharField(max_length=30, blank=True, null=True)
    role = models.CharField(max_length=20, blank=True, null=True)

    # Earnings & Allowances
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Deductions (manual)
    professional_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lwf_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    income_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Auto-calculated fields
    hra = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # 40% of basic
    pf_contribution = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # 12% of basic
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.employee:
            self.emp_code = self.employee.emp_code
            self.name = self.employee.name
            self.designation = self.employee.designation
            self.employment_type = self.employee.employment_type
            self.category = self.employee.category
            self.role = self.employee.role

        # Auto calculate HRA & PF
        self.hra = (self.basic_salary * 40) / 100
        self.pf_contribution = (self.basic_salary * 12) / 100

        # Gross salary
        self.gross_salary = self.basic_salary + self.hra + self.special_allowance

        # Total deductions
        self.total_deductions = self.pf_contribution + self.professional_tax + self.lwf_contribution + self.income_tax

        # Net pay
        self.net_pay = self.gross_salary - self.total_deductions

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.name} - Declaration"



# models.py
from django.db import models

class EmployeeSalarySlip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    total_days = models.IntegerField(default=0)
    present_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    lop_days = models.IntegerField(default=0)
    salary_deduction = models.FloatField(default=0)
    final_salary = models.FloatField(default=0)

    
    net_pay_in_words = models.CharField(max_length=255, blank=True, null=True)

    # Snapshots of employee info at the time
    emp_code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    uan_number = models.CharField(max_length=12, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    aadhaar_number = models.CharField(max_length=12, blank=True, null=True)
    pf_number = models.CharField(max_length=50, blank=True, null=True)
    pension_no = models.CharField(max_length=50, blank=True, null=True)
    esi_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    bank_account_number = models.CharField(max_length=30, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("employee", "month", "year")

    def __str__(self):
        return f"{self.employee.name} - {self.month}/{self.year}"

