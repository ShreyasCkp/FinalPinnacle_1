from django.shortcuts import render
from admission.models import ConfirmedAdmission

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from admission.models import ConfirmedAdmission
from django.http import HttpResponseRedirect
from django.urls import reverse

def student_login_view(request):
    context = {}

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        context['selected_user'] = username

        try:
            student = ConfirmedAdmission.objects.get(student_userid=username)

            if student.is_locked:
                context['error'] = "Account is locked due to multiple failed attempts. Contact admin."
                return render(request, 'lms/student_login.html', context)

            if student.student_password != password:
                student.wrong_attempts += 1
                if student.wrong_attempts >= 3:
                    student.is_locked = True
                student.save()
                context['error'] = "Invalid password."
                return render(request, 'lms/student_login.html', context)

            # Reset wrong attempts on success
            student.wrong_attempts = 0
            student.save()

            # Determine redirect URL first
            if not student.password_changed:
                redirect_url = reverse('student_set_password')
            elif not student.passcode_set:
                redirect_url = reverse('student_set_passcode')
            else:
                redirect_url = reverse('student_dashboard')

            # Create response and set cookies
            response = HttpResponseRedirect(redirect_url)
            response.set_cookie('student_id', student.id)
            response.set_cookie('student_userid', student.student_userid)
            response.set_cookie('student_name', student.student_name)


            return response

        except ConfirmedAdmission.DoesNotExist:
            context['error'] = "Invalid credentials."

    return render(request, 'lms/student_login.html', context)


def student_logout(request):
    request.session.flush()
    response = redirect('student_login_view')
    response.delete_cookie('student_id')
    response.delete_cookie('student_userid')
    response.delete_cookie('student_name')
    return response


def student_set_password(request):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    student = ConfirmedAdmission.objects.get(student_userid=student_userid)
    error = None

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            error = "Passwords do not match."
        elif len(new_password) < 8:
            error = "Password must be at least 8 characters."
        else:
            student.student_password = new_password
            student.password_changed = True
            student.save()
            return redirect('student_set_passcode')

    return render(request, 'lms/student_set_password.html', {
        'error': error,
        'selected_user': student.student_userid  # or student.username or however you call it
    })



def student_set_passcode(request):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    student = ConfirmedAdmission.objects.get(student_userid=student_userid)
    error = None

    if request.method == 'POST':
        passcode = request.POST.get('passcode')

        if not passcode.isdigit() or len(passcode) < 4:
            error = "Passcode must be at least 4 digits."
        else:
            student.passcode = passcode
            student.passcode_set = True
            student.save()
            return redirect('student_dashboard')

    return render(request, 'lms/student_set_passcode.html', {'error': error})




from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Avg, Count
from datetime import timedelta

from lms.models import (
    Assignment,
    AssignmentSubmission,
    StudentExamMarks,
    Exam,
    StudentNotification  # ✅ Import notification model
)
from master.models import StudentDatabase, CollegeStartEndPlan
from admission.models import ConfirmedAdmission
from attendence.models import StudentAttendance  # ✅ Make sure this import is correct

def student_dashboard(request):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    try:
        confirmed_student = ConfirmedAdmission.objects.get(student_userid=student_userid)
        student = StudentDatabase.objects.get(student_userid=student_userid)
    except ConfirmedAdmission.DoesNotExist:
        return redirect('student_login_view')

    # === Academic Info ===
    academic_year = student.academic_year
    course_type = student.course_type
    course = student.course
    semester = student.semester or student.current_year

    # === Assignments ===
    assignments = Assignment.objects.filter(
        academic_year=academic_year,
        program_type=course_type,
        course=course,
        semester_number=semester
    )

    submissions = AssignmentSubmission.objects.filter(
        student_userid=student_userid,
        assignment__in=assignments
    )
    submissions_dict = {sub.assignment_id: sub for sub in submissions}
    submitted_ids = set(submissions_dict.keys())

    pending_assignments = sum(1 for a in assignments if a.id not in submitted_ids)

    # Assignments due this week
    today = timezone.now().date()
    end_week = today + timedelta(days=7)
    due_this_week = assignments.filter(due_date__range=(today, end_week)).count()

    # === GPA / Score ===
    average_score = submissions.filter(student_status='graded').aggregate(
        avg_score=Avg('score')
    )['avg_score'] or 0.0

    # === Attendance Calculation ===
    try:
        plan = CollegeStartEndPlan.objects.get(
            program_type=course_type,
            academic_year=academic_year,
            course=course,
            semester_number=semester
        )

        start_date = plan.start_date
        end_date = min(plan.end_date, today)

        attendance_qs = StudentAttendance.objects.filter(
            student=student,
            course=course,
            semester_number=semester,
            academic_year=academic_year,
            attendance_date__range=(start_date, end_date)
        )

        total_sessions = attendance_qs.count()
        attended_sessions = attendance_qs.filter(status__in=['present', 'late']).count()
        attendance_rate = round((attended_sessions / total_sessions) * 100, 2) if total_sessions > 0 else 0.0

    except CollegeStartEndPlan.DoesNotExist:
        attendance_rate = 0.0

    # === Notifications ===
    notifications = []

    # 📝 Assignment Notifications
    assignments_due = assignments.filter(due_date__gte=today).annotate(
        submitted_count=Count('submissions')
    )
    assignment_notifications = assignments_due.filter(submitted_count=0)

    for assignment in assignment_notifications:
        notifications.append({
            'type': 'assignment',
            'title': f"Assignment due on {assignment.due_date.strftime('%d %b')}",
            'url': '/student/assignments/',
        })

    # 📘 Exam Notifications
    exam_notifications = Exam.objects.filter(
        course=course,
        exam_date__range=(today, today + timedelta(days=30))
    )

    for exam in exam_notifications:
        days_until_exam = (exam.exam_date - today).days
        if days_until_exam in [7, 30]:
            label = f"{exam.subject.name} exam on {exam.exam_date.strftime('%d %b')} (in {days_until_exam} days)"
        else:
            label = f"{exam.subject.name} exam on {exam.exam_date.strftime('%d %b')}"
        notifications.append({
            'type': 'exam',
            'title': label,
            'url': '/student/grades/',
        })

    # 🔔 Leave Notifications (from faculty)
   # 🔔 Leave Notifications (from faculty)
    leave_notifications = StudentNotification.objects.filter(
    student=student,
    is_read=False
    ).order_by('-created_at')[:5]


    for note in leave_notifications:
        notifications.append({
            'type': 'leave',
            'title': note.title,
            'message': note.message,
            'url': f'/student/notification/read/{note.id}/',  # ✅ This won't change
        })



    # === Final Context ===
    context = {
        'student': student,
        'pending_assignments': pending_assignments,
        'due_this_week': due_this_week,
        'current_gpa': round(average_score, 2),
        'attendance_rate': attendance_rate,
        'notifications': notifications,
        'notification_count': len(notifications),
    }

    return render(request, 'lms/student_dashboard.html', context)

 
from django.shortcuts import get_object_or_404, redirect
from lms.models import StudentNotification

def mark_notification_as_read(request, notification_id):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    notification = get_object_or_404(StudentNotification, id=notification_id)

    # ✅ Check ownership
    if notification.student.student_userid != student_userid:
        return redirect('student_dashboard')

    # ✅ Mark as read
    notification.is_read = True
    notification.save()

    # ✅ Redirect to the actual leave list page
    return redirect('/student/leave/list/')





def student_change_password(request):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    student = ConfirmedAdmission.objects.get(student_userid=student_userid)
    error = None
    success = None

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if old_password != student.student_password:
            error = "Old password is incorrect."
        elif new_password != confirm_password:
            error = "New passwords do not match."
        elif len(new_password) < 8:
            error = "New password must be at least 8 characters."
        else:
            student.student_password = new_password
            student.save()
            success = "Password updated successfully."

    return render(request, 'lms/student_change_password.html', {
        'error': error,
        'success': success
    })
def student_change_passcode(request):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    student = ConfirmedAdmission.objects.get(student_userid=student_userid)
    error = None
    success = None

    if request.method == 'POST':
        old_passcode = request.POST.get('old_passcode')
        new_passcode = request.POST.get('new_passcode')
        confirm_passcode = request.POST.get('confirm_passcode')

        if old_passcode != student.passcode:
            error = "Old passcode is incorrect."
        elif new_passcode != confirm_passcode:
            error = "New passcodes do not match."
        elif not new_passcode.isdigit() or len(new_passcode) < 4:
            error = "New passcode must be at least 4 digits."
        else:
            student.passcode = new_passcode
            student.save()
            success = "Passcode updated successfully."

    return render(request, 'lms/student_change_passcode.html', {
        'error': error,
        'success': success
    })

# from django.shortcuts import render, redirect
# from django.utils import timezone 
# from django.db.models import Avg, Q
# from datetime import timedelta

# from lms.models import Assignment, AssignmentSubmission, StudentExamMarks
# from master.models import StudentDatabase
# from admission.models import ConfirmedAdmission
# def student_dashboard(request):
#     student_userid = request.COOKIES.get('student_userid')
#     if not student_userid:
#         return redirect('student_login_view')

#     try:
#         confirmed_student = ConfirmedAdmission.objects.get(student_userid=student_userid)
#         student = StudentDatabase.objects.get(student_userid=student_userid)
#     except ConfirmedAdmission.DoesNotExist:
#         return redirect('student_login_view')

#     # Fetch academic info
#     academic_year = student.academic_year
#     course_type = student.course_type
#     course = student.course
#     semester = student.semester or student.current_year

#     # --- Assignments ---
#     assignments = Assignment.objects.filter(
#         academic_year=academic_year,
#         program_type=course_type,
#         course=course,
#         semester_number=semester
#     )

#     submissions = AssignmentSubmission.objects.filter(
#         student_userid=student_userid,
#         assignment__in=assignments
#     )
#     submissions_dict = {sub.assignment_id: sub for sub in submissions}
#     submitted_ids = set(submissions_dict.keys())

#     pending_assignments = sum(1 for a in assignments if a.id not in submitted_ids)

#     # Assignments due this week
#     today = timezone.now().date()
#     end_week = today + timedelta(days=7)
#     due_this_week = assignments.filter(due_date__range=(today, end_week)).count()

#     # --- GPA / Score ---
#     average_score = submissions.filter(status='graded').aggregate(
#         avg_score=Avg('score')
#     )['avg_score'] or 0.0

#     # --- Attendance Rate (Placeholder) ---
#     attendance_rate = 0  # Assuming not implemented yet

#     context = {
#         'student': student,
#         'pending_assignments': pending_assignments,
#         'due_this_week': due_this_week,
#         'current_gpa': round(average_score, 2),
#         'attendance_rate': attendance_rate,
#     }

#     return render(request, 'lms/student_dashboard.html', context)



def student_password_reset_view(request):
    context = {}
    username = request.GET.get('username') or request.POST.get('username')
    context['selected_user'] = username
    context['reset'] = True  # Tell the template we're in reset mode

    if request.method == 'POST':
        try:
            student = ConfirmedAdmission.objects.get(student_userid=username)
        except ConfirmedAdmission.DoesNotExist:
            context['error'] = "User does not exist."
            return render(request, 'lms/student_login.html', context)

        # Step 1: Verify passcode
        if 'verify_passcode' in request.POST:
            input_passcode = request.POST.get('passcode', '').strip()
            if not student.passcode_set or student.passcode != input_passcode:
                context['error'] = "Incorrect passcode."
            else:
                context['passcode_verified'] = True  # Show new password fields

        # Step 2: Reset password after passcode verified
        elif 'password_reset_submit' in request.POST:
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()

            import re
            pattern = r'^[A-Z][a-z]*[!@#$%^&*(),.?":{}|<>][a-zA-Z0-9]*[0-9]+$'

            if new_password != confirm_password:
                context['error'] = "Passwords do not match."
                context['passcode_verified'] = True  # keep showing reset form
            elif not re.match(pattern, new_password) or not (8 <= len(new_password) <= 16):
                context['error'] = "Invalid password format."
                context['passcode_verified'] = True
            else:
                student.student_password = new_password
                student.password_changed = True
                student.save()
                context['success_message'] = "Password reset successfully."
                return redirect('student_login_view')

    return render(request, 'lms/student_login.html', context)

from django.shortcuts import render, redirect
from django.utils.timezone import localtime  
from master.models import StudentDatabase
from attendence.models import StudentAttendance
from datetime import date  
from timetable.models import TimetableEntry
from master.models import AcademicYear  



def my_attendance_view(request):
    student_userid = request.COOKIES.get('student_userid')
   

    if not student_userid:
        
        return redirect('student_login_view')

    try:
        confirmed_student = ConfirmedAdmission.objects.get(student_userid=student_userid)
        student = StudentDatabase.objects.get(student_userid=student_userid)
        
    except (ConfirmedAdmission.DoesNotExist, StudentDatabase.DoesNotExist):
        
        return redirect('student_login_view')

    today_date = localtime().date()
    today_day = today_date.strftime('%A')  # e.g. 'Thursday'
   

    # Student course details
    course = student.course
    course_type = student.course_type
    

    # Convert academic_year string to FK object
    try:
        academic_year_obj = AcademicYear.objects.get(year=student.academic_year)
        
    except AcademicYear.DoesNotExist:
       
        academic_year_obj = None

    # Choose semester or year
    if course_type and 'puc' in course_type.name.lower():

        semester_or_year = student.current_year
        
    else:
        semester_or_year = student.semester
       

    # Fetch today's scheduled classes from timetable
    today_schedule = TimetableEntry.objects.filter(
        day=today_day,
        course=course,
        course_type=course_type,
        semester_number=semester_or_year,
        academic_year=academic_year_obj
    )



    total_records = today_schedule.count()

    # Attendance records for today
    today_attendance = StudentAttendance.objects.filter(
        student=student,
        attendance_date=today_date
    ).select_related('subject', 'faculty', 'course')

   

    present_today = today_attendance.filter(status='present').count()
    late_today = today_attendance.filter(status='late').count()
    absent_today = today_attendance.filter(status='absent').count()
    attended_today = present_today + late_today

   

    attendance_rate = round((attended_today / total_records) * 100, 2) if total_records > 0 else 0
  

    context = {
        'total_records': total_records,
        'present_today': present_today,
        'late_today': late_today,
        'absent_today': absent_today,
        'attendance_rate': attendance_rate,
        'today_records': today_attendance,
    }
    return render(request, 'lms/my_attendance.html', context)


from django.shortcuts import render, redirect
from datetime import date
from fees.models import StudentFeeCollection
from django.db import models
# Import your models here
from django.utils.timezone import localtime

from django.shortcuts import render, redirect
from datetime import date

from django.db.models import Sum, Case, When, Value, CharField

from django.db.models import Max, Subquery, OuterRef

from django.shortcuts import render, redirect
from datetime import date
from django.db import models
from django.db.models import OuterRef, Subquery, Max
from fees.models import StudentFeeCollection


from collections import defaultdict
from decimal import Decimal





def my_fees_view(request):
    student_userid = request.COOKIES.get('student_userid')

    if not student_userid:
        return redirect('student_login_view')

    try:
        confirmed_student = ConfirmedAdmission.objects.get(student_userid=student_userid)
        student = StudentDatabase.objects.get(student_userid=student_userid)
    except (ConfirmedAdmission.DoesNotExist, StudentDatabase.DoesNotExist):
        return redirect('student_login_view')

    # Fetch all fee records for the student
    all_fees = StudentFeeCollection.objects.filter(student_userid=student_userid)

    grouped_fees = defaultdict(list)
    for fee in all_fees:
        key = (fee.fee_type_id, fee.due_date)
        grouped_fees[key].append(fee)

    fee_display_list = []
    total_fees = Decimal('0')
    total_collected = Decimal('0')
    total_pending = Decimal('0')
    total_overdue = Decimal('0')
    overdue_fee_types = set()
    today = date.today()

    for (fee_type_id, due_date), records in grouped_fees.items():
        latest_record = max(records, key=lambda x: x.id)
        amount = latest_record.amount  # assumed same for all grouped records
        total_paid = sum(r.paid_amount for r in records)
        total_discount = sum(getattr(r, 'applied_discount', Decimal('0')) for r in records)
        balance = amount - total_paid - total_discount

        if balance <= 0:
            status = 'Paid'
            balance = Decimal('0')
        elif total_paid > 0:
            status = 'Partial'
        else:
            status = 'Pending'

        if balance > 0 and due_date < today:
            total_overdue += balance
            overdue_fee_types.add(latest_record.fee_type.name)  # Collect overdue fee type names

        total_fees += amount
        total_collected += total_paid
        total_pending += balance

        fee_display_list.append({
            'id': latest_record.id,
            'fee_type': latest_record.fee_type,
            'due_date': latest_record.due_date,
            'amount': amount,
            'paid_amount': total_paid,
            'balance_amount': balance,
            'status': status,
            'applied_discount': total_discount,
            'total_paid': total_paid + total_discount,
        })

    fee_display_list.sort(key=lambda x: x['due_date'])

    context = {
        'fee_collections': fee_display_list,
        'total_fees': total_fees,
        'collected': total_collected,
        'pending': total_pending,
        'overdue': total_overdue,
        'overdue_fee_types': sorted(overdue_fee_types),  # pass sorted list to template
    }

    return render(request, 'lms/my_fee.html', context)




from django.shortcuts import render, redirect

def student_profile_view(request):
    student_userid = request.COOKIES.get('student_userid')

    if not student_userid:
        return redirect('student_login_view')

    try:
        # Get ConfirmedAdmission record
        confirmed_student = ConfirmedAdmission.objects.get(student_userid=student_userid)
        student_entry = StudentDatabase.objects.get(student_userid=student_userid)
      
    except (ConfirmedAdmission.DoesNotExist, StudentDatabase.DoesNotExist):
        return redirect('student_login_view')

    # Determine linked admission (PU or Degree)
    if student_entry.pu_admission:
        admission = student_entry.pu_admission
    elif student_entry.degree_admission:
        admission = student_entry.degree_admission
    else:
        # No linked admission found, redirect or handle as needed
        return redirect('student_login_view')

    context = {
        'confirmed_student': confirmed_student,
        'admission': admission,
        'student': student_entry,  # For template consistency
    }

    return render(request, 'lms/my_profile.html', context)



#change
from .models import Assignment, AssignmentSubmission
from django.db.models import Avg, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from master.models import StudentDatabase
from django.db.models import Sum

from .models import Assignment, AssignmentSubmission
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.utils import timezone
from master.models import StudentDatabase

def my_assignments_view(request):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    try:
        student = StudentDatabase.objects.get(student_userid=student_userid)
    except StudentDatabase.DoesNotExist:
        return redirect('student_login_view')

    academic_year = student.academic_year
    course_type = student.course_type
    course = student.course
    semester = student.semester or student.current_year

    # Get all relevant assignments
    assignments = Assignment.objects.filter(
        academic_year=academic_year,
        program_type=course_type,
        course=course,
        semester_number=semester
    ).order_by('-due_date')

    # Fetch all submissions for those assignments by this student
    submissions = AssignmentSubmission.objects.filter(
        student_userid=student_userid,
        assignment__in=assignments
    )

    # ✅ Auto-grade: If score is given and status is not 'graded', update it
    # Auto-grade
    for sub in submissions:
        if sub.score is not None and sub.student_status != 'graded':
            sub.student_status = 'graded'
            sub.save(update_fields=['student_status'])

    # Refresh dict
    submissions_dict = {sub.assignment_id: sub for sub in submissions}
    submitted_assignment_ids = submissions_dict.keys()

    # Stats
    pending = sum(1 for a in assignments if a.id not in submitted_assignment_ids)
    submitted = sum(
        1 for a in assignments
        if submissions_dict.get(a.id) and submissions_dict[a.id].student_status == 'submitted'
    )
    graded = sum(
        1 for a in assignments
        if submissions_dict.get(a.id) and submissions_dict[a.id].student_status == 'graded'
    )

    # Calculate total max marks
    total_max_marks = assignments.aggregate(total=Sum('marks'))['total'] or 0

    # Total scored marks from graded submissions

    total_scored_marks = submissions.filter(student_status='graded').aggregate(total=Sum('score'))['total'] or 0

    # Calculate percentage
    percentage = (total_scored_marks / total_max_marks * 100) if total_max_marks > 0 else 0
    percentage = round(percentage, 2)
    context = {
        'assignments': assignments,
        'submitted_assignment_ids': submitted_assignment_ids,
        'submissions_dict': submissions_dict,
        'pending': pending,
        'submitted': submitted,
        'graded': graded,
        'percentage': percentage,
        'today': timezone.now().date(),
    }
    return render(request, 'lms/my_assignments.html', context)


#change


from django.views.decorators.http import require_http_methods
from django.http import HttpResponseForbidden
from .forms import AssignmentSubmissionForm  
from django.utils import timezone

@require_http_methods(["GET", "POST"])
def submit_assignment_view(request, assignment_id):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = get_object_or_404(StudentDatabase, student_userid=student_userid)

    submission, created = AssignmentSubmission.objects.get_or_create(
        student_userid=student_userid,
        assignment=assignment,
        defaults={'student_status': 'pending', 'faculty_status': 'pending'}
    )

    # Mark as in_progress when student downloads the assignment (optional: handle download view separately)
    # if 'download' in request.GET:
    #     submission.student_status = 'in_progress'
    #     submission.faculty_status = 'in_progress'
    #     submission.save()
    if 'download' in request.GET:
        submission.student_status = 'in_progress'
        # Faculty stays pending until student submits
        submission.save()

    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.student_status = 'submitted'
            submission.faculty_status = 'submitted'
            submission.submitted_on = timezone.now()
            submission.save()
            return redirect('my_assignments_view')
    else:
        form = AssignmentSubmissionForm(instance=submission)

    return render(request, 'lms/submit_assignment.html', {
        'form': form,
        'assignment': assignment,
    })




#change

#change

from lms.models import AssignmentSubmission  # Import this if not already

from core.utils import get_logged_in_user
from lms.models import AssignmentSubmission

def assignment_list(request):
    # Get logged-in faculty
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    # Only assignments created by this employee
    assignments = Assignment.objects.filter(faculty=employee).order_by('-due_date')

    # Apply GET filters
    program_type = request.GET.get('program_type')
    academic_year = request.GET.get('academic_year')
    course = request.GET.get('course')
    semester = request.GET.get('semester')
    subject = request.GET.get('subject')

    if program_type:
        assignments = assignments.filter(program_type_id=program_type)
    if academic_year:
        assignments = assignments.filter(academic_year=academic_year)
    if course:
        assignments = assignments.filter(course_id=course)
    if semester:
        assignments = assignments.filter(semester_number=semester)
    if subject:
        assignments = assignments.filter(subject_id=subject)

    assignment_data = []
    for assignment in assignments:
        submitted_count = AssignmentSubmission.objects.filter(
            assignment=assignment
        ).exclude(submitted_file__isnull=True).exclude(submitted_file='').count()


        # total_students = StudentDatabase.objects.filter(

        # Base queryset
        students_qs = StudentDatabase.objects.filter(

            course=assignment.course,
            academic_year=assignment.academic_year,
            course_type=assignment.program_type
        )

        # Different filter for PUC vs Degree
        if assignment.program_type.name.lower().startswith("puc"):
            students_qs = students_qs.filter(current_year=assignment.semester_number)
        else:  # Degree/UG
            students_qs = students_qs.filter(semester=assignment.semester_number)

        total_students = students_qs.count()

        assignment_data.append({
            'assignment': assignment,
            'submitted_count': submitted_count,
            'total_students': total_students,
        })


    context = {
        'assignment_data': assignment_data,
        'program_types': CourseType.objects.all(),
        'courses': Course.objects.all(),
        'subjects': Subject.objects.all(),
        'years': Assignment.objects.values_list('academic_year', flat=True).distinct(),
        'selected': {
            'program_type': program_type,
            'academic_year': academic_year,
            'course': course,
            'semester': semester,
            'subject': subject
        }
    }

    return render(request, 'lms/employee_assignments_list.html', context)




#change
#create 
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import AssignmentForm
from .models import Assignment, Assignment
from master.models import CourseType, Course, Subject, StudentDatabase
from core.utils import get_logged_in_user, log_activity

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import AssignmentForm
from .models import Assignment
from master.models import Course, Subject, CourseType, Employee, StudentDatabase, EmployeeSubjectAssignment


def create_assignment(request):
    # Authenticate employee from cookies
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    # Get filter values from GET request
    selected_program_type_id = request.GET.get('program_type')
    selected_academic_year = request.GET.get('academic_year')
    selected_course_id = request.GET.get('course')
    selected_semester_id = request.GET.get('semester')
    selected_subject_id = request.GET.get('subject')

    # 🔹 Get only assignments of this employee
    assignments = EmployeeSubjectAssignment.objects.filter(employee=employee).select_related('course', 'subject')

    # Distinct courses, subjects, semesters from assignments
    assigned_courses = {a.course.id: a.course for a in assignments}
    assigned_subjects = {a.subject.id: a.subject for a in assignments}
    course_semesters = {}
    for a in assignments:
        course_semesters.setdefault(a.course.id, set()).add(a.semester)

    # 🔹 Filter courses by program type
    filtered_courses = []
    for course in assigned_courses.values():
        if not selected_program_type_id or str(course.course_type_id) == selected_program_type_id:
            filtered_courses.append(course)

    # 🔹 Filter subjects by selected course
    filtered_subjects = []
    if selected_course_id and selected_semester_id:
         for a in assignments:
             if (
                 str(a.course.id) == selected_course_id and
                 str(a.semester) == selected_semester_id and
                 a.subject not in filtered_subjects
             ):
                 filtered_subjects.append(a.subject)

    # 🔹 Semester options
    semester_display = []
    if selected_course_id and int(selected_course_id) in course_semesters:
        course = assigned_courses[int(selected_course_id)]
        sem_list = sorted(course_semesters[int(selected_course_id)])
        semester_display = [{'id': sem, 'label': f"{course.name} {sem}"} for sem in sem_list]

    # 🔹 Academic years
    academic_years = []
    if selected_program_type_id:
        academic_years = (
            StudentDatabase.objects
            .filter(course__course_type_id=selected_program_type_id)
            .values_list('academic_year', flat=True)
            .distinct()
            .order_by('-academic_year')
        )

    # Form handling
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, faculty_queryset=Employee.objects.filter(id=employee.id))

        if form.is_valid():
            assignment = form.save(commit=False)

            # Require all filters
            if not (selected_program_type_id and selected_course_id and selected_semester_id and selected_subject_id):
                form.add_error(None, "Program type, Course, Semester, and Subject must be selected.")
            else:
                assignment.program_type_id = selected_program_type_id
                assignment.academic_year = selected_academic_year
                assignment.course_id = selected_course_id
                assignment.semester_number = selected_semester_id
                assignment.subject_id = selected_subject_id
                assignment.faculty = employee   # 🔹 auto assign logged-in employee
                assignment.save()

                messages.success(request, f"Assignment '{assignment.title}' created successfully!")
                return redirect('assignment_list')

    else:
        form = AssignmentForm(faculty_queryset=Employee.objects.filter(id=employee.id))
        form.fields['faculty'].initial = employee.id

    return render(request, 'lms/employee_assignments_form.html', {
        'form': form,
        'program_types': CourseType.objects.all().order_by('name'),
        'academic_years': academic_years,
        'courses': filtered_courses,
        'semesters': semester_display,
        'subjects': filtered_subjects,
        'faculty_members': [employee],   # only the logged-in employee
        'selected': {
            'program_type': selected_program_type_id,
            'academic_year': selected_academic_year,
            'course': selected_course_id,
            'semester': selected_semester_id,
            'subject': selected_subject_id,
            'faculty': employee.id,
        },
        'is_edit': False
    })




#change
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import AssignmentForm
from .models import Assignment
from master.models import Course, Subject, CourseType, Employee, StudentDatabase, EmployeeSubjectAssignment


def edit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)

    # Authenticate employee
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    # ✅ Allow edit only if faculty is same OR empty
    if assignment.faculty and assignment.faculty != employee:
        messages.error(request, "You are not allowed to edit this assignment.")
        return redirect('assignment_list')

    # If faculty not set → auto-assign to logged-in employee
    if not assignment.faculty:
        assignment.faculty = employee
        assignment.save()

    # Selected values from assignment
    selected_program_type_id = assignment.program_type_id
    selected_academic_year = assignment.academic_year
    selected_course_id = assignment.course_id
    selected_semester_id = assignment.semester_number
    selected_subject_id = assignment.subject_id

    # 🔹 Get employee’s subject assignments
    emp_assignments = EmployeeSubjectAssignment.objects.filter(employee=employee).select_related('course', 'subject')

    # Courses assigned to employee (filtered by program type)
    assigned_courses = {a.course.id: a.course for a in emp_assignments}
    filtered_courses = [
        c for c in assigned_courses.values()
        if not selected_program_type_id or str(c.course_type_id) == str(selected_program_type_id)
    ]

    # Semesters assigned to employee for the selected course
    course_semesters = {}
    for a in emp_assignments:
        course_semesters.setdefault(a.course.id, set()).add(a.semester)

    semester_display = []
    if selected_course_id and int(selected_course_id) in course_semesters:
        course = assigned_courses[int(selected_course_id)]
        sem_list = sorted(course_semesters[int(selected_course_id)])
        semester_display = [{'id': sem, 'label': f"{course.name} - Semester {sem}"} for sem in sem_list]

    # Subjects assigned to employee for the selected course
    filtered_subjects = []
    if selected_course_id and selected_semester_id:
        for a in emp_assignments:
            if (
                str(a.course.id) == selected_course_id and 
                str(a.semester) == selected_semester_id and 
                a.subject not in filtered_subjects
            ):
                filtered_subjects.append(a.subject)

    # Academic years linked with selected program type
    academic_years = []
    if selected_program_type_id:
        academic_years = (
            StudentDatabase.objects
            .filter(course__course_type_id=selected_program_type_id)
            .values_list('academic_year', flat=True)
            .distinct()
            .order_by('-academic_year')
        )

    # Faculty = logged-in employee only
    faculty_queryset = Employee.objects.filter(id=employee.id)

    if request.method == 'POST':
        form = AssignmentForm(
            request.POST,
            request.FILES,
            instance=assignment,
            faculty_queryset=faculty_queryset
        )
        if form.is_valid():
            updated = form.save(commit=False)
            updated.program_type_id = selected_program_type_id
            updated.academic_year = selected_academic_year
            updated.course_id = selected_course_id
            updated.semester_number = selected_semester_id
            updated.subject_id = selected_subject_id
            updated.faculty = employee  # 🔒 Always logged-in employee
            updated.save()
            messages.success(request, "Assignment updated successfully.")
            return redirect('assignment_list')
        else:
            print("Form errors:", form.errors)
    else:
        form = AssignmentForm(instance=assignment, faculty_queryset=faculty_queryset)

    context = {
        'form': form,
        'program_types': CourseType.objects.all().order_by('name'),
        'academic_years': academic_years,
        'courses': filtered_courses,
        'semesters': semester_display,
        'subjects': filtered_subjects,
        'faculty_members': [employee],
        'selected': {
            'program_type': str(assignment.program_type_id or ''),
            'academic_year': str(assignment.academic_year or ''),
            'course': str(assignment.course_id or ''),
            'semester': str(assignment.semester_number or ''),
            'subject': str(assignment.subject_id or ''),
            'faculty': str(assignment.faculty_id or employee.id or ''),
        },

    
        'is_edit': True
    }



    return render(request, 'lms/employee_assignments_form.html', context)

#change
from django.shortcuts import render, get_object_or_404
from .models import Assignment
from .forms import AssignmentForm
from master.models import Course, Subject, CourseType, StudentDatabase, EmployeeSubjectAssignment, Employee

def view_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)

    selected_program_type_id = assignment.program_type_id
    selected_academic_year = assignment.academic_year
    selected_course_id = assignment.course_id
    selected_semester_id = assignment.semester_number
    selected_subject_id = assignment.subject_id
    selected_faculty_id = assignment.faculty_id

    # Courses filtered by program type
    filtered_courses = Course.objects.filter(course_type_id=selected_program_type_id)

    # Subjects filtered by selected course
    filtered_subjects = Subject.objects.filter(course_id=selected_course_id).order_by('name')

    # Semesters for selected course
    semester_display = []
    if selected_course_id:
        selected_course = Course.objects.get(id=selected_course_id)
        is_pu = selected_course.course_type.name.strip().lower() == "puc regular"
        total = selected_course.duration_years if is_pu else selected_course.total_semesters or 0
        semester_display = [{'id': i, 'label': f"{selected_course.name} {i}"} for i in range(1, total + 1)]

    # Academic years filtered by program type
    academic_years = (
        StudentDatabase.objects
        .filter(course__course_type_id=selected_program_type_id)
        .values_list('academic_year', flat=True)
        .distinct()
        .order_by('-academic_year')
    )

    # Faculty assigned for this course+semester+subject
    faculty_assignments = EmployeeSubjectAssignment.objects.filter(
        course_id=selected_course_id,
        semester=selected_semester_id,
        subject_id=selected_subject_id
    ).select_related('employee')

    faculty_members = [a.employee for a in faculty_assignments]

    # 🔹 Ensure current faculty is included in list (important for view mode)
    if assignment.faculty and assignment.faculty not in faculty_members:
        faculty_members.append(assignment.faculty)

    # Read-only form
    form = AssignmentForm(instance=assignment, faculty_queryset=faculty_members)
    for field in form.fields.values():
        field.disabled = True

    context = {
        'form': form,
        'program_types': CourseType.objects.all().order_by('name'),
        'academic_years': academic_years,
        'courses': filtered_courses,
        'semesters': semester_display,
        'subjects': filtered_subjects,
        'faculty_members': faculty_members,
        'selected': {
            'program_type': str(selected_program_type_id or ''),
            'academic_year': str(selected_academic_year or ''),
            'course': str(selected_course_id or ''),
            'semester': str(selected_semester_id or ''),
            'subject': str(selected_subject_id or ''),
            'faculty': str(selected_faculty_id or ''),  # ✅ added this
        },
        'view_mode': True,
    }

    return render(request, 'lms/employee_assignments_form.html', context)

#change
from django.http import HttpResponse

def download_assignment(request, assignment_id):
    """Return assignment file download only"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    if assignment.attachment:
        response = HttpResponse(
            assignment.attachment,
            content_type="application/octet-stream"
        )
        response["Content-Disposition"] = f'attachment; filename="{assignment.attachment.name}"'
        return response
    else:
        return HttpResponse("No file attached", status=404)


# from django.shortcuts import get_object_or_404
# from django.http import HttpResponse
# from .models import Assignment, AssignmentSubmission
# from admission.models import ConfirmedAdmission


# def download_assignment(request, assignment_id):
#     """Student downloads assignment → update/create submission → set In Progress"""

#     # ✅ Get logged in student from cookie
#     student_userid = request.COOKIES.get("student_userid")
#     if not student_userid:
#         return HttpResponse("Student not logged in.", status=403)

#     try:
#         student = ConfirmedAdmission.objects.get(student_userid=student_userid)
#     except ConfirmedAdmission.DoesNotExist:
#         return HttpResponse("Student record not found.", status=404)

#     # ✅ Get assignment
#     assignment = get_object_or_404(Assignment, id=assignment_id)

#     # ✅ Fetch OR create submission row for this student & assignment
#     submission, created = AssignmentSubmission.objects.get_or_create(
#         assignment=assignment,
#         student_userid=student.student_userid,
#         defaults={
#             "student_status": "in_progress",
#             "faculty_status": "in_progress",
#         },
#     )

#     if not created:  # if already exists → just update
#         submission.student_status = "in_progress"
#         submission.faculty_status = "in_progress"
#         submission.save()

#     # ✅ Return file as download
#     if assignment.attachment:
#         response = HttpResponse(
#             assignment.attachment,
#             content_type="application/octet-stream"
#         )
#         response["Content-Disposition"] = f'attachment; filename="{assignment.attachment.name}"'
#         return response
#     else:
#         return HttpResponse("No file attached to this assignment.", status=404)


#change new

# views.py
from django.views.decorators.http import require_POST
from django.http import JsonResponse

@require_POST
def mark_in_progress(request, assignment_id):
    """Mark assignment as in_progress when student starts working on it"""
    student_userid = request.COOKIES.get("student_userid")
    if not student_userid:
        return JsonResponse({"error": "Not logged in"}, status=403)

    try:
        student = ConfirmedAdmission.objects.get(student_userid=student_userid)
    except ConfirmedAdmission.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    assignment = get_object_or_404(Assignment, id=assignment_id)

    submission, created = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student_userid=student.student_userid,
        defaults={
            "student_status": "in_progress",
            "faculty_status": "in_progress",
        },
    )
    if not created:
        submission.student_status = "in_progress"
        submission.faculty_status = "in_progress"
        submission.save()

    return JsonResponse({"success": True, "status": "in_progress"})



import os
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404

def delete_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)

    # Store file path before deleting
    file_path = assignment.attachment.path if assignment.attachment else None
    folder_path = os.path.dirname(file_path) if file_path else None

    # Delete the Assignment object (this will not delete the file automatically)
    assignment.delete()

    # Delete the file if it exists
    if file_path and os.path.isfile(file_path):
        os.remove(file_path)

    # Delete folder if empty
    if folder_path and os.path.isdir(folder_path) and not os.listdir(folder_path):
        try:
            os.rmdir(folder_path)
        except OSError:
            pass  # Ignore errors (e.g., folder not empty)

    messages.success(request, "Assignment deleted successfully.")
    return redirect('assignment_list')


# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import BookForm
from .models import Book
 
def book_list(request):
    books = Book.objects.all().order_by('-id')
    return render(request, 'lms/books_list.html', {'books': books})
 
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f"'{book.title}' was successfully added.")
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'lms/books_form.html', {'form': form})
 
def book_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(instance=book)
 
    # Disable all fields
    for field in form.fields.values():
        field.widget.attrs['disabled'] = 'disabled'
 
    return render(request, 'lms/books_form.html', {'form': form, 'is_view': True})
 
 
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{book.title}' was successfully updated.")
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'lms/books_form.html', {'form': form})
 
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    title = book.title
    book.delete()
    messages.success(request, f"'{title}' was successfully deleted.")
    return redirect('book_list')



from django.shortcuts import render, get_object_or_404
from .models import Book, BorrowRecord  # Adjust model names as per your app

def book_borrow_details(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    borrow_records = BorrowRecord.objects.filter(book=book)  # Replace with actual model name
    
    return render(request, 'lms/book_borrow_details.html', {
        'book': book,
        'borrow_records': borrow_records
    })

from django.shortcuts import render, redirect
from .forms import BorrowRecordForm
from .models import BorrowRecord
from datetime import date  # ⬅️ Add this import

def borrow_book_view(request):
    if request.method == 'POST':
        form = BorrowRecordForm(request.POST)
        if form.is_valid():
            borrow_record = form.save()
            messages.success(request, f"Book '{borrow_record.book.title}' successfully borrowed by {borrow_record.student}.")
            return redirect('book_borrow_details', book_id=borrow_record.book.id)
        else:
            messages.error(request, "")
    else:
        form = BorrowRecordForm()
    borrowed_data = {}
    borrow_records = BorrowRecord.objects.filter(returned=False).values('book_id', 'student_id')
    for record in borrow_records:
        borrowed_data.setdefault(record['book_id'], []).append(record['student_id'])

    return render(request, 'lms/borrow_book_form.html', {
        'form': form,
        'borrowed_data': borrowed_data  # For JS to check
    })




# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from .models import BorrowRecord

def borrow_record_details(request, record_id):
    borrow_record = get_object_or_404(BorrowRecord, id=record_id)

    # If form is submitted (book returned)
    if request.method == 'POST' and not borrow_record.returned:
        borrow_record.returned = True
        borrow_record.return_date = now().date()  # record the current date as return date
        borrow_record.save()

        # Increase the available copies of the book
        book = borrow_record.book
        book.available_copies += 1
        book.save()

        return redirect('book_list')  # or any other redirect

    return render(request, 'lms/borrow_record_details.html', {
        'borrow_record': borrow_record
    })



from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from .forms import EmployeeStudyMaterialForm
from .models import EmployeeStudyMaterial
from master.models import Course, Subject, CourseType, Employee, StudentDatabase, EmployeeSubjectAssignment




def create_study_material(request):
    # Authenticate employee from cookies
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    # Get query parameters from filters (GET params)
    selected_program_type_id = request.GET.get('program_type')
    selected_academic_year = request.GET.get('academic_year')
    selected_course_id = request.GET.get('course')
    selected_semester_id = request.GET.get('semester')
    selected_subject_id = request.GET.get('subject')

    # Get only subjects assigned to this employee
    assignments = EmployeeSubjectAssignment.objects.filter(employee=employee).select_related('course', 'subject')

    # Distinct courses, subjects, semesters from assignments
    assigned_courses = {a.course.id: a.course for a in assignments}
    assigned_subjects = {a.subject.id: a.subject for a in assignments}
    course_semesters = {}
    for a in assignments:
        course_semesters.setdefault(a.course.id, set()).add(a.semester)

    # Filter courses based on selected program type
    filtered_courses = []
    for course in assigned_courses.values():
        if not selected_program_type_id or str(course.course_type_id) == selected_program_type_id:
            filtered_courses.append(course)

    # Filter subjects based on selected course
    filtered_subjects = []
    if selected_course_id and selected_semester_id:
        for a in assignments:
            if (
                str(a.course.id) == selected_course_id and 
                str(a.semester) == selected_semester_id and 
                a.subject not in filtered_subjects
            ):
                filtered_subjects.append(a.subject)

    # Generate semester dropdown options
    semester_display = []
    if selected_course_id and int(selected_course_id) in course_semesters:
        course = assigned_courses[int(selected_course_id)]
        sem_list = sorted(course_semesters[int(selected_course_id)])
        semester_display = [{'id': sem, 'label': f"{course.name} {sem}"} for sem in sem_list]

    # Academic years for this program type
    academic_years = []
    if selected_program_type_id:
        academic_years = (
            StudentDatabase.objects
            .filter(course__course_type_id=selected_program_type_id)
            .values_list('academic_year', flat=True)
            .distinct()
            .order_by('-academic_year')
        )

    if request.method == 'POST':
        form = EmployeeStudyMaterialForm(request.POST, request.FILES, faculty_queryset=Employee.objects.filter(id=employee.id))

        if form.is_valid():
            material = form.save(commit=False)

            # Use selected GET params here, NOT request.POST.get()
            # Also ensure these are not None or empty strings
            if not (selected_program_type_id and selected_course_id and selected_semester_id and selected_subject_id):
                form.add_error(None, "Program type, Course, Semester, and Subject must be selected.")
            else:
                material.program_type_id = selected_program_type_id
                material.academic_year = selected_academic_year
                material.course_id = selected_course_id
                material.semester_number = selected_semester_id
                material.subject_id = selected_subject_id
                material.faculty = employee  # Assign logged-in employee
                material.save()
                return redirect('employee_study_material_list')

    else:
        form = EmployeeStudyMaterialForm(faculty_queryset=Employee.objects.filter(id=employee.id))
        form.fields['faculty'].initial = employee.id

    return render(request, 'lms/employee_study_material_form.html', {
        'form': form,
        'program_types': CourseType.objects.all().order_by('name'),
        'academic_years': academic_years,
        'courses': filtered_courses,
        'semesters': semester_display,
        'subjects': filtered_subjects,
        'faculty_members': [employee],
        'selected': {
            'program_type': selected_program_type_id,
            'academic_year': selected_academic_year,
            'course': selected_course_id,
            'semester': selected_semester_id,
            'subject': selected_subject_id,
            'faculty': employee.id,
        },
        'is_edit': False
    })


from django.shortcuts import render, redirect, get_object_or_404
from .forms import EmployeeStudyMaterialForm
from .models import EmployeeStudyMaterial
from master.models import Course, Subject, CourseType, Employee, StudentDatabase, EmployeeSubjectAssignment

def edit_study_material(request, pk):
    # 🔐 Authenticate employee from cookies
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    instance = get_object_or_404(EmployeeStudyMaterial, pk=pk)

    # ✅ Prevent unauthorized editing
    if instance.faculty != employee:
        return redirect('employee_study_material_list')

    # Extract current values
    selected_program_type_id = instance.program_type_id
    selected_academic_year = instance.academic_year
    selected_course_id = instance.course_id
    selected_semester_id = instance.semester_number
    selected_subject_id = instance.subject_id

    # Fetch employee's subject assignments
    assignments = EmployeeSubjectAssignment.objects.filter(employee=employee).select_related('course', 'subject')

    # Map assigned course and subject data
    assigned_courses = {a.course.id: a.course for a in assignments}
    assigned_subjects = {a.subject.id: a.subject for a in assignments}
    course_semesters = {}
    for a in assignments:
        course_semesters.setdefault(a.course.id, set()).add(a.semester)

    # Filter courses
    filtered_courses = [
        course for course in assigned_courses.values()
        if not selected_program_type_id or str(course.course_type_id) == str(selected_program_type_id)
    ]

    # Filter subjects
    filtered_subjects = []
    if selected_course_id:
        for a in assignments:
            if str(a.course.id) == str(selected_course_id) and a.subject not in filtered_subjects:
                filtered_subjects.append(a.subject)

    # Semester options
    semester_display = []
    if selected_course_id and int(selected_course_id) in course_semesters:
        course = assigned_courses[int(selected_course_id)]
        sem_list = sorted(course_semesters[int(selected_course_id)])
        semester_display = [{'id': sem, 'label': f"{course.name} {sem}"} for sem in sem_list]

    # Academic year dropdown
    academic_years = (
        StudentDatabase.objects
        .filter(course__course_type_id=selected_program_type_id)
        .values_list('academic_year', flat=True)
        .distinct()
        .order_by('-academic_year')
    )

    # Handle form submission
    if request.method == 'POST':
        form = EmployeeStudyMaterialForm(request.POST, request.FILES, instance=instance, faculty_queryset=Employee.objects.filter(id=employee.id))
        if form.is_valid():
            material = form.save(commit=False)

            # Prevent accidental overwrite if filters changed
            if not (selected_program_type_id and selected_course_id and selected_semester_id and selected_subject_id):
                form.add_error(None, "Program type, Course, Semester, and Subject must be selected.")
            else:
                material.program_type_id = selected_program_type_id
                material.academic_year = selected_academic_year
                material.course_id = selected_course_id
                material.semester_number = selected_semester_id
                material.subject_id = selected_subject_id
                material.faculty = employee  # Redundant but safe
                material.save()
                return redirect('employee_study_material_list')
    else:
        form = EmployeeStudyMaterialForm(instance=instance, faculty_queryset=Employee.objects.filter(id=employee.id))
        form.fields['faculty'].initial = employee.id

    return render(request, 'lms/employee_study_material_form.html', {
        'form': form,
        'program_types': CourseType.objects.all().order_by('name'),
        'academic_years': academic_years,
        'courses': filtered_courses,
        'semesters': semester_display,
        'subjects': filtered_subjects,
        'faculty_members': [employee],
        'selected': {
        'program_type': str(instance.program_type_id or ''),
        'academic_year': str(instance.academic_year or ''),
        'course': str(instance.course_id or ''),
        'semester': str(instance.semester_number or ''),
        'subject': str(instance.subject_id or ''),
        'faculty': str(instance.faculty_id or ''),
    },
        'is_edit': True
    })



from django.shortcuts import render, redirect
from master.models import Employee
from .models import EmployeeStudyMaterial

def employee_study_material_list(request):
    # Get employee from cookie
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    # Filter materials by logged-in faculty
    study_materials = EmployeeStudyMaterial.objects.filter(faculty=employee).order_by('-created_at')

    return render(request, 'lms/employee_study_material_list.html', {
        'study_materials': study_materials
    })


def delete_employee_study_material(request, pk):
    material = get_object_or_404(EmployeeStudyMaterial, pk=pk)
    material.delete()
    return redirect('employee_study_material_list')



#This is exam


#This is exam

from django.shortcuts import render, redirect, get_object_or_404
from .models import Exam
from .forms import ExamForm
from master.models import Course, Subject, CourseType, StudentDatabase, Employee

def exam_list(request):
    # Authenticate employee
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    # Show only exams created by this faculty
    exams = Exam.objects.filter(faculty=employee).select_related('subject', 'course', 'faculty').order_by('-created_at')

    return render(request, 'lms/employee_exam_create_list.html', {
        'exams': exams
    })


def create_exam(request):
    # Authenticate employee
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    # Get filter parameters
    selected_program_type_id = request.GET.get('program_type')
    selected_academic_year = request.GET.get('academic_year')
    selected_course_id = request.GET.get('course')
    selected_semester_id = request.GET.get('semester')
    selected_subject_id = request.GET.get('subject')

    # Get only assigned subjects for this employee
    assignments = EmployeeSubjectAssignment.objects.filter(employee=employee).select_related('course', 'subject')

    assigned_courses = {a.course.id: a.course for a in assignments}
    assigned_subjects = {a.subject.id: a.subject for a in assignments}
    course_semesters = {}
    for a in assignments:
        course_semesters.setdefault(a.course.id, set()).add(a.semester)

    # Filter courses based on selected program type
    filtered_courses = []
    for course in assigned_courses.values():
        if not selected_program_type_id or str(course.course_type_id) == selected_program_type_id:
            filtered_courses.append(course)

    # Filter subjects based on selected course
    filtered_subjects = []
    if selected_course_id and selected_semester_id:
        for a in assignments:
            if (
                str(a.course.id) == selected_course_id and 
                str(a.semester) == selected_semester_id and 
                a.subject not in filtered_subjects
            ):
                filtered_subjects.append(a.subject)
    # Generate semester options
    semester_display = []
    if selected_course_id and int(selected_course_id) in course_semesters:
        course = assigned_courses[int(selected_course_id)]
        sem_list = sorted(course_semesters[int(selected_course_id)])
        semester_display = [{'id': sem, 'label': f"{course.name} {sem}"} for sem in sem_list]

    # Academic years for selected program type
    academic_years = []
    if selected_program_type_id:
        academic_years = (
            StudentDatabase.objects
            .filter(course__course_type_id=selected_program_type_id)
            .values_list('academic_year', flat=True)
            .distinct()
            .order_by('-academic_year')
        )

    # Handle form submission
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            if not (selected_program_type_id and selected_course_id and selected_semester_id and selected_subject_id):
                form.add_error(None, "All filters (Program, Course, Semester, Subject) must be selected.")
            else:
                exam.program_type_id = selected_program_type_id
                exam.academic_year = selected_academic_year
                exam.course_id = selected_course_id
                exam.semester_number = selected_semester_id
                exam.subject_id = selected_subject_id
                exam.faculty = employee  # if applicable
                exam.save()
                return redirect('exam_list')
    else:
        form = ExamForm()

    context = {
        'form': form,
        'program_types': CourseType.objects.all().order_by('name'),
        'academic_years': academic_years,
        'courses': filtered_courses,
        'semesters': semester_display,
        'subjects': filtered_subjects,
        'faculty_members': [employee],
        'selected': {
            'program_type': selected_program_type_id,
            'academic_year': selected_academic_year,
            'course': selected_course_id,
            'semester': selected_semester_id,
            'subject': selected_subject_id,
            'faculty': employee.id,
        },
        'is_edit': False
    }

    return render(request, 'lms/employee_exam_create_form.html', context)


def edit_exam(request, pk):
    # Authenticate employee
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    exam = get_object_or_404(Exam, pk=pk)

    # Optional: Prevent editing of other employee's exams
    if exam.faculty_id and exam.faculty_id != employee.id:
        return redirect('exam_list')  # Or raise permission denied

    # Preselect filters based on saved exam
    selected_program_type_id = exam.program_type_id
    selected_academic_year = exam.academic_year
    selected_course_id = exam.course_id
    selected_semester_id = exam.semester_number
    selected_subject_id = exam.subject_id

    # Get assignments for logged-in employee
    assignments = EmployeeSubjectAssignment.objects.filter(employee=employee).select_related('course', 'subject')

    assigned_courses = {a.course.id: a.course for a in assignments}
    assigned_subjects = {a.subject.id: a.subject for a in assignments}
    course_semesters = {}
    for a in assignments:
        course_semesters.setdefault(a.course.id, set()).add(a.semester)

    # Filter courses based on selected program type
    filtered_courses = []
    for course in assigned_courses.values():
        if not selected_program_type_id or str(course.course_type_id) == str(selected_program_type_id):
            filtered_courses.append(course)

    # Filter subjects based on selected course
    filtered_subjects = []
    if selected_course_id:
        for a in assignments:
            if str(a.course.id) == str(selected_course_id) and a.subject not in filtered_subjects:
                filtered_subjects.append(a.subject)

    # Generate semester options
    semester_display = []
    if selected_course_id and int(selected_course_id) in course_semesters:
        course = assigned_courses[int(selected_course_id)]
        sem_list = sorted(course_semesters[int(selected_course_id)])
        semester_display = [{'id': sem, 'label': f"{course.name} {sem}"} for sem in sem_list]

    # Academic years for selected program type
    academic_years = []
    if selected_program_type_id:
        academic_years = (
            StudentDatabase.objects
            .filter(course__course_type_id=selected_program_type_id)
            .values_list('academic_year', flat=True)
            .distinct()
            .order_by('-academic_year')
        )

    # Handle form submission
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            updated_exam = form.save(commit=False)
            updated_exam.program_type_id = selected_program_type_id
            updated_exam.academic_year = selected_academic_year
            updated_exam.course_id = selected_course_id
            updated_exam.semester_number = selected_semester_id
            updated_exam.subject_id = selected_subject_id
            updated_exam.faculty = employee
            updated_exam.save()
            return redirect('exam_list')
    else:
        form = ExamForm(instance=exam)

    context = {
        'form': form,
        'program_types': CourseType.objects.all().order_by('name'),
        'academic_years': academic_years,
        'courses': filtered_courses,
        'semesters': semester_display,
        'subjects': filtered_subjects,
        'faculty_members': [employee],
        'selected': {
        'program_type': str(exam.program_type_id or ''),
        'academic_year': str(exam.academic_year or ''),
        'course': str(exam.course_id or ''),
        'semester': str(exam.semester_number or ''),
        'subject': str(exam.subject_id or ''),
        'faculty': str(exam.faculty_id or ''),
    },
        'is_edit': True,
        'exam': exam,
    }

    return render(request, 'lms/employee_exam_create_form.html', context)



def view_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    return render(request, 'lms/employee_exam_create_form.html', {'view_mode': True, 'exam': exam})

def delete_exam(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    exam.delete()
    return redirect('exam_list')




#change
#change
def sanitize(text):
    if text is None:
        return ''
    # Replace any invalid characters with '?'
    return text.encode('utf-8', errors='replace').decode('utf-8')
from decimal import Decimal, InvalidOperation
from django.db.models import Q
def submitted_assignments(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    students = StudentDatabase.objects.filter(
        course_type=assignment.program_type,
        academic_year=assignment.academic_year,
        course=assignment.subject.course
    ).filter(
        Q(semester=assignment.subject.semester) | 
        Q(current_year=assignment.subject.semester)
    )

    student_submissions = []
    for student in students:
        submission, _ = AssignmentSubmission.objects.get_or_create(
            assignment=assignment,
            student_userid=student.student_userid,
            defaults={'student_status': 'pending', 'faculty_status': 'pending'}
        )
        student_submissions.append({
            "student": student,
            "submission": submission
        })

    if request.method == 'POST':
        for data in student_submissions:
            submission = data["submission"]

            # Read POST values
            action = request.POST.get(f'action_{submission.id}', '').strip()
            score_raw = request.POST.get(f'score_{submission.id}', '').strip()
            remarks_raw = request.POST.get(f'remarks_{submission.id}', '').strip()
            rejection_reason = request.POST.get(f'rejection_reason_{submission.id}', '').strip()

            # Normalize score
            score_val = None
            if score_raw:
                try:
                    score_val = Decimal(score_raw)
                except (InvalidOperation, ValueError):
                    score_val = None

            # Process actions
            if action == 'reject':
                submission.student_status = 'rejected'
                submission.faculty_status = 'rejected'
                submission.rejection_reason = rejection_reason
                submission.score = None
                submission.remarks = None

            elif action == 'review':
                submission.rejection_reason = None

                if not score_val and not remarks_raw:
                    # Faculty accepted but did not grade yet
                    submission.student_status = 'review'
                    submission.faculty_status = 'review'
                    submission.score = None
                    submission.remarks = None
                else:
                    # Faculty provided grading info now
                    submission.student_status = 'graded'
                    submission.faculty_status = 'graded'
                    submission.score = score_val
                    submission.remarks = remarks_raw or None

            else:
                # No radio button changed this time
                # But if faculty already accepted earlier and now adds score/remarks → promote to graded
                if submission.faculty_status == 'review' and (score_val or remarks_raw):
                    submission.student_status = 'graded'
                    submission.faculty_status = 'graded'
                    submission.score = score_val
                    submission.remarks = remarks_raw or submission.remarks

            submission.save()

            print(f"✅ Saved submission {submission.id}: "
                  f"student_status={submission.student_status}, "
                  f"faculty_status={submission.faculty_status}, "
                  f"score={submission.score}, remarks={submission.remarks}, "
                  f"rejection_reason={submission.rejection_reason}")

        print("=== POST PROCESSING DONE ===")
        return redirect('submitted_assignments', assignment_id=assignment.id)

    return render(request, 'lms/submitted_assignments_list.html', {
        'assignment': assignment,
        'student_submissions': student_submissions
    })

# Create Marks Entry
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from master.models import CourseType, Course, Subject, StudentDatabase, Employee, ExamType
from lms.models import Exam
from .models import StudentExamMarks

def create_exam_marks(request):
    # Authenticate employee
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    # Get filter values from GET
    selected_program_type_id = request.GET.get('program_type')
    selected_academic_year = request.GET.get('academic_year')
    selected_course_id = request.GET.get('course')
    selected_semester_id = request.GET.get('semester')
    selected_subject_id = request.GET.get('subject')

    # Get subject assignments for logged-in employee
    assignments = EmployeeSubjectAssignment.objects.filter(employee=employee).select_related('course', 'subject')

    assigned_courses = {a.course.id: a.course for a in assignments}
    assigned_subjects = {a.subject.id: a.subject for a in assignments}
    course_semesters = {}
    for a in assignments:
        course_semesters.setdefault(a.course.id, set()).add(a.semester)

    # Filter courses based on selected program type
    filtered_courses = []
    for course in assigned_courses.values():
        if not selected_program_type_id or str(course.course_type_id) == selected_program_type_id:
            filtered_courses.append(course)

    # Filter subjects based on selected course
    filtered_subjects = []
    if selected_course_id and selected_semester_id:
        for a in assignments:
            if (
                str(a.course.id) == selected_course_id and 
                str(a.semester) == selected_semester_id and 
                a.subject not in filtered_subjects
            ):
                filtered_subjects.append(a.subject)

    # Generate semester options
    semester_display = []
    if selected_course_id and int(selected_course_id) in course_semesters:
        course = assigned_courses[int(selected_course_id)]
        sem_list = sorted(course_semesters[int(selected_course_id)])
        semester_display = [{'id': sem, 'label': f"{course.name} {sem}"} for sem in sem_list]

    # Academic years
    academic_years = []
    if selected_program_type_id:
        academic_years = (
            StudentDatabase.objects
            .filter(course__course_type_id=selected_program_type_id)
            .values_list('academic_year', flat=True)
            .distinct()
            .order_by('-academic_year')
        )

    # Get students for selected course/semester or current_year (PUC case)
    students = []
    if selected_course_id and selected_semester_id:
        try:
            selected_course = Course.objects.select_related('course_type').get(id=selected_course_id)
            course_type_name = selected_course.course_type.name.lower()
        except Course.DoesNotExist:
            course_type_name = ""

        student_filter = {
            'course_id': selected_course_id,
            'academic_year': selected_academic_year,
            'status': 'Active',
        }

        if "puc" in course_type_name:
            student_filter['current_year'] = selected_semester_id
        else:
            student_filter['semester'] = selected_semester_id

        students = StudentDatabase.objects.filter(**student_filter)

    # Filter exams created by this faculty for selected filters
    exams = Exam.objects.filter(faculty=employee)
    if selected_program_type_id:
        exams = exams.filter(program_type_id=selected_program_type_id)
    if selected_academic_year:
        exams = exams.filter(academic_year=selected_academic_year)
    if selected_course_id:
        exams = exams.filter(course_id=selected_course_id)
    if selected_semester_id:
        exams = exams.filter(semester_number=selected_semester_id)
    if selected_subject_id:
        exams = exams.filter(subject_id=selected_subject_id)

    # Get distinct exam types
    exam_type_ids = exams.values_list('exam_type_id', flat=True).distinct()
    exam_types = ExamType.objects.filter(id__in=exam_type_ids)

    # Handle mark submission
    if request.method == 'POST' and request.POST.get('form_action') == 'submit_marks':
        selected_exam_type_id = request.POST.get('exam_type_id')

        if not selected_exam_type_id:
            messages.error(request, "Please select an exam type.")
            return redirect(request.path)

        selected_exam_type = get_object_or_404(ExamType, id=selected_exam_type_id)
        exam_qs = exams.filter(exam_type=selected_exam_type)

        if not exam_qs.exists():
            messages.error(request, "No matching exam found.")
            return redirect(request.path)

        selected_exam = exam_qs.first()
        max_marks = selected_exam.marks  # ✅ Get from Exam model

        for sid in request.POST.getlist('student_ids[]'):
            StudentExamMarks.objects.update_or_create(
                student_id=sid,
                subject=selected_exam.subject,
                mark_type=selected_exam.exam_type,
                academic_year=selected_exam.academic_year,
                defaults={
                    'program_type': selected_exam.program_type,
                    'course': selected_exam.course,
                    'semester_number': selected_exam.semester_number,
                    'faculty': employee,
                    'marks_obtained': request.POST.get(f"marks_{sid}") or 0,
                    'max_marks': max_marks,
                    'remarks': request.POST.get(f"remarks_{sid}"),
                }
            )

        messages.success(request, "Marks saved successfully.")
        return redirect('exam_marks_list')

    # Context for rendering
    context = {
        'mode': 'create',
        'program_types': CourseType.objects.all().order_by('name'),
        'academic_years': academic_years,
        'courses': filtered_courses,
        'semesters': semester_display,
        'subjects': filtered_subjects,
        'students': students,
        'exam_types': exam_types,
        'selected': {
            'program_type': selected_program_type_id,
            'academic_year': selected_academic_year,
            'course': selected_course_id,
            'semester': selected_semester_id,
            'subject': selected_subject_id,
        },
    }

    return render(request, 'lms/employee_exam_marks_create_form.html', context)





# Edit Marks
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

def edit_exam_marks(request, pk):
    # Authenticate employee
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    mark = get_object_or_404(StudentExamMarks, pk=pk)

    # Extract selected filters from the current mark object for dropdown pre-selection
    selected_program_type = str(mark.program_type_id or '')
    selected_academic_year = str(mark.academic_year or '')
    selected_course = str(mark.course_id or '')
    selected_semester = str(mark.semester_number or '')
    selected_subject = str(mark.subject_id or '')

    # Prepare dropdown querysets similarly to create view

    program_types = CourseType.objects.all()

    academic_years = []
    if selected_program_type:
        academic_years = (
            StudentDatabase.objects
            .filter(course__course_type_id=selected_program_type)
            .values_list('academic_year', flat=True)
            .distinct()
            .order_by('-academic_year')
        )

    courses = Course.objects.all()
    if selected_program_type:
        courses = courses.filter(course_type_id=selected_program_type)

    semesters = []
    if selected_course:
        course = get_object_or_404(Course, id=selected_course)
        semesters = [{'id': i, 'label': f"Semester {i}"} for i in range(1, (course.total_semesters or 0) + 1)]

    subjects = []
    if selected_course and selected_semester:
        subjects = Subject.objects.filter(course_id=selected_course, semester=selected_semester)

    faculty_members = []
    if selected_subject:
        faculty_members = Employee.objects.filter(subject_assignments__subject_id=selected_subject).distinct()

    students = []
    if selected_course and selected_semester:
        students = StudentDatabase.objects.filter(course_id=selected_course, semester=selected_semester)

    if request.method == 'POST':
        marks_obtained = request.POST.get('marks_obtained')
        remarks = request.POST.get('remarks')

        try:
            mark.marks_obtained = float(marks_obtained)
        except (TypeError, ValueError):
            messages.error(request, "Invalid marks value.")
            return redirect(request.path)

        mark.remarks = remarks
        mark.save()
        messages.success(request, "Exam marks updated successfully!")
        return redirect('exam_marks_list')

    # Prepare context with current mark data and dropdowns for editing
    context = {
        'mode': 'edit',
        'mark': mark,
        'program_types': program_types,
        'academic_years': academic_years,
        'courses': courses,
        'semesters': semesters,
        'subjects': subjects,
        'faculty_members': faculty_members,
        'students': students,
        'selected': {
            'program_type': selected_program_type,
            'academic_year': selected_academic_year,
            'course': selected_course,
            'semester': selected_semester,
            'subject': selected_subject,
            'faculty': str(mark.faculty_id or ''),
        }
    }
    return render(request, 'lms/employee_exam_marks_create_form.html', context)



def view_exam_marks(request, pk):
    mark = get_object_or_404(StudentExamMarks, pk=pk)
    context = {
        'mode': 'view',
        'mark': mark,
    }
    return render(request, 'lms/employee_exam_marks_create_form.html', context)
# List & Delete Marks
def exam_marks_list(request):
    # Authenticate employee
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    # Filter marks only for this faculty
    marks_list = StudentExamMarks.objects.filter(faculty=employee).select_related('student', 'subject', 'faculty')

    return render(request, 'lms/employee_exam_marks_create_list.html', {
        'marks_list': marks_list,
        'employee': employee,  # optional: pass employee info to template
    })


def delete_exam_marks(request, pk):
    mark_record = get_object_or_404(StudentExamMarks, pk=pk)
    mark_record.delete()
    messages.success(request, "Marks deleted successfully!")
    return redirect('exam_marks_list')





from django.shortcuts import render
from datetime import datetime

from django.db.models import Avg, Count, Q
from .models import Assignment  # Adjust according to your actual model names


from django.shortcuts import redirect, render
from django.db.models import Avg
from django.utils.timezone import now

from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.db.models import Avg
from master.models import  StudentDatabase
from .models import AssignmentSubmission, Exam, StudentExamMarks  # Update model imports as needed

def my_grades_view(request):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    current_time = now().date()

    # === FETCH STUDENT OBJECT ===
    try:
        student = StudentDatabase.objects.get(student_userid=student_userid)
    except StudentDatabase.DoesNotExist:
        return redirect('student_login_view')

    # === ASSIGNMENT SUBMISSIONS ===
    submissions = AssignmentSubmission.objects.filter(student_userid=student_userid).select_related(
        'assignment__program_type',
        'assignment__course',
        'assignment__subject',
        'assignment__time_slot',
        'assignment__faculty'
    )

    assignments = [submission.assignment for submission in submissions]
    submission_dict = {submission.assignment.id: submission for submission in submissions}

    total_assignments = len(assignments)
    upcoming_assignments = submissions.filter(assignment__due_date__gt=current_time, student_status='pending').count()
    graded_assignments = submissions.filter(student_status='graded').count()
    avg_assignment_score = submissions.filter(student_status='graded').aggregate(average=Avg('score'))['average'] or 0
    avg_assignment_score = round(avg_assignment_score, 2)

    # === EXAMS (filtered by student's course, program, and semester) ===
 # Detect course type name
    course_type_name = student.course_type.name.lower()

    exam_filter = {
        'program_type': student.course_type,
        'course': student.course,
    }

    # If course type contains "puc", use current_year instead of semester
    if "puc" in course_type_name:
        exam_filter['semester_number'] = student.current_year
    else:
        exam_filter['semester_number'] = student.semester

    student_exams = Exam.objects.filter(**exam_filter).select_related(
        'program_type', 'course', 'subject', 'faculty', 'exam_type'
    )

    exam_marks = StudentExamMarks.objects.filter(
        student=student
    ).select_related('subject', 'mark_type')

    # Map: (subject_id, mark_type_id, academic_year) => marks
    exam_marks_dict = {
        (mark.subject_id, mark.mark_type_id, mark.academic_year): mark
        for mark in exam_marks
    }

    exam_data = []
    for exam in student_exams:
        key = (exam.subject_id, exam.exam_type_id, exam.academic_year)
        mark_entry = exam_marks_dict.get(key)

        if exam.exam_date > current_time:
            status = 'Scheduled'
            score = None
        elif mark_entry:
            status = 'Graded'
            score = float(mark_entry.marks_obtained)
        else:
            status = 'Completed (Awaiting Grading)'
            score = None

        exam_data.append({
            'exam': exam,
            'status': status,
            'score': score,
            'max_marks': float(mark_entry.max_marks) if mark_entry else None,
        })

    total_exams = len(student_exams)+ total_assignments 
    scheduled_exams = len([e for e in exam_data if e['status'] == 'Scheduled'])
    graded_exams = len([e for e in exam_data if e['status'] == 'Graded'])

    exam_scores = [e['score'] for e in exam_data if e['score'] is not None]
    # Total scored marks and total max marks
    total_obtained = sum(exam_scores) + sum(
        [float(submission.score or 0) for submission in submissions if submission.student_status == 'graded']
    )

    total_max_marks = sum([
        float(mark_entry.max_marks)
        for mark_entry in exam_marks
        if mark_entry.marks_obtained is not None
    ]) + sum([

        float(submission.score or 0)

        for submission in submissions
        if submission.student_status == 'graded'
    ])

    # Final percentage
    percentage_score = round((total_obtained / total_max_marks) * 100, 2) if total_max_marks else 0


    # === CONTEXT FOR TEMPLATE ===
    context = {
        # Assignments
        'assignments': assignments,
        'submission_dict': submission_dict,
        'total_assignments': total_assignments,
        'upcoming_assignments': upcoming_assignments,
        'graded_assignments': graded_assignments,
        'avg_assignment_score': avg_assignment_score,

        # Exams
        'exam_data': exam_data,
        'total_exams': total_exams,
        'scheduled_exams': scheduled_exams,
        'graded_exams': graded_exams,

        # Combined Stats
        'upcoming': upcoming_assignments + scheduled_exams,
        'graded': graded_assignments + graded_exams,
        'avg_score': percentage_score,
        # Student (for displaying name in template)
        'logged_in_student': student,
    }

    return render(request, 'lms/my_grades.html', context)



from django.shortcuts import render, redirect
from .models import EmployeeStudyMaterial, StudentDatabase
from django.db.models import Count, Q

def my_study_materials_view(request):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    try:
        student = StudentDatabase.objects.get(student_userid=student_userid)
    except StudentDatabase.DoesNotExist:
        return redirect('student_login_view')

    academic_year = student.academic_year
    course_type = student.course_type
    course = student.course
    semester = student.semester or student.current_year

    # Fetch all relevant materials
    materials = EmployeeStudyMaterial.objects.filter(
        academic_year=academic_year,
        program_type=course_type,
        course=course,
        semester_number=semester
    ).select_related('subject', 'faculty').order_by('-created_at')

    # Stats
    total_materials = materials.count()
    notes = materials.filter(material_type='pdf').count()
    ebook_count = materials.filter(material_type='ebook').count()

    # Avoid divide-by-zero error
    ebook_percent = (ebook_count / total_materials * 100) if total_materials else 0
    
    context = {
        'materials': materials,
        'total_materials': total_materials,
        'notes': notes,
        'e_books': round(ebook_percent, 2),
    }

    return render(request, 'lms/my_study_materials.html', context)


from django.shortcuts import render, redirect
from django.db.models import Count
from .models import Certificate
from .forms import CertificateUploadForm
from django.utils.timezone import now

def my_certificates_view(request):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    try:
        student = StudentDatabase.objects.get(student_userid=student_userid)
    except StudentDatabase.DoesNotExist:
        return redirect('student_login_view')

    # Fetch all certificates for the logged-in student
    certificates = Certificate.objects.filter(student=student)

    # Summary stats
    total_count = certificates.count()
    recent_count = certificates.filter(uploaded_at__date=now().date()).count()

    form = CertificateUploadForm()
    if request.method == 'POST':
        form = CertificateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.student = student
            cert.save()
            return redirect('my_certificates_view')

    context = {
        'certificates': certificates,
        'form': form,
        'total_certificates': total_count,
        'recent_uploads': recent_count,
        'logged_in_student': student,
    }
    return render(request, 'lms/my_certificates.html', context)


from datetime import date
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render, redirect
from lms.models import CalendarEvent, Assignment, AssignmentSubmission, BorrowRecord
from master.models import StudentDatabase
from fees.models import StudentFeeCollection
import calendar
import json
import holidays
from hijridate import Hijri
from pathlib import Path
from decimal import Decimal

def hijri_to_gregorian(year, month, day):
    for offset in [-1, 0, 1]:
        try:
            g = Hijri(year + offset, month, day).to_gregorian()
            if g.year == year:
                return g
        except Exception:
            continue
    return None


def student_calendar_form(request):
    today = timezone.localdate()
    now = timezone.now()

    year = int(request.GET.get('year') or today.year)
    month = int(request.GET.get('month') or today.month)
    month = month if 1 <= month <= 12 else today.month

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    cal = calendar.Calendar(firstweekday=6)
    month_days = list(cal.monthdayscalendar(year, month))
    weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    try:
        student = StudentDatabase.objects.get(student_userid=student_userid)
    except StudentDatabase.DoesNotExist:
        return redirect('student_login_view')

    # Calendar events
    future_events_qs = CalendarEvent.objects.filter(
        Q(date__gt=today) | Q(date=today, time__gte=now.time())
    )

    future_events = [{
        'id': e.id,
        'title': e.title,
        'description': e.description or '',
        'date': e.date.isoformat(),
        'time': e.time.strftime('%H:%M') if e.time else '',
        'event_type': '',  # Since event_type is removed
    } for e in future_events_qs]

    extra_events = []

    submitted_ids = AssignmentSubmission.objects.filter(
        student_userid=student_userid,
        student_status__in=['submitted', 'graded']
    ).values_list('assignment_id', flat=True)

    pending_assignments = Assignment.objects.filter(
        academic_year=student.academic_year,
        program_type=student.course_type,
        course=student.course,
        semester_number=student.semester or student.current_year,
        due_date__gte=today
    ).exclude(id__in=submitted_ids)

    for a in pending_assignments:
        if a.due_date >= today:
            extra_events.append({
                "title": f"Assignment Due: {a.title}",
                "date": a.due_date.isoformat(),
                "event_type": "AssignmentDue",
                "description": "",
                "url": "/student/assignments/"
            })

    borrow_records = BorrowRecord.objects.filter(student__student_userid=student_userid, returned=False)
    for br in borrow_records:
        if br.return_due_date:
            title = "Library Return Due" if br.return_due_date >= today else "Library Return Overdue!"
            extra_events.append({
                "title": title,
                "date": br.return_due_date.isoformat(),
                "event_type": "LibraryReturn",
                "description": "",
                # "url": reverse("book_borrow_details", args=[br.book.id])
            })

    fees = StudentFeeCollection.objects.filter(student_userid=student_userid).select_related('fee_type')
    grouped_fees = defaultdict(list)
    for fee in fees:
        key = (fee.fee_type_id, fee.due_date)
        grouped_fees[key].append(fee)

    for (fee_type_id, due_date), records in grouped_fees.items():
        latest_record = max(records, key=lambda x: x.id)
        amount = latest_record.amount or Decimal('0')
        total_paid = sum(Decimal(r.paid_amount or 0) for r in records)
        total_discount = sum(Decimal(getattr(r, 'applied_discount', 0) or 0) for r in records)
        balance = amount - total_paid - total_discount
        balance = max(balance, Decimal('0'))

        if balance <= Decimal('0.01'):
            continue

        if due_date:
            title = f"{latest_record.fee_type.name} Fee Due" if due_date >= today else f"{latest_record.fee_type.name} Fee Overdue!"
            extra_events.append({
                "title": title,
                "date": due_date.isoformat(),
                "event_type": "FeeDue",
                "description": "",
                "url": "/student/fees/"
            })

    india_holidays = holidays.India(years=year)
    all_holidays = [{"date": d, "name": n} for d, n in india_holidays.items() if d.year == year]

    fixed = {
        (1, 14): "Makara Sankranti", (4, 10): "Mahavir Jayanti", (4, 14): "Dr. Ambedkar Jayanti",
        (4, 18): "Good Friday", (4, 30): "Basava Jayanti", (5, 1): "May Day",
        (8, 15): "Independence Day", (10, 2): "Gandhi Jayanti",
        (11, 1): "Kannada Rajyotsava", (12, 25): "Christmas"
    }
    for (m, d), name in fixed.items():
        dt = date(year, m, d)
        if dt not in india_holidays:
            all_holidays.append({"date": dt, "name": name})

    islamic_dates = [
        (10, 1, "Eid al‑Fitr"),
        (12, 10, "Bakrid (Eid al‑Adha)"),
        (3, 12, "Eid Milad")
    ]
    for hijri_month, hijri_day, name in islamic_dates:
        g_date = hijri_to_gregorian(year, hijri_month, hijri_day)
        if g_date:
            all_holidays.append({"date": g_date, "name": name})

    try:
        json_path = Path(__file__).parent / "hindu_festivals.json"
        with open(json_path, 'r') as f:
            festival_data = json.load(f)
            for fest in festival_data.get(str(year), []):
                try:
                    dt = date(year, fest["month"], fest["day"])
                    all_holidays.append({"date": dt, "name": fest["name"]})
                except ValueError:
                    continue
    except Exception as e:
        print(f"Error loading Hindu festivals: {e}")

    month_holidays = [h for h in all_holidays if h["date"].month == month]

    filtered_extra_events = []
    for event in extra_events:
        if event['event_type'] in ['AssignmentDue', 'LibraryReturn', 'FeeDue']:
            event_date = date.fromisoformat(event['date'])
            if event_date.year == year and event_date.month == month:
                filtered_extra_events.append(event)
        else:
            filtered_extra_events.append(event)

    combined_events = future_events + filtered_extra_events

    # Build dictionary with dates as keys and list of event_types on that day as values
    event_days = defaultdict(list)
    for e in combined_events:
        event_days[e['date']].append(e['event_type'])

    context = {
        'today': today,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'month_days': month_days,
        'weekdays': weekdays,
        'events_json': json.dumps(combined_events, default=str),
        'gov_holidays_json': json.dumps([
            {"date": h["date"].isoformat(), "name": h["name"]} for h in all_holidays
        ]),
        'month_holidays': month_holidays,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'due_assignments_count': sum(1 for e in extra_events if e["event_type"] == "AssignmentDue"),
        'fee_due_count': sum(1 for e in extra_events if e["event_type"] == "FeeDue"),
        'upcoming_exams_count': 0,
        'total_events_count': len(combined_events),
        'due_date_types': ['AssignmentDue', 'LibraryReturn', 'FeeDue'],
        'combined_events': combined_events,
        'event_days': dict(event_days),  # Pass to template for highlighting
    }

    return render(request, 'lms/student_calendar.html', context)



# lms/views.py


from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

# lms/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .forms import StudentLeaveForm
from .models import StudentLeave
from attendence.models import StudentAttendance
from master.models import (
    EmployeeSubjectAssignment,
    CollegeStartEndPlan,
    Notification,
    Employee,
)
from lms.models import StudentNotification  # ✅ Import your model


# ✅ Utility: Get logged-in student from cookie
def get_logged_in_student(request):
    from master.models import StudentDatabase
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return None
    try:
        return StudentDatabase.objects.get(student_userid=student_userid)
    except StudentDatabase.DoesNotExist:
        return None


# ✅ CREATE Leave View + Student Notification
def student_leave_create(request):
    student = get_logged_in_student(request)
    if not student:
        return redirect('student_login_view')

    attendance_rate = 0.0
    attendance_allowed = False

    try:
        plan = CollegeStartEndPlan.objects.get(
            program_type=student.course_type,
            academic_year=student.academic_year,
            course=student.course,
            semester_number=student.semester or student.current_year
        )
        start_date = plan.start_date
        today = timezone.now().date()
        end_date = min(plan.end_date, today)

        attendance_qs = StudentAttendance.objects.filter(
            student=student,
            course=student.course,
            semester_number=student.semester or student.current_year,
            academic_year=student.academic_year,
            attendance_date__range=(start_date, end_date)
        )

        total_sessions = attendance_qs.count()
        attended_sessions = attendance_qs.filter(status__in=['present', 'late']).count()
        attendance_rate = round((attended_sessions / total_sessions) * 100, 2) if total_sessions > 0 else 0.0
        attendance_allowed = attendance_rate >= 75

    except CollegeStartEndPlan.DoesNotExist:
        attendance_allowed = True  # No plan = no restriction

    leaves = StudentLeave.objects.filter(student=student).order_by('-applied_on')

    if request.method == 'POST':
        form = StudentLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.student = student
            leave.status = 'pending'

            # ✅ Get Class Teacher
            class_teacher_assignment = EmployeeSubjectAssignment.objects.filter(
                course=student.course,
                semester=student.semester,
                is_class_teacher=True
            ).select_related('employee__user').first()

            if not class_teacher_assignment or not class_teacher_assignment.employee.user:
                messages.error(request, "No class teacher assigned.")
                return redirect('student_leave_create')

            leave.class_teacher = class_teacher_assignment.employee
            leave.save()

            # ✅ Create student-side notification
            StudentNotification.objects.create(
                student=student,
                title="Leave Request Submitted",
                message=f"You applied for leave from {leave.from_date} to {leave.to_date}.",
                url="",  # Optional: Add reverse() if you want to link to a leave view
                is_read=False
            )

            messages.success(request, "Leave request submitted successfully.")
            return redirect('student_leave_list')
    else:
        form = StudentLeaveForm()

    return render(request, 'lms/student_leave_form.html', {
        'form': form,
        'leaves': leaves,
        'attendance_allowed': attendance_allowed,
        'attendance_rate': attendance_rate,
        'today': timezone.now().date(),
    })


# ✅ EDIT Leave View + Student Notification
def student_leave_edit(request, pk):
    student = get_logged_in_student(request)
    if not student:
        return redirect('student_login_view')

    leave = get_object_or_404(StudentLeave, id=pk, student=student)

    if leave.from_date <= timezone.now().date():
        messages.error(request, "You can't edit this leave anymore.")
        return redirect('student_leave_list')

    attendance_rate = 0.0
    attendance_allowed = False

    try:
        plan = CollegeStartEndPlan.objects.get(
            program_type=student.course_type,
            academic_year=student.academic_year,
            course=student.course,
            semester_number=student.semester or student.current_year
        )
        start_date = plan.start_date
        today = timezone.now().date()
        end_date = min(plan.end_date, today)

        attendance_qs = StudentAttendance.objects.filter(
            student=student,
            course=student.course,
            semester_number=student.semester or student.current_year,
            academic_year=student.academic_year,
            attendance_date__range=(start_date, end_date)
        )

        total_sessions = attendance_qs.count()
        attended_sessions = attendance_qs.filter(status__in=['present', 'late']).count()
        attendance_rate = round((attended_sessions / total_sessions) * 100, 2) if total_sessions > 0 else 0.0
        attendance_allowed = attendance_rate >= 75

    except CollegeStartEndPlan.DoesNotExist:
        attendance_allowed = True

    if request.method == 'POST':
        form = StudentLeaveForm(request.POST, instance=leave)
        if form.is_valid():
            updated_leave = form.save(commit=False)
            updated_leave.status = 'pending'
            updated_leave.is_edited = True
            updated_leave.is_seen_by_teacher = False
            updated_leave.save()

            # ✅ Create student-side notification on edit
            StudentNotification.objects.create(
                student=student,
                title="Leave Request Edited",
                message=f"You updated your leave from {leave.from_date} to {leave.to_date}. Awaiting approval again.",
                url="",  # Optional: Add leave detail URL here
                is_read=False
            )

            messages.success(request, "Leave updated and sent for re-approval.")
            return redirect('student_leave_list')
    else:
        form = StudentLeaveForm(instance=leave)

    return render(request, 'lms/student_leave_form.html', {
        'form': form,
        'edit_mode': True,
        'leave': leave,
        'attendance_allowed': attendance_allowed,
        'attendance_rate': attendance_rate,
        'today': timezone.now().date(),
    })






from django.views.decorators.csrf import csrf_protect
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import StudentLeave

@csrf_protect
def student_leave_cancel(request, pk):
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('student_leave_list')

    student = get_logged_in_student(request)
    if not student:
        messages.error(request, "You must be logged in.")
        return redirect('student_login_view')

    leave = get_object_or_404(StudentLeave, id=pk, student=student)

    # ✅ Allow cancellation if leave is either approved or pending and in the future
    if leave.status in ['approved', 'pending'] and leave.from_date > timezone.localdate():
        leave.status = 'cancelled'
        leave.save()
        messages.success(request, "Leave request cancelled successfully.")
    else:
        messages.error(request, "This leave request cannot be cancelled.")

    return redirect('student_leave_list')




def student_leave_list(request):
    student = get_logged_in_student(request)
    if not student:
        return redirect('student_login_view')

    # ✅ Fetch only the logged-in student’s leave records
    leaves = StudentLeave.objects.filter(student=student).order_by('-applied_on')

    context = {
        'leaves': leaves,
        'today': timezone.now().date(),
    }

    return render(request, 'lms/student_leave_list.html', context)

# views.py

from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import StudentLeave
from master.models import Employee

def get_logged_in_employee(request):
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return None
    try:
        return Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return None

from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.db.models import Q
from .models import StudentLeave
from master.models import Employee, EmployeeSubjectAssignment

def leave_approval_list(request):
    employee_id = request.COOKIES.get('employee_id')
    if not employee_id:
        return HttpResponseForbidden("You are not authorized to view this page.")

    try:
        teacher = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return HttpResponseForbidden("Invalid user.")

    # ✅ Only get leaves where this teacher is explicitly assigned as class_teacher
    leaves = StudentLeave.objects.filter(
        class_teacher=teacher
    ).select_related('student', 'student__course').order_by('-applied_on')

    # ✅ Also fetch assignments to know which classes the teacher is class teacher for
    assignments = EmployeeSubjectAssignment.objects.filter(
        employee=teacher,
        is_class_teacher=True
    ).select_related('course', 'subject')

    # Unique class list (course + semester)
    unique_classes = {}
    for assignment in assignments:
        key = (assignment.course.id, assignment.semester)
        if key not in unique_classes:
            unique_classes[key] = assignment

    unique_class_list = list(unique_classes.values())

    return render(request, 'lms/leave_approval_list.html', {
        'leaves': leaves,
        'assignments': assignments,
        'unique_class_list': unique_class_list
    })





from lms.models import StudentNotification  # Add this import

def approve_leave(request, pk):
    teacher = get_logged_in_employee(request)
    if not teacher:
        return HttpResponseForbidden("You are not authorized to approve leave.")

    leave = get_object_or_404(StudentLeave, id=pk)

    is_class_teacher = EmployeeSubjectAssignment.objects.filter(
        employee=teacher,
        course=leave.student.course,
        semester=leave.student.semester,
        is_class_teacher=True
    ).exists()

    if not is_class_teacher:
        return HttpResponseForbidden("You are not authorized to approve this leave.")

    remarks = request.GET.get('remarks', '')

    leave.status = 'approved'
    leave.remarks = remarks
    if not leave.class_teacher:
        leave.class_teacher = teacher
    leave.save()

    # ✅ Create notification
    StudentNotification.objects.create(
        student=leave.student,
        title="Leave Approved",
        message=f"Your leave from {leave.from_date} to {leave.to_date} has been approved. Remarks: {remarks}",
        url='/student/leave/list/'  # or wherever the leave status is shown
    )

    messages.success(request, f"Leave request of {leave.student.student_name} has been approved.")
    return redirect('leave_approval_list')


def reject_leave(request, pk):
    teacher = get_logged_in_employee(request)
    if not teacher:
        return HttpResponseForbidden("You are not authorized to reject leave.")

    leave = get_object_or_404(StudentLeave, id=pk)

    is_class_teacher = EmployeeSubjectAssignment.objects.filter(
        employee=teacher,
        course=leave.student.course,
        semester=leave.student.semester,
        is_class_teacher=True
    ).exists()

    if not is_class_teacher:
        return HttpResponseForbidden("You are not authorized to reject this leave.")

    remarks = request.GET.get('remarks', '')

    leave.status = 'rejected'
    leave.remarks = remarks
    if not leave.class_teacher:
        leave.class_teacher = teacher
    leave.save()

    # ✅ Create notification
    StudentNotification.objects.create(
        student=leave.student,
        title="Leave Rejected",
        message=f"Your leave from {leave.from_date} to {leave.to_date} has been rejected. Remarks: {remarks}",
        url='/student/leave/list/'
    )

    messages.error(request, f"Leave request of {leave.student.student_name} has been rejected.")
    return redirect('leave_approval_list')







from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from master.models import Employee  # Adjust to your actual app & model
from django.utils import timezone

def employee_login_view(request):
    context = {}

    if request.method == 'POST':
        # Use the correct POST key matching your form's input name
        employee_userid = request.POST.get('employee_userid', '').strip()
        password = request.POST.get('password', '').strip()

        print(f"Received login attempt for employee_userid: '{employee_userid}' with password: '{password}'")  # DEBUG

        context['selected_user'] = employee_userid

        try:
            employee = Employee.objects.get(employee_userid=employee_userid)
            print(f"Found employee: {employee.employee_userid}")  # DEBUG

            if employee.is_locked:
                print("Account is locked.")  # DEBUG
                context['error'] = "Account is locked due to multiple failed attempts. Contact admin."
                return render(request, 'employee/employee_login.html', context)

            print(f"Stored password: '{employee.employee_password}'")  # DEBUG

            if employee.employee_password != password:
                print("Password mismatch.")  # DEBUG
                employee.wrong_attempts = (employee.wrong_attempts or 0) + 1
                if employee.wrong_attempts >= 3:
                    employee.is_locked = True
                    print("Account locked due to too many failed attempts.")  # DEBUG
                employee.save()
                context['error'] = "Invalid password."
                return render(request, 'lms/employee_login.html', context)

            # Successful login
            print("Password matched. Login successful.")  # DEBUG
            employee.wrong_attempts = 0
            employee.save()

            # Determine redirect URL
            if not employee.password_changed:
                redirect_url = reverse('employee_set_password')
            elif not employee.passcode_set:
                redirect_url = reverse('employee_set_passcode')
            else:
                redirect_url = reverse('employee_dashboard_view')

            response = HttpResponseRedirect(redirect_url)
            response.set_cookie('employee_id', employee.id)
            response.set_cookie('employee_userid', employee.employee_userid)
            response.set_cookie('employee_name', employee.name)  # Your model uses 'name', not employee_name

            return response

        except Employee.DoesNotExist:
            print(f"Employee with employee_userid '{employee_userid}' not found.")  # DEBUG
            context['error'] = "Invalid credentials."

    return render(request, 'lms/employee_login.html', context)



def employee_logout(request):
    request.session.flush()
    response = redirect('employee_login_view')
    response.delete_cookie('employee_id')
    response.delete_cookie('employee_userid')
    response.delete_cookie('employee_name')
    return response


def employee_set_password(request):
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    employee = Employee.objects.get(employee_userid=employee_userid)
    error = None

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            error = "Passwords do not match."
        elif len(new_password) < 8:
            error = "Password must be at least 8 characters."
        else:
            employee.employee_password = new_password
            employee.password_changed = True
            employee.save()
            return redirect('employee_set_passcode')

    return render(request, 'lms/employee_set_password.html', {
        'error': error,
        'selected_user': employee.employee_userid,
    })


def employee_set_passcode(request):
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    employee = Employee.objects.get(employee_userid=employee_userid)
    error = None

    if request.method == 'POST':
        passcode = request.POST.get('passcode')

        if not passcode.isdigit() or len(passcode) < 4:
            error = "Passcode must be at least 4 digits."
        else:
            employee.passcode = passcode
            employee.passcode_set = True
            employee.save()
            return redirect('employee_dashboard_view')

    return render(request, 'lms/employee_set_passcode.html', {'error': error})


from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta, datetime
import calendar
from django.contrib.auth.models import User  # Import User model

from .models import Employee, Assignment, EmployeeStudyMaterial
from attendence.models import StudentAttendance
from timetable.models import TimetableEntry
from master.models import Notification

def employee_dashboard_view(request):
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    # Try to get the corresponding User instance
    try:
        user = User.objects.get(username=employee.employee_userid)  # Adjust if needed
    except User.DoesNotExist:
        user = None

    filter_type = request.GET.get('filter', 'all')
    sections = request.GET.getlist('sections')
    if not sections:
        sections = ['student_attendance']

    now = timezone.now()
    today = now.date()

    if filter_type == 'day':
        start_date = end_date = today
    elif filter_type == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif filter_type == 'month':
        start_date = today.replace(day=1)
        end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    elif filter_type == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    else:
        start_date = end_date = None

    subject_ids = TimetableEntry.objects.filter(faculty=employee).values_list('subject_id', flat=True).distinct()
    attendance_qs = StudentAttendance.objects.filter(subject_id__in=subject_ids)
    if start_date and end_date:
        attendance_qs = attendance_qs.filter(attendance_date__range=(start_date, end_date))

    student_present = attendance_qs.filter(status='present').count()
    student_late = attendance_qs.filter(status='late').count()
    student_absent = attendance_qs.filter(status='absent').count()
    total_marked = student_present + student_late + student_absent
    student_attendance_rate = round(((student_present + student_late) / total_marked) * 100, 1) if total_marked else 0

    assignment_qs = Assignment.objects.filter(faculty=employee)
    if start_date and end_date:
        assignment_qs = assignment_qs.filter(created_at__date__range=(start_date, end_date))
    total_assignments = assignment_qs.count()

    material_qs = EmployeeStudyMaterial.objects.filter(faculty=employee)
    if start_date and end_date:
        material_qs = material_qs.filter(created_at__date__range=(start_date, end_date))
    total_study_materials = material_qs.count()

    classes_today = TimetableEntry.objects.filter(
        faculty=employee,
        day=today.strftime('%A')
    )

    # Notification logic
    if user:
        leave_notifications = Notification.objects.filter(
            user=user
        ).select_related('leave', 'leave__student').order_by('-timestamp')[:10]
    else:
        leave_notifications = Notification.objects.none()

    notifications = [
        {
            'type': 'leave',
            'title': note.message,
            'url': '/hr/leaves/',  # Change URL if needed
            'timestamp': note.timestamp
        }
        for note in leave_notifications
    ]

    notification_count = len(notifications)

    context = {
        'selected_filter': filter_type,
        'student_present': student_present if 'student_attendance' in sections else 0,
        'student_late': student_late if 'student_attendance' in sections else 0,
        'student_absent': student_absent if 'student_attendance' in sections else 0,
        'student_attendance_rate': student_attendance_rate if 'student_attendance' in sections else 0,
        'total_assignments': total_assignments,
        'total_study_materials': total_study_materials,
        'num_classes_today': classes_today.count(),
        'classes_today': classes_today,
        'notifications': notifications,
        'notification_count': notification_count,
    }

    return render(request, 'lms/employee_dashboard.html', context)








from django.shortcuts import render, redirect
import re

def employee_password_reset_view(request):
    context = {}
    username = request.GET.get('username') or request.POST.get('username')
    context['selected_user'] = username
    context['reset'] = True  # Indicate reset mode in template

    if request.method == 'POST':
        try:
            employee = Employee.objects.get(employee_userid=username)
        except Employee.DoesNotExist:
            context['error'] = "User does not exist."
            return render(request, 'lms/employee_login.html', context)

        # Step 1: Verify passcode
        if 'verify_passcode' in request.POST:
            input_passcode = request.POST.get('passcode', '').strip()
            if not employee.passcode_set or employee.passcode != input_passcode:
                context['error'] = "Incorrect passcode."
            else:
                context['passcode_verified'] = True  # Show password reset fields

        # Step 2: Reset password after passcode verified
        elif 'password_reset_submit' in request.POST:
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()

            pattern = r'^[A-Z][a-z]*[!@#$%^&*(),.?":{}|<>][a-zA-Z0-9]*[0-9]+$'

            if new_password != confirm_password:
                context['error'] = "Passwords do not match."
                context['passcode_verified'] = True
            elif not re.match(pattern, new_password) or not (8 <= len(new_password) <= 16):
                context['error'] = "Invalid password format."
                context['passcode_verified'] = True
            else:
                employee.employee_password = new_password
                employee.password_changed = True
                employee.save()
                context['success_message'] = "Password reset successfully."
                return redirect('employee_login_view')

    return render(request, 'lms/employee_login.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from master.models import StudentDatabase
from .models import StudentExamMarks, AssignmentSubmission, Exam

def student_certificate_view(request):
    student_userid = request.COOKIES.get('student_userid')
    if not student_userid:
        return redirect('student_login_view')

    student = get_object_or_404(StudentDatabase, student_userid=student_userid)

    # Fetch exam marks
    exam_marks = StudentExamMarks.objects.filter(student=student).select_related('subject', 'mark_type')

    # Fetch assignments
    assignments = AssignmentSubmission.objects.filter(student_userid=student_userid, student_status='graded').select_related('assignment')

    context = {
        "student": student,
        "exam_marks": exam_marks,
        "assignments": assignments,
        "generated_date": now().date()
    }
    return render(request, "lms/student_certificate.html", context)


from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee
from master.forms import BankDetailsForm

from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee
from master.forms import BankDetailsForm
 
def employee_profile(request):
 
    # Get employee_userid from cookies (not session)
    employee_userid = request.COOKIES.get("employee_userid")
 
    if not employee_userid:
        return redirect("employee_login_view")
 
    employee = get_object_or_404(Employee, employee_userid=employee_userid)
 
 
    if employee.bank_name and employee.ifsc_code and employee.bank_account_number:
        return render(
            request,
            "lms/employee_profile.html",
            {"employee": employee, "bank_form": None},
        )
 
 
    if request.method == "POST":
        form = BankDetailsForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect("employee_profile")
    else:
        form = BankDetailsForm(instance=employee)
 
    return render(
        request,
        "lms/employee_profile.html",
        {"employee": employee, "bank_form": form},
    )
 

from django.shortcuts import render, redirect
from django.utils import timezone
from calendar import monthrange
from datetime import date, timedelta
from master.models import Employee
from attendence.models import attendance
from hr.models import Leave  # assuming your Leave model is in hr app

from django.shortcuts import render, redirect
from django.utils import timezone
from calendar import monthrange
from datetime import date, timedelta
from master.models import Employee
from attendence.models import attendance
from hr.models import Leave  # make sure this import is correct

def employee_attendance_view(request):
    employee_userid = request.COOKIES.get("employee_userid")
    if not employee_userid:
        return redirect('employee_login_view')

    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')

    today = timezone.now().date()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))

    # Attendance records for this employee & month
    records = attendance.objects.filter(
        employee=employee,
        date__year=selected_year,
        date__month=selected_month
    ).order_by('date')

    # Approved leaves overlapping this month
    approved_leaves = Leave.objects.filter(
        employee=employee,
        is_approved=True,
        end_date__gte=date(selected_year, selected_month, 1)
    )

    # Map leave dates to their type
    leave_map = {}
    for leave in approved_leaves:
        current = leave.start_date
        while current <= leave.end_date:
            if current <= today:
                leave_map[current] = leave.leave_type
            current += timedelta(days=1)

    # Holidays with custom icons
    national_holidays = {
        (1, 26): {"name": "Republic Day", "icon": "🟧⚪🟩"},
        (4, 18): {"name": "Good Friday", "icon": "✝️"},
        (5, 1): {"name": "May Day", "icon": "🛠️"},
        (8, 15): {"name": "Independence Day", "icon": "🟧⚪🟩"},
        (10, 2): {"name": "Gandhi Jayanti", "icon": "🕊️"},
    }

    holiday_map = {}
    for (m, d), info in national_holidays.items():
        dt = date(selected_year, m, d)
        if dt.month == selected_month:
            holiday_map[dt] = info

    # Prepare summary counts
    present_count = records.filter(status="Present").count()
    late_count = records.filter(status="Late").count()
    absent_count = records.filter(status="Absent").count()
    leave_count = len(leave_map)

    summary = {
        "Present": present_count,
        "Late": late_count,
        "Absent": absent_count,
        "Leave": leave_count,
        "Total": records.count() + leave_count
    }

    # Map attendance by date
    attendance_map = {att.date: att.status for att in records}

    # Build calendar data
    days_in_month = monthrange(selected_year, selected_month)[1]
    calendar_data = []

    for day in range(1, days_in_month + 1):
        current_date = date(selected_year, selected_month, day)

        if current_date > today:
            status = ""
            leave_type = ""
            icon = ""
        elif current_date in attendance_map:
            # Attendance overrides leaves & holidays
            status = attendance_map[current_date]
            leave_type = ""
            icon = "✅" if status == "Present" else ("⏰" if status == "Late" else "❌")
        elif current_date in leave_map:
            status = "Leave"
            leave_type = leave_map[current_date]
            icon = "📝"
        elif current_date in holiday_map:
            status = "Holiday"
            leave_type = holiday_map[current_date]["name"]
            icon = holiday_map[current_date]["icon"]
        else:
            status = "Absent"
            leave_type = ""
            icon = "❌"

        calendar_data.append({
            "date": current_date,
            "status": status,
            "leave_type": leave_type,
            "icon": icon
        })

    # Month & Year dropdowns
    months = [{"num": i, "name": date(1900, i, 1).strftime("%B")} for i in range(1, 13)]
    year_list = [y for y in range(today.year, today.year - 10, -1)]

    context = {
        "employee": employee,
        "calendar_data": calendar_data,
        "summary": summary,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "months": months,
        "year_list": year_list,
        "month_name": date(1900, selected_month, 1).strftime("%B"),
    }

    return render(request, "lms/employee_attendance.html", context)



from django.shortcuts import render

def show_page(request):
    return render(request, "lms/mark_enter_dashboard.html")



from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Avg, Value, DecimalField
from django.db.models.functions import Coalesce
from lms.models import AssignmentSubmission, StudentExamMarks, ExamType
from master.models import StudentDatabase, CourseType, Course

def employee_all_student_view(request):
    selected_program_type = request.GET.get("program_type")
    selected_batch = request.GET.get("batch")
    selected_course = request.GET.get("course")
    selected_sem_year = request.GET.get("sem_year")
    selected_exam_type = request.GET.get("exam_type")   # ✅ new filter

    students = StudentDatabase.objects.all()

    if selected_program_type:
        students = students.filter(course_type_id=selected_program_type)
    if selected_batch:
        students = students.filter(academic_year=selected_batch)
    if selected_course:
        students = students.filter(course_id=selected_course)
    if selected_sem_year:
        students = students.filter(
            Q(semester=selected_sem_year) | Q(current_year=selected_sem_year)
        )

    data = []
    for student in students:
        assignment_qs = AssignmentSubmission.objects.filter(
            student_userid=student.student_userid,
            faculty_status="graded"
        )

        # ✅ apply exam type filter if selected
        if selected_exam_type:
            assignment_qs = assignment_qs.filter(assignment__exam_type_id=selected_exam_type)

        assignment_data = (
            assignment_qs
            .values("assignment__exam_type__title")
            .annotate(
                avg_score=Coalesce(
                    Avg("score"),
                    Value(0, output_field=DecimalField())
                )
            )
        )

        # Exam avg
        exam_qs = StudentExamMarks.objects.filter(
            student__student_userid=student.student_userid
        )
        if selected_exam_type:
            exam_qs = exam_qs.filter(mark_type_id=selected_exam_type)

        exams = exam_qs.aggregate(
            avg_score=Coalesce(Avg("marks_obtained"), Value(0, output_field=DecimalField()))
        )


        data.append({
            "student": student,
            "assignments": assignment_data,
            "exam_avg": exams["avg_score"],
        })

    # Dropdown sources
    program_types = CourseType.objects.all()
    exam_types = ExamType.objects.filter(is_active=True)   # ✅ new dropdown
    batches, courses, sem_years = [], [], []

    if selected_program_type:
        batches = (
            StudentDatabase.objects.filter(course__course_type_id=selected_program_type)
            .values_list("academic_year", flat=True).distinct().order_by("-academic_year")
        )

    courses = Course.objects.all()
    if selected_program_type:
        courses = courses.filter(course_type_id=selected_program_type)

    if selected_course:
        course = get_object_or_404(Course, id=selected_course)
        if course.total_semesters:
            sem_years = [{"id": i, "name": f"{course.name} {i}"} for i in range(1, course.total_semesters + 1)]
        else:
            sem_years = [{"id": i, "name": f"{course.name} {i}"} for i in range(1, course.duration_years + 1)]

    context = {
        "data": data,
        "program_types": program_types,
        "exam_types": exam_types,    # ✅ add to context
        "batches": batches,
        "courses": courses,
        "sem_years": sem_years,
        "selected": {
            "program_type": selected_program_type or "",
            "batch": selected_batch or "",
            "course": selected_course or "",
            "sem_year": selected_sem_year or "",
            "exam_type": selected_exam_type or "",   # ✅ track selected
        }
    }
    return render(request, "lms/employee_all_student_view.html", context)





#list
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from lms.models import FinalExamMarks, AssignmentSubmission
from master.models import StudentDatabase, Subject, Course, Employee
from master.models import EmployeeSubjectAssignment
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django import forms
class MarksEntryForm(forms.Form):
    max_marks = forms.IntegerField(
        required=False,
        initial=75,
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"})
    )
    marks_obtained = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
def student_marks_entry(request):
    # 1️⃣ Authenticate employee
    employee_userid = request.COOKIES.get("employee_userid")
    if not employee_userid:
        return redirect("employee_login_view")
 
    try:
        faculty = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect("employee_login_view")
 
    # 2️⃣ Assignments where employee is class teacher
    assignments = EmployeeSubjectAssignment.objects.filter(
        employee=faculty, is_class_teacher=True
    ).select_related("course", "course__course_type", "subject")
 
    if not assignments.exists():
        messages.error(request, "You are not assigned as class teacher for any class.")
        return render(request, "lms/student_marks_entry.html", {
            "students": [], "assignments": [], "course_types": [],
            "academic_years": [], "courses": [], "semesters": [],
            "subjects": [], "student_form_pairs": [], "selected": {}
        })
 
    # 3️⃣ Get filter selections
    selected_program_type_id = request.GET.get("course_type")
    selected_academic_year = request.GET.get("academic_year", "").replace("–", "-").strip()
    selected_course_id = request.GET.get("course")
    selected_semester_id = request.GET.get("semester")
    selected_subject_id = request.GET.get("subject")
 
    if selected_semester_id:
        try:
            selected_semester_id = str(int(selected_semester_id))
        except ValueError:
            selected_semester_id = ''
    else:
        selected_semester_id = ''
 
    # 4️⃣ Program Types
    program_types = sorted({a.course.course_type for a in assignments}, key=lambda x: x.name)
 
    # 5️⃣ Academic Years
    academic_years = list(
        StudentDatabase.objects.filter(
            course__in=[a.course for a in assignments],
            status="Active"
        ).values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    )
 
    # 6️⃣ Courses
    assigned_courses = {a.course.id: a.course for a in assignments}
    filtered_courses = [
        c for c in assigned_courses.values()
        if (not selected_program_type_id or str(c.course_type_id) == selected_program_type_id)
    ]
 
    # 7️⃣ Semesters
    semester_display = []
    if selected_course_id and int(selected_course_id) in assigned_courses:
        sems = sorted({str(a.semester) for a in assignments if str(a.course.id) == selected_course_id})
        course_name = assigned_courses[int(selected_course_id)].name
        semester_display = [{"id": s, "label": f"{course_name} {s}"} for s in sems]
 
    # 8️⃣ Subjects
    subjects = []
    if selected_course_id and selected_semester_id and selected_program_type_id and selected_academic_year:
        subjects = Subject.objects.filter(
            is_active=True,
            course_id=selected_course_id,
            semester=selected_semester_id,
            program_type_id=selected_program_type_id,
            academic_year__year=selected_academic_year
        ).order_by("name")
 
    # 9️⃣ Students
    students = []
    if selected_course_id and selected_semester_id and selected_academic_year:
        try:
            course = Course.objects.select_related("course_type").get(id=selected_course_id)
            course_type_name = course.course_type.name.lower()
        except Course.DoesNotExist:
            course_type_name = ""
 
        student_filter = {
            "course_id": selected_course_id,
            "academic_year": selected_academic_year,
            "status": "Active",
        }
        if "puc" in course_type_name:
            student_filter["current_year"] = selected_semester_id
        else:
            student_filter["semester"] = selected_semester_id
 
        students = StudentDatabase.objects.filter(**student_filter).order_by("student_name")
 
    # 🔟 Build student_form_pairs with best 2 internal exams
    student_form_pairs = []
    if selected_subject_id:
        subject_obj = Subject.objects.filter(id=selected_subject_id).first()
 
        for stu in students:
            # Gather all internal marks (excluding finals)
            mark_qs = StudentExamMarks.objects.filter(
                student=stu,
                subject_id=selected_subject_id,
                course_id=selected_course_id,
                semester_number=selected_semester_id,
                academic_year=selected_academic_year
            ).exclude(mark_type__title__icontains="final").select_related("mark_type")
 
            exam_mark_tuples = []
            for mark in mark_qs:
                # Use the actual max_marks stored with the mark, not from Exam table
                max_marks = mark.max_marks
                percent = (mark.marks_obtained / max_marks) if max_marks else 0
                exam_mark_tuples.append((mark.marks_obtained, max_marks, percent))
                # Print for debugging (optional, can remove after confirming correct output)
                print(f"Student: {stu.student_name}, MarkType: {mark.mark_type}, Obtained: {mark.marks_obtained}, Max: {max_marks}, Percent: {percent}")
 
            # Take best two by percentage
            best_two = sorted(
                exam_mark_tuples,
                key=lambda x: x[2],  # sort by percent
                reverse=True
            )[:2]
 
            print(f"Student: {stu.student_name}, Best Two: {best_two}")
 
            best_two_obtained = sum(x[0] for x in best_two)
            best_two_max = sum(x[1] for x in best_two)
 
            internal_max = 25
            internal_obtained = round((best_two_obtained / best_two_max) * internal_max) if best_two_max else 0
 
            print(f"Student: {stu.student_name}, Best2 Obtained: {best_two_obtained}, Best2 Max: {best_two_max}, Internal Obtained: {internal_obtained}")
 
            # ---- Final marks ----
            final_marks_obj = StudentExamMarks.objects.filter(
                student=stu,
                subject_id=selected_subject_id,
                mark_type__title__icontains="final",
                academic_year=selected_academic_year
            ).first()
 
            if final_marks_obj:
                form = MarksEntryForm(initial={
                    "max_marks": final_marks_obj.max_marks or 75,
                    "marks_obtained": final_marks_obj.marks_obtained
                })
            else:
                form = MarksEntryForm(initial={"max_marks": 75})
 
            pair = {
                "student": stu,
                "subject": subject_obj,
                "internal_max": internal_max,
                "internal_obtained": internal_obtained,
                "form": form
            }
            student_form_pairs.append(pair)
 
    # ⭐️ SAVE LOGIC FOR INTERNAL MARKS ⭐️
    if request.method == "POST" and selected_subject_id:
        for pair in student_form_pairs:
            student = pair["student"]
            subject = pair["subject"]
            internal_max = pair["internal_max"]
            internal_obtained = pair["internal_obtained"]
 
            academic_year_obj = None
            if selected_academic_year:
                academic_year_obj = AcademicYear.objects.filter(year=selected_academic_year).first()
 
            # Ensure ID types are correct
            program_type_id = int(selected_program_type_id) if selected_program_type_id else None
 
            # ✅ Get values directly from POST
            marks_obtained = request.POST.get(f"marks_obtained_{student.id}") or None
            max_marks = request.POST.get(f"max_marks_{student.id}") or 75
 
            if form.is_valid():
                marks_obtained = form.cleaned_data.get("marks_obtained")
                max_marks = form.cleaned_data.get("max_marks") or 75
            else:
                print("Form errors:", form.errors)  # debug
 
            FinalExamMarks.objects.update_or_create(
                student=student,
                subject=subject,
                course_id=selected_course_id,
                sem_year=selected_semester_id,
                academic_year=academic_year_obj,
                program_type_id=program_type_id,
                defaults={
                    "internal_max": internal_max,
                    "internal_obtained": internal_obtained,
                    "max_marks": max_marks,
                    "marks_obtained": marks_obtained,
                }
            )
        messages.success(request, "Internal marks saved!")
        return redirect("student_marks_list")  # 👈 redirect after save
 
    # Context
    context = {
        "assignments": assignments,
        "course_types": program_types,
        "academic_years": academic_years,
        "courses": filtered_courses,
        "semesters": semester_display,
        "subjects": subjects,
        "students": students,
        "student_form_pairs": student_form_pairs,
        "selected": {
            "program_type": selected_program_type_id,
            "academic_year": selected_academic_year,
            "course": selected_course_id,
            "semester": selected_semester_id,
            "subject": selected_subject_id,
        },
    }
    return render(request, "lms/student_marks_entry.html", context)




def student_marks_list(request):
    marks_list = FinalExamMarks.objects.select_related(
        "student", "subject", "course", "academic_year", "program_type", "assignment"
    ).order_by("student_id", "subject__name")  # ✅ order by student first

    context = {
        "marks_list": marks_list
    }
    return render(request, "lms/student_marks_list.html", context)




# =============================
#  VIEW Final Marks (Detail Page)
# =============================

def student_marks_view(request, pk):
    mark = get_object_or_404(FinalExamMarks.objects.select_related("student", "subject", "course"), pk=pk)

    return render(request, "lms/student_marks_entry.html", {
        "student_form_pairs": [{
            "student": mark.student,
            "subject": mark.subject,
            "internal_max": mark.internal_max,
            "internal_obtained": mark.internal_obtained,
            "form": None,  # no form in view mode
            "mark_obj": mark,
        }],
        "view_only": True,
    })


# =============================
#  EDIT Final Marks (Update Page)
# =============================

def student_marks_edit(request, pk):
    mark = get_object_or_404(FinalExamMarks, pk=pk)

    if request.method == "POST":
        form = MarksEntryForm(request.POST, instance=mark)
        if form.is_valid():
            form.save()
            messages.success(request, "Marks updated successfully!")
            return redirect("student_marks_list")
    else:
        form = MarksEntryForm(instance=mark)

    return render(request, "lms/student_marks_entry.html", {
        "form": form,
        "mark_obj": mark,
        "edit_mode": True,  # 👈 use in template
    })


# =============================
#  DELETE Final Marks
# =============================

def student_marks_delete(request, pk):
    mark = get_object_or_404(FinalExamMarks, pk=pk)

    if request.method == "POST":  # Confirm delete
        mark.delete()
        messages.success(request, "Marks deleted successfully!")
        return redirect("student_marks_list")

    return render(request, "lms/student_marks_list.html", {
        "delete_obj": mark
    })




from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.timezone import now

from .models import FinalExamMarks
from master.models import StudentDatabase


def student_marksheet_view(request, student_id):
    student = get_object_or_404(StudentDatabase, id=student_id)
    exam_marks = FinalExamMarks.objects.filter(student=student).select_related("subject")

    context = {
        "student": student,
        "exam_marks": exam_marks,
        "generated_date": now().strftime("%d-%m-%Y"),
    }
    return render(request, "lms/student_marksheet.html", context)


from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from .models import FinalExamMarks
from master.models import StudentDatabase


def student_marksheet_pdf(request, student_id):
    student = get_object_or_404(StudentDatabase, id=student_id)
    exam_marks = FinalExamMarks.objects.filter(student=student).select_related("subject")

    html_string = render_to_string("lms/student_marksheet.html", {
        "student": student,
        "exam_marks": exam_marks,
        "generated_date": now().strftime("%d-%m-%Y"),
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="marksheet_{student.student_userid}.pdf"'

    HTML(string=html_string).write_pdf(response)
    return response



# For student-facing library view
from .models import Book

def student_book_list(request):
    books = Book.objects.filter(status='active').order_by('-id')  # Only available books
    return render(request, 'lms/student_book_list.html', {'books': books})

def student_book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'lms/student_book_detail.html', {'book': book})


from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee

def employee_change_password(request):
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login')

    employee = get_object_or_404(Employee, employee_userid=employee_userid)
    error = None
    success = None

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if old_password != employee.employee_password:
            error = "Old password is incorrect."
        elif new_password != confirm_password:
            error = "New passwords do not match."
        elif len(new_password) < 8:
            error = "New password must be at least 8 characters."
        else:
            employee.employee_password = new_password
            employee.save()
            success = "Password updated successfully."

    return render(request, 'lms/employee_change_password.html', {
        'error': error,
        'success': success
    })


def employee_change_passcode(request):
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login')

    employee = get_object_or_404(Employee, employee_userid=employee_userid)
    error = None
    success = None

    if request.method == 'POST':
        old_passcode = request.POST.get('old_passcode')
        new_passcode = request.POST.get('new_passcode')
        confirm_passcode = request.POST.get('confirm_passcode')

        if old_passcode != employee.passcode:
            error = "Old passcode is incorrect."
        elif new_passcode != confirm_passcode:
            error = "New passcodes do not match."
        elif not new_passcode.isdigit() or len(new_passcode) < 4:
            error = "New passcode must be at least 4 digits."
        else:
            employee.passcode = new_passcode
            employee.save()
            success = "Passcode updated successfully."

    return render(request, 'lms/employee_change_passcode.html', {
        'error': error,
        'success': success
    })


def settings_view(request):
    return render(request, 'lms/settings.html')