
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

from admission.models import ConfirmedAdmission
from master.models import StudentDatabase

def parent_context(request):
    """
    Context processor to provide logged_in_parent, student, and parent_name
    to all templates (sidebar/topbar) for the parent portal.
    """
    parent_userid = request.COOKIES.get('parent_userid')
    confirmed = None
    student = None
    parent_name = None

    if parent_userid:
        try:
            confirmed = ConfirmedAdmission.objects.get(parent_userid=parent_userid)

            # linked student
            student = StudentDatabase.objects.filter(student_userid=confirmed.student_userid).first()

            # --- Parent Name logic based on primary_guardian ---
            if confirmed.pu_admission:
                pu = confirmed.pu_admission
                if pu.primary_guardian == "father":
                    parent_name = pu.father_name
                elif pu.primary_guardian == "mother":
                    parent_name = pu.mother_name
                elif pu.primary_guardian == "guardian":
                    parent_name = pu.guardian_name
            elif confirmed.degree_admission:
                deg = confirmed.degree_admission
                if deg.primary_guardian == "father":
                    parent_name = deg.father_name
                elif deg.primary_guardian == "mother":
                    parent_name = deg.mother_name
                elif deg.primary_guardian == "guardian":
                    parent_name = deg.guardian_name

        except ConfirmedAdmission.DoesNotExist:
            pass

    return {
        'logged_in_parent': confirmed,
        'student': student,
        'parent_name': parent_name,
    }
