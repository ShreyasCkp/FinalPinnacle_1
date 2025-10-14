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

   #  # 🔔 Leave Notifications (from faculty)
   # # 🔔 Leave Notifications (from faculty)
   #  leave_notifications = StudentNotification.objects.filter(
   #  student=student,
   #  is_read=False
   #  ).order_by('-created_at')[:5]


    # for note in leave_notifications:
    #     notifications.append({
    #         'type': 'leave',
    #         'title': note.title,
    #         'message': note.message,
    #         'url': f'/student/notification/read/{note.id}/',  # ✅ This won't change
    #     })



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

    # --- Build daily_receipts like parent view ---
    receipt_dict = defaultdict(list)
    for payment in all_fees:
        if payment.receipt_no:  # Only include valid receipts
            receipt_dict[payment.receipt_no].append(payment)

    daily_receipts = []
    for receipt_no, transactions in receipt_dict.items():
        if not transactions:
            continue  # skip if no transactions

        first_txn = transactions[0]  # 👈 use the first transaction

        fee_types = ", ".join([t.fee_type.name for t in transactions if t.fee_type])

        daily_receipts.append({
            'admission_no': first_txn.admission_no,   # ✅ fixed
            'receipt_no': receipt_no,
            'receipt_date': first_txn.receipt_date,
            'fee_types': fee_types,
            'transactions': transactions,
        })


    context = {
        'fee_collections': fee_display_list,
        'total_fees': total_fees,
        'collected': total_collected,
        'pending': total_pending,
        'overdue': total_overdue,
        'overdue_fee_types': sorted(overdue_fee_types),  # pass sorted list to template
        'daily_receipts': daily_receipts,  # 👈 now available in template
    }

    return render(request, 'lms/my_fee.html', context)


# from django.http import HttpResponse
# from django.template.loader import get_template
# from django.db.models import Q
# from weasyprint import HTML
# from master.models import StudentDatabase
# from fees.models import StudentFeeCollection


# def student_fee_receipt(request, admission_no, receipt_no):
#     # Fetch all transactions for this receipt
#     transactions = StudentFeeCollection.objects.filter(
#         admission_no=admission_no,
#         receipt_no=receipt_no
#     )

#     if not transactions.exists():
#         return HttpResponse("Receipt not found", status=404)

#     # Fetch student
#     student = StudentDatabase.objects.filter(
#         Q(pu_admission__admission_no=admission_no) |
#         Q(degree_admission__admission_no=admission_no)
#     ).first()

#     if not student:
#         return HttpResponse("Student not found", status=404)

#     # Prepare fee rows + totals
#     fees = []
#     total_amount = total_paid = total_discount = total_balance = 0
#     for txn in transactions:
#         fees.append({
#             "name": txn.fee_type.name if txn.fee_type else "",
#             "due_date": txn.due_date,
#             "amount": txn.amount,
#             "paid": txn.paid_amount,
#             "discount": getattr(txn, "applied_discount", 0),
#             "balance": txn.balance_amount,
#         })
#         total_amount += txn.amount
#         total_paid += txn.paid_amount
#         total_discount += getattr(txn, "applied_discount", 0)
#         total_balance += txn.balance_amount

#     # Context for template
#     context = {
#         "student": student,
#         "admission_no": student.get_admission_no(),
#         "year_display": student.current_year or student.semester,
#         "receipt": {
#             "receipt_no": receipt_no,
#             "date": transactions[0].receipt_date,
#             "mode_of_payment": transactions[0].payment_mode,
#             "status": "Paid" if total_paid > 0 else transactions[0].status,
#             "fees": fees,
#             "total_amount": total_amount,
#             "total_paid": total_paid,
#             "total_due": total_balance,
#         },
#     }

#     # Render template to HTML
#     template = get_template("lms/student_fee_download.html")
#     html_string = template.render(context)

#     # Generate PDF with WeasyPrint (important: base_url for images/fonts)
#     pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()

#     # Return as downloadable PDF
#     response = HttpResponse(pdf, content_type="application/pdf")
#     response["Content-Disposition"] = f'attachment; filename="receipt_{receipt_no}.pdf"'
#     return response



import os
from django.http import HttpResponse
from django.template.loader import get_template
from django.db.models import Q
from master.models import StudentDatabase
from fees.models import StudentFeeCollection
import pdfkit
from django.conf import settings


def student_fee_receipt(request, admission_no, receipt_no):
    # Fetch all transactions for this receipt
    transactions = StudentFeeCollection.objects.filter(
        admission_no=admission_no,
        receipt_no=receipt_no
    )

    if not transactions.exists():
        return HttpResponse("Receipt not found", status=404)

    # Fetch student
    student = StudentDatabase.objects.filter(
        Q(pu_admission__admission_no=admission_no) |
        Q(degree_admission__admission_no=admission_no)
    ).first()

    if not student:
        return HttpResponse("Student not found", status=404)

    # Prepare fee rows + totals
    fees = []
    total_amount = total_paid = total_discount = total_balance = 0
    for txn in transactions:
        fees.append({
            "name": txn.fee_type.name if txn.fee_type else "",
            "due_date": txn.due_date,
            "amount": txn.amount,
            "paid": txn.paid_amount,
            "discount": getattr(txn, "applied_discount", 0),
            "balance": txn.balance_amount,
        })
        total_amount += txn.amount
        total_paid += txn.paid_amount
        total_discount += getattr(txn, "applied_discount", 0)
        total_balance += txn.balance_amount

    # Context for template
    context = {
        "student": student,
        "admission_no": student.get_admission_no(),
        "year_display": student.current_year or student.semester,
        "receipt": {
            "receipt_no": receipt_no,
            "date": transactions[0].receipt_date,
            "mode_of_payment": transactions[0].payment_mode,
            "status": "Paid" if total_paid > 0 else transactions[0].status,
            "fees": fees,
            "total_amount": total_amount,
            "total_paid": total_paid,
            "total_due": total_balance,
        },
    }

    # Render HTML template
    template = get_template("lms/student_fee_download.html")
    html_string = template.render(context)

    # ✅ Set correct wkhtmltopdf path
    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

    # ✅ PDF options
    options = {
        "page-size": "A5",
        "encoding": "UTF-8",
        "enable-local-file-access": True,
        "zoom": "1.25",
        "no-outline": None,
        "margin-top": "0.2in",
        "margin-bottom": "0.2in",
        "margin-left": "0.2in",
        "margin-right": "0.2in",
        "print-media-type": True,
        "load-error-handling": "ignore",
    }

    # ✅ Generate PDF
    pdf = pdfkit.from_string(html_string, False, configuration=config, options=options)

    # ✅ Return as downloadable PDF
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="receipt_{receipt_no}.pdf"'
    return response




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
    # Stats
    pending = sum(
        1 for a in assignments
        if not submissions_dict.get(a.id)
        or submissions_dict[a.id].student_status in ['pending', 'in_progress', 'rejected', 'review']
    )

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


#parent Login

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from admission.models import ConfirmedAdmission

# ---------------- Parent Login -----------------
def parent_login_view(request):
    context = {}

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        context['selected_user'] = username

        try:
            parent = ConfirmedAdmission.objects.get(parent_userid=username)

            if parent.parent_is_locked:
                context['error'] = "Account is locked due to multiple failed attempts. Contact admin."
                return render(request, 'lms/parent_login.html', context)

            if parent.parent_password != password:
                parent.parent_wrong_attempts += 1
                if parent.parent_wrong_attempts >= 3:
                    parent.parent_is_locked = True
                parent.save()
                context['error'] = "Invalid password."
                return render(request, 'lms/parent_login.html', context)

            # Reset wrong attempts on success
            parent.parent_wrong_attempts = 0
            parent.save()

            # Determine redirect URL first
            if not parent.parent_password_changed:
                redirect_url = reverse('parent_set_password')
            elif not parent.parent_passcode_set:
                redirect_url = reverse('parent_set_passcode')
            else:
                redirect_url = reverse('parent_dashboard')

            # Create response and set cookies
            response = HttpResponseRedirect(redirect_url)
            response.set_cookie('parent_id', parent.id)
            response.set_cookie('parent_userid', parent.parent_userid)
            response.set_cookie('parent_name', parent.pu_admission.student_name if parent.pu_admission else parent.degree_admission.student_name)
            return response

        except ConfirmedAdmission.DoesNotExist:
            context['error'] = "Invalid credentials."

    return render(request, 'lms/parent_login.html', context)


def parent_logout(request):
    request.session.flush()
    response = redirect('parent_login_view')
    response.delete_cookie('parent_id')
    response.delete_cookie('parent_userid')
    response.delete_cookie('parent_name')
    return response


def parent_set_password(request):
    parent_userid = request.COOKIES.get('parent_userid')
    if not parent_userid:
        return redirect('parent_login_view')

    parent = ConfirmedAdmission.objects.get(parent_userid=parent_userid)
    error = None

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            error = "Passwords do not match."
        elif len(new_password) < 8:
            error = "Password must be at least 8 characters."
        else:
            parent.parent_password = new_password
            parent.parent_password_changed = True
            parent.save()
            return redirect('parent_set_passcode')

    return render(request, 'lms/parent_set_password.html', {
        'error': error,
        'selected_user': parent.parent_userid
    })


def parent_set_passcode(request):
    parent_userid = request.COOKIES.get('parent_userid')
    if not parent_userid:
        return redirect('parent_login_view')

    parent = ConfirmedAdmission.objects.get(parent_userid=parent_userid)
    error = None

    if request.method == 'POST':
        passcode = request.POST.get('passcode')

        if not passcode.isdigit() or len(passcode) < 4:
            error = "Passcode must be at least 4 digits."
        else:
            parent.parent_passcode = passcode
            parent.parent_passcode_set = True
            parent.save()
            return redirect('parent_dashboard')

    return render(request, 'lms/parent_set_passcode.html', {'error': error})


def parent_change_password(request):
    parent_userid = request.COOKIES.get('parent_userid')
    if not parent_userid:
        return redirect('parent_login_view')

    parent = ConfirmedAdmission.objects.get(parent_userid=parent_userid)
    error = None
    success = None

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if old_password != parent.parent_password:
            error = "Old password is incorrect."
        elif new_password != confirm_password:
            error = "New passwords do not match."
        elif len(new_password) < 8:
            error = "New password must be at least 8 characters."
        else:
            parent.parent_password = new_password
            parent.save()
            success = "Password updated successfully."

    return render(request, 'lms/parent_change_password.html', {
        'error': error,
        'success': success
    })


def parent_change_passcode(request):
    parent_userid = request.COOKIES.get('parent_userid')
    if not parent_userid:
        return redirect('parent_login_view')

    parent = ConfirmedAdmission.objects.get(parent_userid=parent_userid)
    error = None
    success = None

    if request.method == 'POST':
        old_passcode = request.POST.get('old_passcode')
        new_passcode = request.POST.get('new_passcode')
        confirm_passcode = request.POST.get('confirm_passcode')

        if old_passcode != parent.parent_passcode:
            error = "Old passcode is incorrect."
        elif new_passcode != confirm_passcode:
            error = "New passcodes do not match."
        elif not new_passcode.isdigit() or len(new_passcode) < 4:
            error = "New passcode must be at least 4 digits."
        else:
            parent.parent_passcode = new_passcode
            parent.save()
            success = "Passcode updated successfully."

    return render(request, 'lms/parent_change_passcode.html', {
        'error': error,
        'success': success
    })


def parent_password_reset_view(request):
    context = {}
    username = request.GET.get('username') or request.POST.get('username')
    context['selected_user'] = username
    context['reset'] = True  # tell the template we are in reset mode

    from .models import ParentDatabase  # or wherever parent info is stored

    if request.method == 'POST':
        try:
            parent = ParentDatabase.objects.get(parent_userid=username)
        except ParentDatabase.DoesNotExist:
            context['error'] = "User does not exist."
            return render(request, 'lms/parent_login.html', context)

        # Step 1: Verify passcode
        if 'verify_passcode' in request.POST:
            input_passcode = request.POST.get('passcode', '').strip()
            if not parent.passcode_set or parent.passcode != input_passcode:
                context['error'] = "Incorrect passcode."
            else:
                context['passcode_verified'] = True  # show new password fields

        # Step 2: Reset password after passcode verified
        elif 'password_reset_submit' in request.POST:
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()

            import re
            pattern = r'^[A-Z][a-z]*[!@#$%^&*(),.?":{}|<>][a-zA-Z0-9]*[0-9]+$'

            if new_password != confirm_password:
                context['error'] = "Passwords do not match."
                context['passcode_verified'] = True
            elif not re.match(pattern, new_password) or not (8 <= len(new_password) <= 16):
                context['error'] = "Invalid password format."
                context['passcode_verified'] = True
            else:
                parent.parent_password = new_password
                parent.password_changed = True
                parent.save()
                context['success_message'] = "Password reset successfully."
                return redirect('parent_login_view')

    return render(request, 'lms/parent_login.html', context)


from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count

from lms.models import Assignment, AssignmentSubmission, Exam
from master.models import StudentDatabase, CollegeStartEndPlan
from attendence.models import StudentAttendance
from admission.models import ConfirmedAdmission


def parent_dashboard(request):

    parent_userid = request.COOKIES.get('parent_userid')

    if not parent_userid:

        return redirect('parent_login_view')
 
    try:

        confirmed_student = ConfirmedAdmission.objects.get(parent_userid=parent_userid)

    except ConfirmedAdmission.DoesNotExist:

        return redirect('parent_login_view')
 
    # get the student record linked by student_userid

    try:

        student = StudentDatabase.objects.get(student_userid=confirmed_student.student_userid)

    except StudentDatabase.DoesNotExist:

        return redirect('parent_login_view')
 
    # --- Parent Name logic based on primary_guardian ---

    parent_name = None

    if confirmed_student.pu_admission:

        pu = confirmed_student.pu_admission

        if pu.primary_guardian == "father":

            parent_name = pu.father_name

        elif pu.primary_guardian == "mother":

            parent_name = pu.mother_name

        elif pu.primary_guardian == "guardian":

            parent_name = pu.guardian_name

    elif confirmed_student.degree_admission:

        deg = confirmed_student.degree_admission

        if deg.primary_guardian == "father":

            parent_name = deg.father_name

        elif deg.primary_guardian == "mother":

            parent_name = deg.mother_name

        elif deg.primary_guardian == "guardian":

            parent_name = deg.guardian_name
 
    # === Academic Info ===

    today = timezone.now().date()

    semester = student.semester or student.current_year

    assignments = Assignment.objects.filter(

        academic_year=student.academic_year,

        program_type=student.course_type,

        course=student.course,

        semester_number=semester

    )
 
    submissions = AssignmentSubmission.objects.filter(

        student_userid=student.student_userid,

        assignment__in=assignments

    )

    submissions_dict = {sub.assignment_id: sub for sub in submissions}

    submitted_ids = set(submissions_dict.keys())
 
    pending_assignments = sum(1 for a in assignments if a.id not in submitted_ids)
 
    # Assignments due this week

    end_week = today + timedelta(days=7)

    due_this_week = assignments.filter(due_date__range=(today, end_week)).count()
 
    # === GPA / Score ===

    average_score = submissions.filter(student_status='graded').aggregate(

        avg_score=Avg('score')

    )['avg_score'] or 0.0
 
    # === Attendance Calculation ===

    attendance_rate = 0.0

    total_sessions = 0

    attended_sessions = 0
 
    try:

        plan = CollegeStartEndPlan.objects.get(

            program_type=student.course_type,

            academic_year=student.academic_year,

            course=student.course,

            semester_number=semester

        )
 
        start_date = plan.start_date

        end_date = min(plan.end_date, today)
 
        attendance_qs = StudentAttendance.objects.filter(

            student=student,

            course=student.course,

            semester_number=semester,

            academic_year=student.academic_year,

            attendance_date__range=(start_date, end_date)

        )
 
        total_sessions = attendance_qs.count()

        attended_sessions = attendance_qs.filter(status__in=['present', 'late']).count()
 
        attendance_rate = round((attended_sessions / total_sessions) * 100, 2) if total_sessions > 0 else 0.0
 
    except CollegeStartEndPlan.DoesNotExist:

        pass
 
    # === Notifications (same as student dashboard, keep as-is) ===

    assignments_due = assignments.filter(due_date__gte=today).annotate(

        submitted_count=Count('submissions')

    )

    assignment_notifications = assignments_due.filter(submitted_count=0)
 
    exam_notifications = Exam.objects.filter(

        course=student.course,

        exam_date__range=(today, today + timedelta(days=30))

    )
 
    notifications = []
 
    for assignment in assignment_notifications:

        notifications.append({

            'type': 'assignment',

            'title': f"Assignment due on {assignment.due_date.strftime('%d %b')}",

            'url': '/parent/assignments/',

        })
 
    for exam in exam_notifications:

        days_until_exam = (exam.exam_date - today).days

        if days_until_exam in [7, 30]:

            label = f"{exam.subject.name} exam on {exam.exam_date.strftime('%d %b')} (in {days_until_exam} days)"

        else:

            label = f"{exam.subject.name} exam on {exam.exam_date.strftime('%d %b')}"

        notifications.append({

            'type': 'exam',

            'title': label,

            'url': '/parent/grades/',

        })
 
    # === Fee Summary (reused from parent_fee_view) ===
    is_pu = student.pu_admission is not None
    admission = student.pu_admission if is_pu else student.degree_admission if student.degree_admission else None

    admission_no = admission.admission_no if admission else None
    academic_year_obj = AcademicYear.objects.filter(year=student.academic_year).first()

    # Always check last available period for dashboard summary
    if is_pu:
        selected_period = student.current_year or 1
    else:
        selected_period = student.semester or 1

    fee_decl_query = {
        "academic_year": academic_year_obj,
        "course_type": student.course_type,
        "course": student.course,
        "semester": selected_period,
    }
    fee_decl = FeeDeclaration.objects.filter(**fee_decl_query).first()

    # Determine selected period
    if is_pu:
        selected_period = student.current_year or 1
    else:
        selected_period = student.semester or 1

    # Try fetching FeeDeclaration based on semester/year
    fee_decl = FeeDeclaration.objects.filter(
        academic_year=academic_year_obj,
        course_type=student.course_type,
        course=student.course,
    ).filter(
        # For PU: match current_year; For Degree: match semester
        semester=selected_period if not is_pu else None
    ).filter(
        current_year=selected_period if is_pu else None
    ).first()

    # Calculate Fee KPI totals
    total_fee = 0
    paid_fee = 0
    due_fee = 0
    fee_status = "N/A"

    if fee_decl:
        for fee in fee_decl.fee_details.all():
            declared = fee.amount or 0
            total_fee += declared

            # Fetch all payments for this fee type & admission_no
            all_payments = StudentFeeCollection.objects.filter(
                admission_no=admission_no,
                fee_type=fee.fee_type
            )
            paid_sum = all_payments.aggregate(total=Sum('paid_amount'))['total'] or 0
            paid_fee += paid_sum

        due_fee = total_fee - paid_fee
        fee_status = "Paid" if due_fee <= 0 else "Due"

    # === Context ===
    context = {
        'student': student,
        'confirmed_student': confirmed_student,
        'parent_name': parent_name,
        'logged_in_parent': confirmed_student,
        'parent_userid': parent_userid,

        # Cards
        'pending_assignments': pending_assignments,
        'due_this_week': due_this_week,
        'current_gpa': round(average_score, 2),
        'attendance_rate': attendance_rate,

        # Fee Card
        'fee_status': fee_status,
        'due_fee': due_fee,
        'paid_fee': paid_fee,
        'total_fee': total_fee,

        # Notifications
        'notifications': notifications,
        'notification_count': len(notifications),
    }

    return render(request, 'lms/parent_dashboard.html', context)

#parent dashboard

from django.shortcuts import render

def show_page(request):
    return render(request, "lms/parent_dashboard.html")



from django.shortcuts import render, get_object_or_404, redirect
from admission.models import ConfirmedAdmission
from master.models import StudentDatabase
from attendence.models import StudentAttendance
from timetable.models import TimetableEntry
from fees.models import StudentFeeCollection
from collections import defaultdict
from datetime import date
from decimal import Decimal
import calendar

WEEKDAY_MAP = {
    0: 'Monday', 1: 'Tuesday', 2: 'Wednesday',
    3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
}

def parent_attendance_view(request):
    parent_id = request.COOKIES.get('parent_id')
    if not parent_id:
        return redirect("parent_login")

    parent = get_object_or_404(ConfirmedAdmission, id=parent_id)
    student = get_object_or_404(StudentDatabase, student_userid=parent.student_userid)

    months = [
        (5, 'May'), (6, 'Jun'), (7, 'Jul'), (8, 'Aug'), (9, 'Sep'), (10, 'Oct'),
        (11, 'Nov'), (12, 'Dec'), (1, 'Jan'), (2, 'Feb'), (3, 'Mar'), (4, 'Apr')
    ]

    attendance_grid = []
    total_present = total_late = total_absent = total_holiday = total_weekend = 0
    total_classes = total_attended_classes = 0

    today = date.today()
    current_year = today.year
    start_year = current_year - 1 if today.month < 5 else current_year
    start_date = date(start_year, 5, 1)
    end_date = date(start_year + 1, 4, 30)

    records = StudentAttendance.objects.filter(
        student=student,
        attendance_date__range=(start_date, end_date)
    )

    attendance_by_date = defaultdict(list)
    for record in records:
        attendance_by_date[record.attendance_date].append(record)

    timetable_entries = TimetableEntry.objects.filter(
        course=student.course,
        semester_number=getattr(student, 'semester_number', 1)
    )

    timetable_by_day = defaultdict(list)
    for entry in timetable_entries:
        timetable_by_day[entry.day].append(entry)

    valid_days_per_month = {}
    for m, _ in months:
        y = start_year if m >= 5 else start_year + 1
        valid_days_per_month[m] = calendar.monthrange(y, m)[1]

    for day in range(1, 32):
        if not any(day <= valid_days_per_month[m] for m, _ in months):
            continue

        row = []
        for m, _ in months:
            y = start_year if m >= 5 else start_year + 1
            try:
                current_date = date(y, m, day)
            except ValueError:
                row.append('')
                continue

            if current_date > today:
                row.append('')
                continue

            weekday = current_date.weekday()
            weekday_name = WEEKDAY_MAP[weekday]

            if weekday in [5, 6]:  # Weekend
                row.append('W')
                total_weekend += 1
                continue

            scheduled_classes = timetable_by_day.get(weekday_name, [])
            class_count = len(scheduled_classes)

            if class_count == 0:
                row.append('H')
                total_holiday += 1
                continue

            attended_count = 0
            records_today = attendance_by_date.get(current_date, [])
            for sched_class in scheduled_classes:
                if any(r.subject == sched_class.subject and r.status in ['present', 'late'] for r in records_today):
                    attended_count += 1

            total_classes += class_count
            total_attended_classes += attended_count

            if attended_count > 0:
                percentage = round((attended_count / class_count) * 100)
                row.append(f'P ({percentage}%)')
                total_present += 1
            else:
                row.append('A (0%)')
                total_absent += 1

        attendance_grid.append({'day': day, 'statuses': row})

    total_late = records.filter(status='L').count()
    attendance_percentage = round((total_attended_classes / total_classes) * 100, 2) if total_classes else 0

    context = {
        "student": student,
        "months": months,
        "attendance_grid": attendance_grid,
        "total_present": total_present,
        "total_late": total_late,
        "total_absent": total_absent,
        "total_holiday": total_holiday,
        "total_weekend": total_weekend,
        "attendance_percentage": attendance_percentage,
        "logged_in_parent": parent
    }
    return render(request, "lms/parent_attendance.html", context)



from django.shortcuts import render, get_object_or_404
from master.models import StudentDatabase
from lms.models import FinalExamMarks
from admission.models import ConfirmedAdmission

def parent_marksheet_download(request):
    # Get logged-in parent
    parent_userid = request.COOKIES.get('parent_userid')
    if not parent_userid:
        return redirect('parent_login_view')

    # Get confirmed student linked to parent
    try:
        confirmed_student = ConfirmedAdmission.objects.get(parent_userid=parent_userid)
    except ConfirmedAdmission.DoesNotExist:
        return redirect('parent_login_view')

    # Get student record
    try:
        student = StudentDatabase.objects.get(student_userid=confirmed_student.student_userid)
    except StudentDatabase.DoesNotExist:
        return redirect('parent_login_view')

    # Check if student has marks
    has_marks = FinalExamMarks.objects.filter(student=student).exists()

    context = {
        "student": student,
        "has_marks": has_marks,
    }

    return render(request, "lms/parent_marksheet_download.html", context)





from django.shortcuts import render, redirect
from fees.models import StudentFeeCollection, FeeDeclaration, FeeDeclarationDetail
from admission.models import ConfirmedAdmission
from master.models import StudentDatabase
from django.contrib import messages
from django.db.models import Q

def parent_fee_view(request):
    parent_userid = request.COOKIES.get("parent_userid")
    if not parent_userid:
        return redirect("parent_login_view")

    # Get student
    try:
        confirmed_student = ConfirmedAdmission.objects.get(parent_userid=parent_userid)
        student = StudentDatabase.objects.get(student_userid=confirmed_student.student_userid)
    except (ConfirmedAdmission.DoesNotExist, StudentDatabase.DoesNotExist):
        return redirect("parent_login_view")

    # Determine admission type (PU or Degree)
    is_pu = student.pu_admission is not None
    admission = student.pu_admission if is_pu else student.degree_admission if student.degree_admission else None
    parent_name = admission.parent_name() if admission else ""
    parent_email = admission.parent_email() if admission else ""
    parent_phone = admission.parent_phone() if admission else ""
    parent_adhar = admission.parent_adhar() if admission else ""
    parent_occupation = admission.parent_occupation() if admission else ""

    # Determine max_period and year_display based on admission type
    if is_pu:
        if student.current_year:
            max_period = student.current_year
            year_display = f"{admission.course.name} {student.current_year}"
        else:
            messages.error(request, "Student year is not set. Please contact admin.")
            max_period = 1
            year_display = f"{admission.course.name} N/A"
    else:
        if student.semester:
            max_period = 1  # always 1, because Degree semesters are not numeric for dropdown
            year_display = f"{admission.course.name} {student.semester}"
        else:
            messages.error(request, "Student semester is not set. Please contact admin.")
            max_period = 1
            year_display = f"{admission.course.name} N/A"

    # Available periods for dropdown (only for PU)
    available_periods = list(range(1, max_period + 1)) if is_pu else [1]
    period_label = "Year" if is_pu else "Semester"

    # Get selected period from GET params or default to latest
    selected_period = int(request.GET.get('period', available_periods[-1]))
    if selected_period not in available_periods:
        selected_period = available_periods[-1]

    # Get admission_no
    admission_no = admission.admission_no if admission else None
    # Convert StudentDatabase.academic_year (string) → AcademicYear object
    academic_year_obj = AcademicYear.objects.filter(year=student.academic_year).first()

    # Build FeeDeclaration query
    fee_decl_query = {
        "academic_year": academic_year_obj,
        "course_type": student.course_type,
        "course": student.course,
        "semester": selected_period,
    }
    fee_decl = FeeDeclaration.objects.filter(**fee_decl_query).first()

    # If no FeeDeclaration found for PU, try matching by academic_year only
    if not fee_decl and is_pu:
        fee_decl_query_alt = {
            "academic_year": academic_year_obj,
            "course_type": student.course_type,
            "course": student.course
        }
        fee_decl = FeeDeclaration.objects.filter(**fee_decl_query_alt).first()

    # --- Build fee status list per fee type and period ---
    fee_status_list = []
    if fee_decl:
        for fee in fee_decl.fee_details.all():
            # Fetch ALL payments for this fee type and admission
            all_payments = StudentFeeCollection.objects.filter(
                admission_no=admission_no,
                fee_type=fee.fee_type
            ).order_by('-paid_amount', '-receipt_date')

            # Prefer payment for selected period, else latest payment
            payment = None
            for p in all_payments:
                if getattr(p, 'semester', None) == selected_period:
                    payment = p
                    break
            if not payment and all_payments.exists():
                payment = all_payments.first()  # fallback to latest/highest payment

            fee_status_list.append({
                "fee_type": fee.fee_type.name,
                "declared_amount": fee.amount,
                "due_date": fee.due_date,
                "paid_amount": payment.paid_amount if payment else 0,
                "discount": payment.applied_discount if payment else 0,
                "balance": payment.balance_amount if payment else fee.amount,
                "status": payment.status if payment else "Pending",
                # "receipt_no": payment.receipt_no if payment else "",      # commented
                # "receipt_date": payment.receipt_date if payment else "",  # commented
            })

    # --- Group payments by receipt_no ---
    receipt_dict = defaultdict(list)

    # Filter StudentFeeCollection by selected period (year for PU, semester for Degree)
    if is_pu:
        all_payments = StudentFeeCollection.objects.filter(
            admission_no=admission_no,
            semester=selected_period  # here semester field stores year for PU
        ).order_by('-receipt_date', '-id')
    else:
        all_payments = StudentFeeCollection.objects.filter(
            admission_no=admission_no,
            semester=selected_period
        ).order_by('-receipt_date', '-id')

    for payment in all_payments:
        if payment.receipt_no:  # Only consider transactions with a receipt_no
            receipt_dict[payment.receipt_no].append(payment)

    # Build daily_receipts list
    daily_receipts = []
    for receipt_no, transactions in receipt_dict.items():
        fee_types = ", ".join([t.fee_type.name for t in transactions if t.fee_type])
        daily_receipts.append({
            'receipt_no': receipt_no,
            'receipt_date': transactions[0].receipt_date,
            'admission_no': admission_no,
            'fee_types': fee_types,
            'transactions': transactions,
        })

    # Build student details dictionary
    student_details = {
        'student_name': student.student_name,
        'roll_no': getattr(student, 'student_userid', ''),  # student_userid as roll_no
        'course': student.course.name if student.course else "",
        'year': f"{admission.course.name} {student.current_year}" if is_pu else f"{admission.course.name} {student.semester}" if admission else "",
        'course_type': student.course_type.name if student.course_type else "",
        'admission_no': admission.admission_no if admission else "",
        'mobile': student.student_phone_no or getattr(admission, 'student_phone_no', '') or getattr(admission, 'parent_phone', ''),
        'category': getattr(admission, 'category', "") if admission else "",
        'semester': getattr(student, 'semester', None),
        'current_year': getattr(student, 'current_year', None),
        'dob': getattr(admission, 'dob', None) if admission else None,
        'father_name': getattr(admission, 'father_name', "") if admission else "",
        'mother_name': getattr(admission, 'mother_name', "") if admission else "",
    }

    context = {
        "parent_name": parent_name,
        "parent_email": parent_email,
        "parent_phone": parent_phone,
        "parent_adhar": parent_adhar,
        "parent_occupation": parent_occupation,
        "student_name": student.student_name,
        "roll_no": getattr(student, 'student_userid', ''),
        "course": student.course.name if student.course else "",
        "year": student.current_year if student.current_year else student.semester,
        "course_type": student.course_type.name if student.course_type else "",
        "admission_no": admission.admission_no if admission else "",
        "mobile": student.student_phone_no,
        "category": admission.category if admission else "",
        "periods": available_periods,
        "selected_period": selected_period,
        "period_label": period_label,
        "fee_status_list": fee_status_list,
        "student_details": student_details,
        # Updated receipts for download table
        "daily_receipts": daily_receipts,
    }

    return render(request, "lms/parent_fee_view.html", context)





# from django.http import HttpResponse
# from django.template.loader import get_template
# from weasyprint import HTML
# from master.models import StudentDatabase
# from fees.models import StudentFeeCollection
# from django.db.models import Q

# def generate_daily_receipt(request, admission_no, receipt_no):
#     # Fetch all transactions for this receipt
#     transactions = StudentFeeCollection.objects.filter(
#         admission_no=admission_no,
#         receipt_no=receipt_no
#     )

#     if not transactions.exists():
#         return HttpResponse("No transactions found for this receipt.", status=404)

#     # Fetch student via related PU or Degree admission
#     try:
#         student = StudentDatabase.objects.get(
#             Q(pu_admission__admission_no=admission_no) |
#             Q(degree_admission__admission_no=admission_no)
#         )
#         admission = (
#             student.pu_admission
#             if student.pu_admission and student.pu_admission.admission_no == admission_no
#             else student.degree_admission
#         )
#     except StudentDatabase.DoesNotExist:
#         student = None
#         admission = None

#     # Prepare totals
#     total_amount = sum(t.amount for t in transactions)
#     total_paid = sum(t.paid_amount for t in transactions)
#     total_discount = sum(t.applied_discount for t in transactions)
#     total_balance = sum(t.balance_amount for t in transactions)
#     total_due = total_balance
#     payment_mode = transactions.first().payment_mode or "-"

#     # Build receipt details list
#     receipt_details = [
#         {
#             "fee_type": txn.fee_type.name,
#             "receipt_no": txn.receipt_no,
#             "receipt_date": txn.receipt_date,
#             "amount": txn.amount,
#             "paid_amount": txn.paid_amount,
#             "discount": txn.applied_discount,
#             "balance": txn.balance_amount,
#             "status": txn.status,
#             "payment_mode": txn.payment_mode or "-",
#         }
#         for txn in transactions
#     ]

#     context = {
#         "student": student,
#         "admission_no": admission_no,
#         "receipt_no": receipt_no,
#         "receipt_date": transactions.first().receipt_date,
#         "receipt_details": receipt_details,
#         "total_amount": total_amount,
#         "total_paid": total_paid,
#         "total_discount": total_discount,
#         "total_balance": total_balance,
#         "total_due": total_due,
#         "course": admission.course.name if admission and admission.course else "-",
#         "parent_name": getattr(admission, "parent_name", "-") if admission else "-",
#         "payment_mode": payment_mode,
#     }

#     # Render HTML
#     template = get_template("lms/parent_fee_download.html")
#     html_string = template.render(context)

#     # Generate PDF (IMPORTANT: base_url to resolve assets properly)
#     pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()

#     # Return as downloadable PDF
#     response = HttpResponse(pdf, content_type="application/pdf")
#     response["Content-Disposition"] = f'attachment; filename="fee_receipt_{student}.pdf"'
#     return response




import os
from django.http import HttpResponse
from django.template.loader import render_to_string
from master.models import StudentDatabase
from fees.models import StudentFeeCollection
from django.db.models import Q
import pdfkit
from django.conf import settings

def generate_daily_receipt(request, admission_no, receipt_no):
    # Fetch transactions
    transactions = StudentFeeCollection.objects.filter(
        admission_no=admission_no,
        receipt_no=receipt_no
    )
    if not transactions.exists():
        return HttpResponse("No transactions found for this receipt.", status=404)

    # Fetch student
    try:
        student = StudentDatabase.objects.get(
            Q(pu_admission__admission_no=admission_no) |
            Q(degree_admission__admission_no=admission_no)
        )
        admission = (
            student.pu_admission
            if student.pu_admission and student.pu_admission.admission_no == admission_no
            else student.degree_admission
        )
    except StudentDatabase.DoesNotExist:
        student = None
        admission = None

    # Totals
    total_amount = sum(t.amount for t in transactions)
    total_paid = sum(t.paid_amount for t in transactions)
    total_discount = sum(t.applied_discount for t in transactions)
    total_balance = sum(t.balance_amount for t in transactions)
    total_due = total_balance
    payment_mode = transactions.first().payment_mode or "-"

    # Receipt details
    receipt_details = [
        {
            "fee_type": txn.fee_type.name,
            "receipt_no": txn.receipt_no,
            "receipt_date": txn.receipt_date,
            "amount": txn.amount,
            "paid_amount": txn.paid_amount,
            "discount": txn.applied_discount,
            "balance": txn.balance_amount,
            "status": txn.status,
            "payment_mode": txn.payment_mode or "-",
        }
        for txn in transactions
    ]

    context = {
        "student": student,
        "admission_no": admission_no,
        "receipt_no": receipt_no,
        "receipt_date": transactions.first().receipt_date,
        "receipt_details": receipt_details,
        "total_amount": total_amount,
        "total_paid": total_paid,
        "total_discount": total_discount,
        "total_balance": total_balance,
        "total_due": total_due,
        "course": admission.course.name if admission and admission.course else "-",
        "parent_name": getattr(admission, "parent_name", "-") if admission else "-",
        "payment_mode": payment_mode,
    }

    # Render HTML template
    html_string = render_to_string("lms/parent_fee_download.html", context)

    # wkhtmltopdf path (set correct path for your system or Azure)
    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

    # Options to preserve exact layout
    options = {
        "page-size": "A5",
        "encoding": "UTF-8",
        "enable-local-file-access": True,  # allow local CSS/images
        "zoom": "1.25",  # scale to match your HTML
        "no-outline": None,
        "margin-top": "0.2in",
        "margin-bottom": "0.2in",
        "margin-left": "0.2in",
        "margin-right": "0.2in",
        "load-error-handling": "ignore",  # ignores missing fonts/images
        "print-media-type": True,  # apply @media print CSS
    }

    # Generate PDF
    pdf = pdfkit.from_string(html_string, False, configuration=config, options=options)

    # Return PDF response
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="fee_receipt_{admission_no}.pdf"'
    return response
