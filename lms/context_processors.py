
from admission.models import ConfirmedAdmission

def student_context(request):
    student_id = request.COOKIES.get('student_id')
    student = None

    if student_id:
        try:
            student = ConfirmedAdmission.objects.get(id=student_id)
        except ConfirmedAdmission.DoesNotExist:
            pass

    return {
        'logged_in_student': student
    }

from master.models import Employee

def employee_context(request):
    employee_id = request.COOKIES.get('employee_id')
    employee = None

    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            pass

    return {
        'logged_in_employee': employee
    }