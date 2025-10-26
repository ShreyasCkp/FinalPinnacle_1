# hr/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import HolidayCalendar
from django.contrib import messages

def holiday_list(request):
    holidays = HolidayCalendar.objects.all().order_by('date')
    return render(request, 'hr/holiday_list.html', {'holidays': holidays})

def holiday_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        date = request.POST.get('date')
        holiday_type = request.POST.get('holiday_type')
        is_working_day = request.POST.get('is_working_day') == 'on'

        HolidayCalendar.objects.create(
            name=name,
            date=date,
            holiday_type=holiday_type,
            is_working_day=is_working_day
        )
        messages.success(request, "Holiday added successfully.")
        return redirect('holiday_list')
    return render(request, 'hr/holiday_form.html')

def holiday_edit(request, pk):
    holiday = get_object_or_404(HolidayCalendar, pk=pk)
    if request.method == 'POST':
        holiday.name = request.POST.get('name')
        holiday.date = request.POST.get('date')
        holiday.holiday_type = request.POST.get('holiday_type')
        holiday.is_working_day = request.POST.get('is_working_day') == 'on'
        holiday.save()
        messages.success(request, "Holiday updated successfully.")
        return redirect('holiday_list')
    return render(request, 'hr/holiday_form.html', {'holiday': holiday})

def holiday_delete(request, pk):
    holiday = get_object_or_404(HolidayCalendar, pk=pk)
    holiday.delete()
    messages.success(request, "Holiday deleted successfully.")
    return redirect('holiday_list')


# -- Leave views -------------------------------------------------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Leave
from .forms import LeaveForm

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Leave, Employee
from .forms import LeaveForm

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.safestring import mark_safe
import json

from .models import Leave, Employee
from .forms import LeaveForm


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.safestring import mark_safe
import json
from .models import Leave, Employee
from .forms import LeaveForm
from django.utils import timezone
 
def employee_leave_create(request, leave_id=None):
    """
    Create a new leave or edit an existing leave.
    - leave_id: if provided, opens the form in edit mode for that leave.
    """
    next_page = request.GET.get("next", "leave_list")

    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')

    employee = get_object_or_404(Employee, employee_userid=employee_userid)

    # Check if this is edit mode
    if leave_id:
        leave = get_object_or_404(Leave, id=leave_id, employee=employee)
    else:
        leave = None

    if request.method == 'POST':
        form = LeaveForm(request.POST, instance=leave)
        if form.is_valid():
            leave_obj = form.save(commit=False)
            leave_obj.employee = employee

            if leave_id:
                # Reset approval details when editing
                leave_obj.is_approved = None  # Pending on edit
                if hasattr(leave_obj, "approved_by"):
                    leave_obj.approved_by = None
                if hasattr(leave_obj, "approved_on"):
                    leave_obj.approved_on = None
                if hasattr(leave_obj, "remarks"):
                    leave_obj.remarks = None
                if hasattr(leave_obj, "admin_reason"):
                    leave_obj.admin_reason = None
            else:
                # New leave request → pending approval by default
                leave_obj.is_approved = None

            leave_obj.save()

            if leave_id:
                messages.success(request, "Leave updated successfully and sent for approval.")
            else:
                messages.success(request, "Leave request submitted successfully.")

            return redirect('employee_calendar')
    else:
        form = LeaveForm(instance=leave)

    # Existing leaves for calendar display
    leaves = Leave.objects.filter(employee=employee).order_by('-applied_on')
    existing_leaves = list(leaves.values('start_date', 'end_date', 'leave_type', 'id', 'is_approved'))
    existing_leaves_json = mark_safe(json.dumps(existing_leaves, default=str))

    return render(request, 'hr/employee_leave_form.html', {
        'form': form,
        'leaves': leaves,
        'existing_leaves': existing_leaves_json,
        'edit_leave': leave,  # send to template for showing cancel button if editing
        "next": next_page,   # Pass next into template
    })


 

 

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Leave
from master.models import UserCustom


# 🔹 Helper to fetch approver name from session or cookies
def _get_approver_name(request):
    return request.session.get("username") or request.COOKIES.get("username")


# 🔹 List all leaves (for manager view)
def employee_leave_list(request):
    leaves = Leave.objects.all().order_by("-applied_on", "-start_date")
    return render(request, "hr/employee_leave_list.html", {"leaves": leaves})


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Leave
from master.models import UserCustom
from django.utils import timezone


# 🔹 Approve leave with reason
def leave_approve(request, leave_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    leave = get_object_or_404(Leave, id=leave_id)
    approver = UserCustom.objects.filter(id=user_id).first()

    if request.method == "POST":
        reason = request.POST.get("admin_reason", "").strip()
        if approver:
            leave.approved_by = approver.username
            leave.is_approved = True
            leave.admin_reason = reason
            leave.approved_on = timezone.now()
            leave.save()
            messages.success(request, f"Leave approved by {approver.username}")
        return redirect("employee_leave_list")

    return render(request, "hr/approve_modal.html", {"leave": leave, "action": "approve"})


# 🔹 Reject leave with reason
def leave_reject(request, leave_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    leave = get_object_or_404(Leave, id=leave_id)
    approver = UserCustom.objects.filter(id=user_id).first()

    if request.method == "POST":
        reason = request.POST.get("admin_reason", "").strip()
        if approver:
            leave.approved_by = approver.username
            leave.is_approved = False
            leave.admin_reason = reason
            leave.approved_on = timezone.now()
            leave.save()
            messages.success(request, f"Leave rejected by {approver.username}")
        return redirect("employee_leave_list")

    return render(request, "hr/approve_modal.html", {"leave": leave, "action": "reject"})


# hr/views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import EmployeeSalaryDeclaration
from .forms import EmployeeSalaryDeclarationForm
from master.models import Employee
from django.template.loader import render_to_string
from xhtml2pdf import pisa  # replaced weasyprint

def view_payslip(request, pk):
    declaration = get_object_or_404(EmployeeSalaryDeclaration, pk=pk)
    employee = declaration.employee
    return render(request, 'hr/payslip_form.html', {
        'form': declaration,
        'is_pdf': False,  # Show Submit/Download button in HTML view
        'declaration': declaration,
        'employee': employee,
    })


def download_payslip(request, pk):
    declaration = get_object_or_404(EmployeeSalaryDeclaration, pk=pk)
    employee = declaration.employee

    html_string = render_to_string('hr/payslip_form.html', {
        'declaration': declaration,
        'employee': employee,
        'is_pdf': True,  # Adjust UI in template for PDF
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Payslip_{declaration.emp_code}.pdf"'

    # Convert HTML to PDF using xhtml2pdf
    pisa_status = pisa.CreatePDF(html_string, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors generating the PDF <pre>' + html_string + '</pre>')

    return response




def salary_declaration_create(request):
    if request.method == 'POST':
        form = EmployeeSalaryDeclarationForm(request.POST)
        if form.is_valid():
            form.save()  # gross_salary, total_deductions, net_pay auto-calculated in model
            return redirect('salary_declaration_list')
    else:
        form = EmployeeSalaryDeclarationForm()
    return render(request, 'hr/salary_declaration_form.html', {'form': form, 'title': 'Add Salary Declaration'})

def salary_declaration_edit(request, pk):
    declaration = get_object_or_404(EmployeeSalaryDeclaration, pk=pk)

    if request.method == 'POST':
        form = EmployeeSalaryDeclarationForm(request.POST, instance=declaration)
        if form.is_valid():
            form.save()
            return redirect('salary_declaration_list')
    else:
        # Pre-fill employee details from DB
        form = EmployeeSalaryDeclarationForm(instance=declaration)

    return render(request, 'hr/salary_declaration_form.html', {
        'form': form,
        'title': 'Edit Salary Declaration'
    })

from django.urls import reverse

def salary_declaration_list(request):
    declarations = EmployeeSalaryDeclaration.objects.all().order_by('-created_at')
    for decl in declarations:
        decl.payslip_url = reverse('download_payslip', args=[decl.id]) if decl.id else None
    return render(request, 'hr/salary_declaration_list.html', {'declarations': declarations})

def get_employee_data(request):
    emp_id = request.GET.get('employee_id')
    data = {}
    if emp_id:
        try:
            emp = Employee.objects.get(id=emp_id)
            data = {
                'emp_code': emp.emp_code,
                'name': emp.name,
                'designation': emp.designation,
                'employment_type': emp.employment_type,
                'category': emp.category,
                'role': emp.role
            }
        except Employee.DoesNotExist:
            data = {'error': 'Employee not found'}
    return JsonResponse(data)


from django.views.decorators.http import require_POST

@require_POST
def salary_declaration_delete(request, pk):
    declaration = get_object_or_404(EmployeeSalaryDeclaration, pk=pk)
    declaration.delete()
    return redirect('salary_declaration_list')




from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import date, timedelta
import calendar
import holidays
import numpy as np
from master.models import AcademicEvent
from .models import Leave, Employee

# LEAVE_TYPE_CHOICES
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

def employee_calendar(request):
    # Get logged-in employee
    employee_userid = request.COOKIES.get('employee_userid')
    if not employee_userid:
        return redirect('employee_login_view')
 
    try:
        employee = Employee.objects.get(employee_userid=employee_userid)
    except Employee.DoesNotExist:
        return redirect('employee_login_view')
 
    today = timezone.localdate()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
 
    cal = calendar.Calendar(firstweekday=6)
    month_days = list(cal.monthdayscalendar(year, month))
    weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
 
    # Employee leaves overlapping this month
    leaves_qs = Leave.objects.filter(
        employee=employee,
        start_date__lte=date(year, month, calendar.monthrange(year, month)[1]),
        end_date__gte=date(year, month, 1)
    )
 
    # --- Dynamic leave rules ---
    LEAVE_RULES = {
        'CL': (6, 12),
        'SL': (6, 12),
        'EL': 6,
        'LOP': None,
        'ML': 26 * 7 // 5,
        'PL': (5, 15),
        'BL': (3, 7),
        'Marriage': (3, 5),
        'Sabbatical': (90, 730),
        'Optional': (2, 3),
        'CO': None,
        'Volunteer': (1, 5),
        'WFH': None,
        'Adoption': 12 * 7 // 5,
        'Special': (1, 2)
    }
 
    # Annual allowed leaves
    annual_allowed_leaves = {}
    for leave_type, rule in LEAVE_RULES.items():
        if rule is None:
            continue
        elif isinstance(rule, tuple):
            annual_allowed_leaves[leave_type] = int(np.random.randint(rule[0], rule[1] + 1))
        else:
            annual_allowed_leaves[leave_type] = rule
 
    # Count approved leaves
    leave_taken_count = {lt: 0 for lt in annual_allowed_leaves.keys()}
    day_highlights = []
 
    for leave in leaves_qs:
        # Count approved leaves only
        if leave.is_approved and leave.leave_type in leave_taken_count:
            delta_days = (leave.end_date - leave.start_date).days + 1
            leave_taken_count[leave.leave_type] += delta_days
 
        # build calendar highlights
        current = leave.start_date
        while current <= leave.end_date:
            if current.month == month:
                if leave.is_approved:
                    status = "approved"
                elif leave.is_approved is False:
                    status = "rejected"
                else:
                    status = "pending"
 
                day_highlights.append({
                    "date": current,
                    "status": status,
                    "leave_type": leave.leave_type
                })
            current += timedelta(days=1)
 
    leave_balances = {
        lt: max(annual_allowed_leaves[lt] - leave_taken_count.get(lt, 0), 0)
        for lt in annual_allowed_leaves.keys()
    }
 
    leave_balances_list = [
        {"leave_type": lt, "balance": balance, "allowed": annual_allowed_leaves.get(lt, 0)}
        for lt, balance in leave_balances.items()
    ]
 
    leaves_list = []
    for leave in leaves_qs:
        status_text = "Approved" if leave.is_approved else "Rejected" if leave.is_approved is False else "Pending"
        leaves_list.append({
            "id": leave.id,
            "start": leave.start_date,
            "end": leave.end_date,
            "leave_type": leave.get_leave_type_display(),
            "status": status_text,
            "can_cancel": leave.is_approved and leave.start_date > today,
            "cancel_url": None,
        })
 
    # Holidays (India)
    india_holidays = holidays.India(years=year)
    national_holidays = {
        (1, 26): "Republic Day",
        (4, 18): "Good Friday",
        (5, 1): "May Day",
        (8, 15): "Independence Day",
        (10, 2): "Gandhi Jayanti",
    }
    all_holidays = []
    for (m, d), name in national_holidays.items():
        dt = date(year, m, d)
        all_holidays.append({"date": dt, "name": india_holidays.get(dt, name)})
 
    month_holidays = [h for h in all_holidays if h["date"].month == month]
 
    # Academic Events
    academic_events = AcademicEvent.objects.filter(date__year=year, date__month=month)
 
    # Build highlights_json
    highlights_json = []
 
    # Leaves
    for leave in day_highlights:
        dt = leave["date"]
        color = "green" if leave["status"] == "approved" else "red" if leave["status"] == "rejected" else "yellow"
        highlights_json.append({
            "date_day": dt.day,
            "date_month": dt.month,
            "date_year": dt.year,
            "color": color,
            "title": f"{leave['leave_type']} ({leave['status'].capitalize()})"
        })
 
    # Holidays
    for holiday in month_holidays:
        dt = holiday["date"]
        highlights_json.append({
            "date_day": dt.day,
            "date_month": dt.month,
            "date_year": dt.year,
            "color": "black",
            "title": holiday["name"]
        })
 
    # Academic Events
    for event in academic_events:
        highlights_json.append({
            "date_day": event.date.day,
            "date_month": event.date.month,
            "date_year": event.date.year,
            "color": "blue",
            "title": f"Academic Event: {event.title}"
        })
 
    # Previous / next month
    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)
 
    context = {
        'employee': employee,
        'today': today,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'month_days': month_days,
        'weekdays': weekdays,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'highlights_json': highlights_json,
        'leaves_list': leaves_list,
        'leave_balances_list': leave_balances_list,
        'academic_events': academic_events,
    }
 
    return render(request, 'hr/employee_calendar.html', context) 
 
from django.shortcuts import get_object_or_404, redirect

from django.contrib import messages

from django.utils import timezone

from .models import Leave
 
def edit_leave_redirect(request, leave_id):

    leave = get_object_or_404(Leave, id=leave_id)

    # Only allow editing for future leaves

    if leave.start_date >= timezone.now().date():

        return redirect('employee_leave_create', leave_id=leave.id)

    else:

        messages.error(request, "Past or ongoing leaves cannot be edited.")

        return redirect('employee_leave_create')
 
from django.shortcuts import get_object_or_404, redirect

from django.contrib import messages

from .models import Leave

from django.utils import timezone
 
def edit_leave_cancel(request, leave_id):

    leave = get_object_or_404(Leave, id=leave_id)

    next_page = request.GET.get("next", "leave_list")
 
    if leave.start_date >= timezone.now().date():

        leave.delete()

        messages.success(request, "Leave canceled successfully.")

    else:

        messages.error(request, "Cannot cancel past or ongoing leave.")
 
    return redirect("employee_calendar" if next_page == "calendar" else "employee_calendar")

 
from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from datetime import date
import calendar
from attendence.models import attendance
import calendar
from datetime import date
from django.shortcuts import render
from django.db.models import Sum
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt


def get_working_days(year, month):
    total_days = calendar.monthrange(year, month)[1]
    working_days = sum(1 for day in range(1, total_days + 1) if date(year, month, day).weekday() < 5)
    return total_days, working_days

@csrf_exempt
def employee_salary_dashboard(request):
    today = date.today()
    month = int(request.POST.get("month") or request.GET.get("month", today.month))
    year = int(request.POST.get("year") or request.GET.get("year", today.year))

    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = range(2020, today.year + 1)

    employees = Employee.objects.all()
    data = []

    total_days, working_days = get_working_days(year, month)

    # KPI Totals
    total_employees = 0
    total_tds = 0
    total_pt = 0
    total_epf = 0
    total_compensation = 0

    for emp in employees:
        attendance_qs = attendance.objects.filter(employee=emp, date__year=year, date__month=month)
        present_days = attendance_qs.filter(status="Present").count()
        absent_days = attendance_qs.filter(status="Absent").count()
        lop_days_this_month = sum(
            1 for att in attendance_qs if getattr(att, "lop", False) and att.date.day < 25
        )

        declaration = EmployeeSalaryDeclaration.objects.filter(employee=emp).order_by("-created_at").first()
        net_pay = declaration.net_pay if declaration else 0

        if declaration:
            total_employees += 1
            total_tds += declaration.income_tax or 0
            total_pt += declaration.professional_tax or 0
            total_epf += declaration.pf_contribution or 0
            total_compensation += net_pay

        per_day_salary = net_pay / working_days if working_days > 0 else 0
        salary_deduction = lop_days_this_month * per_day_salary
        final_salary = net_pay - salary_deduction

        # ✅ Save salary slip only on POST
        if request.method == "POST":
            EmployeeSalarySlip.objects.update_or_create(
                employee=emp,
                month=month,
                year=year,
                defaults={
                    "total_days": total_days,
                    "present_days": present_days,
                    "absent_days": absent_days,
                    "lop_days": lop_days_this_month,
                    "salary_deduction": salary_deduction,
                    "final_salary": final_salary,
                    "net_pay_in_words": "",  # optional: convert to words if needed
                    "emp_code": emp.emp_code,
                    "name": emp.name,
                    "designation": emp.designation,
                    "location": emp.location,
                    "uan_number": emp.uan_number,
                    "pan_number": emp.pan_number,
                    "dob": emp.dob,
                    "aadhaar_number": emp.aadhaar_number,
                    "pf_number": emp.pf_number,
                    
                    "esi_number": emp.esi_number,
                    "bank_name": emp.bank_name,
                    "ifsc_code": emp.ifsc_code,
                    "bank_account_number": emp.bank_account_number,
                }
            )

        # Prepare for frontend display
        data.append({
            "employee": emp,
            "declaration": declaration,
            "working_days": working_days,
            "present_days": present_days,
            "lop_days": lop_days_this_month,
            "salary_deduction": salary_deduction,
            "final_salary": final_salary,
        })

    if request.method == "POST":
        messages.success(request, "Salary slips generated and saved successfully.")

    context = {
        "data": data,
        "month": month,
        "year": year,
        "months": months,
        "years": years,
        "kpis": {
            "total_employees": total_employees,
            "total_tds": total_tds,
            "total_pt": total_pt,
            "total_epf": total_epf,
            "total_compensation": total_compensation,
        },
    }
    return render(request, "hr/employee_salary_dashboard.html", context)

















from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from datetime import date
import calendar
from attendence.models import attendance




# ✅ Generate slips for all employees for a given month/year
@transaction.atomic
def generate_employee_salary_slips(request):
    if request.method == "POST":
        month = int(request.POST.get("month"))
        year = int(request.POST.get("year"))

        # total working days in that month
        total_days = calendar.monthrange(year, month)[1]

        employees = Employee.objects.all()
        for emp in employees:
            # Fetch salary declaration (basic, hra, etc.)
            try:
                declaration = EmployeeSalaryDeclaration.objects.get(employee=emp)
                base_salary = declaration.basic_salary
            except EmployeeSalaryDeclaration.DoesNotExist:
                base_salary = 0

            # Attendance
            present_days = attendance.objects.filter(
                employee=emp, date__year=year, date__month=month, status="Present"
            ).count()
            lop_days = attendance.objects.filter(
                employee=emp, date__year=year, date__month=month, status="LOP"
            ).count()
            absent_days = total_days - present_days

            # Salary calc
            per_day_salary = base_salary / total_days if total_days > 0 else 0
            salary_deduction = lop_days * per_day_salary
            final_salary = base_salary - salary_deduction

            # Save/Update slip
            slip, created = EmployeeSalarySlip.objects.update_or_create(
                employee=emp,
                month=month,
                year=year,
                defaults={
                    "total_days": total_days,
                    "present_days": present_days,
                    "absent_days": absent_days,
                    "lop_days": lop_days,
                    "salary_deduction": salary_deduction,
                    "final_salary": final_salary,
                    "net_pay_in_words": "",  # you can add a num2words function here
                    # Snapshot
                    "emp_code": emp.emp_code,
                    "name": emp.name,
                    "designation": emp.designation,
                    "location": emp.location,
                    "uan_number": emp.uan_number,
                    "pan_number": emp.pan_number,
                    "dob": emp.dob,
                    "aadhaar_number": emp.aadhaar_number,
                    "pf_number": emp.pf_number,
                    "pension_no": emp.pension_no,
                    "esi_number": emp.esi_number,
                    "bank_name": emp.bank_name,
                    "ifsc_code": emp.ifsc_code,
                    "bank_account_number": emp.bank_account_number,
                },
            )

        messages.success(request, f"Salary slips generated for {calendar.month_name[month]}, {year}")
        return redirect("employee_salary_slip_list")

    return render(request, "hr/salary_slip.html")

from django.shortcuts import render, get_object_or_404
from datetime import date, datetime
from .models import Employee, EmployeeSalarySlip, EmployeeSalaryDeclaration

from django.shortcuts import render
from decimal import Decimal
from datetime import date
from django.templatetags.static import static
from .models import Employee, EmployeeSalarySlip, EmployeeSalaryDeclaration

# helper function to convert number to words
def number_to_words(num):
    a = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten',
         'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
         'Seventeen', 'Eighteen', 'Nineteen']
    b = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

    def in_words(n):
        if n < 20:
            return a[n]
        if n < 100:
            return b[n // 10] + ('' if n % 10 == 0 else ' ' + a[n % 10])
        if n < 1000:
            return a[n // 100] + ' Hundred' + ('' if n % 100 == 0 else ' ' + in_words(n % 100))
        if n < 100000:
            return in_words(n // 1000) + ' Thousand' + ('' if n % 1000 == 0 else ' ' + in_words(n % 1000))
        if n < 10000000:
            return in_words(n // 100000) + ' Lakh' + ('' if n % 100000 == 0 else ' ' + in_words(n % 100000))
        return in_words(n // 10000000) + ' Crore' + ('' if n % 10000000 == 0 else ' ' + in_words(n % 10000000))

    if num == 0:
        return "Zero"

    rupees = int(num)
    paise = round((num - rupees) * 100)

    result = in_words(rupees) + " Rupees"
    if paise > 0:
        result += " and " + in_words(paise) + " Paise"
    return result + " Only"



from django.shortcuts import render
from decimal import Decimal
from datetime import date
from django.templatetags.static import static
from .models import Employee, EmployeeSalarySlip, EmployeeSalaryDeclaration

# helper function to convert number to words
def number_to_words(num):
    a = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten',
         'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
         'Seventeen', 'Eighteen', 'Nineteen']
    b = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

    def in_words(n):
        if n < 20:
            return a[n]
        if n < 100:
            return b[n // 10] + ('' if n % 10 == 0 else ' ' + a[n % 10])
        if n < 1000:
            return a[n // 100] + ' Hundred' + ('' if n % 100 == 0 else ' ' + in_words(n % 100))
        if n < 100000:
            return in_words(n // 1000) + ' Thousand' + ('' if n % 1000 == 0 else ' ' + in_words(n % 1000))
        if n < 10000000:
            return in_words(n // 100000) + ' Lakh' + ('' if n % 100000 == 0 else ' ' + in_words(n % 100000))
        return in_words(n // 10000000) + ' Crore' + ('' if n % 10000000 == 0 else ' ' + in_words(n % 10000000))

    if num == 0:
        return "Zero"

    rupees = int(num)
    paise = round((num - rupees) * 100)

    result = in_words(rupees) + " Rupees"
    if paise > 0:
        result += " and " + in_words(paise) + " Paise"
    return result + " Only"


from decimal import Decimal
def employee_salary_slip_view(request):
    employee_id = request.COOKIES.get("employee_id")

    if not employee_id:
        return render(request, "hr/salary_slip.html", {
            "error": "Employee not identified. Please login again."
        })

    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return render(request, "hr/salary_slip.html", {
            "error": "Employee not found in system. Please contact HR."
        })

    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    salary_slip = EmployeeSalarySlip.objects.filter(
        employee=employee, year=year, month=month
    ).first()

    declaration = EmployeeSalaryDeclaration.objects.filter(employee=employee).first()

    # --- Handle missing data gracefully ---
    if not salary_slip or not declaration:
        return render(request, "hr/salary_slip.html", {
            "error": "Salary slip or declaration not available for this month.",
            "salary_slip": None,
            "declaration": None,
        })

    logo_url = request.build_absolute_uri(static("images/logo.png")) 

    # ✅ Attendance calculation
    total_days, _ = get_working_days(year, month)
    attendance_qs = attendance.objects.filter(employee=employee, date__year=year, date__month=month)
    present_days = attendance_qs.filter(status="Present").count()
    lop_days = sum(1 for att in attendance_qs if getattr(att, 'lop', False) and att.date.day < 25)

    final_salary = salary_slip.final_salary or 0
    total_deductions = (declaration.total_deductions or 0) + Decimal(salary_slip.salary_deduction or 0)

    net_pay_in_words = num2words(final_salary, to="currency", lang="en_IN").replace("euro", "rupees").title()

    context = {
        "employee": employee,
        "declaration": declaration,
        "total_deductions": total_deductions,
        "month": month,
        "year": year,
        "months": range(1, 13),
        "years": range(2020, today.year + 1),
        "logo_url": logo_url,
        "is_pdf": False,
        "net_pay_in_words": net_pay_in_words,
        'salary_slip': {
            'present_days': present_days,
            'total_days': total_days,
            'lop_days': lop_days,
            'net_pay': final_salary,
            'salary_deduction': salary_slip.salary_deduction or 0,
        },
    }
    return render(request, "hr/salary_slip.html", context)




from datetime import date
from django.shortcuts import render, get_object_or_404
import calendar

from django.shortcuts import render, get_object_or_404
from datetime import date
import calendar

from master.models import Employee
from hr.models import EmployeeSalaryDeclaration, EmployeeSalarySlip

def get_working_days(year, month):
    total_days = calendar.monthrange(year, month)[1]
    working_days = sum(1 for day in range(1, total_days+1) if date(year, month, day).weekday() < 5)
    return total_days, working_days

def employee_annual_dashboard(request):
    employee_id = request.COOKIES.get("employee_id")
    if not employee_id:
        return render(request, "hr/error.html", {"error": "Employee not identified. Please login again."})

    employee = get_object_or_404(Employee, id=employee_id)
    current_year = date.today().year
    months_data = []

    # Fetch employee declaration once for Average Pay Distribution
    try:
        declaration = EmployeeSalaryDeclaration.objects.get(employee=employee)
    except EmployeeSalaryDeclaration.DoesNotExist:
        declaration = None

    for month in range(1, 13):
        total_days, working_days = get_working_days(current_year, month)

        # Fetch slips for this employee and month
        slips = EmployeeSalarySlip.objects.filter(employee=employee, month=month, year=current_year)
        present_days = sum(sl.present_days for sl in slips) if slips.exists() else 0
        lop_days = sum(sl.lop_days for sl in slips) if slips.exists() else 0
        final_salary = float(sum(sl.final_salary for sl in slips)) if slips.exists() else 0
        total_deductions = float(sum(sl.salary_deduction for sl in slips)) if slips.exists() else 0

        months_data.append({
            "month": month,
            "month_name": calendar.month_name[month],
            "present_days": present_days,
            "lop_days": lop_days,
            "net_pay": float(final_salary),
            "basic_salary": float(declaration.basic_salary) if declaration else 0,
            "total_deductions": total_deductions,
            "final_salary": final_salary,
            "declaration": declaration,
            "total_days": total_days,
        })

    return render(request, "hr/employee_annual_dashboard.html", {
        "employee": employee,
        "months_data": months_data,
        "year": current_year,
        "declaration": declaration  # send once for Average Pay Distribution chart
    })

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from datetime import date
from decimal import Decimal
from num2words import num2words
from django.templatetags.static import static

def download_payslip(request, month, year=None):
    # Identify employee
    employee_id = request.GET.get('employee_id') or request.COOKIES.get("employee_id")
    if not employee_id:
        return HttpResponse("Employee not identified", status=400)
    
    employee = get_object_or_404(Employee, id=employee_id)

    # Determine month and year
    if not year:
        year = request.GET.get('year') or date.today().year
    year = int(year)
    month = int(month)

    # Fetch salary slip and declaration
    salary_slip = EmployeeSalarySlip.objects.filter(employee=employee, month=month, year=year).first()
    declaration = EmployeeSalaryDeclaration.objects.filter(employee=employee).first()

    # Calculate attendance
    total_days, _ = get_working_days(year, month)
    attendance_qs = attendance.objects.filter(employee=employee, date__year=year, date__month=month)
    present_days = attendance_qs.filter(status="Present").count()
    lop_days = sum(1 for att in attendance_qs if getattr(att, 'lop', False) and att.date.day < 25)

    # Compute final salary and in-words
    final_salary = salary_slip.final_salary if salary_slip else 0
    net_pay_in_words = num2words(final_salary, to="currency", lang="en_IN").replace("euro", "rupees").title()

    # Logo and deductions
    logo_url = request.build_absolute_uri(static("images/logo.png"))
    total_deductions = (declaration.total_deductions if declaration else 0) + (salary_slip.salary_deduction if salary_slip else 0)

    # Context for template
    context = {
        'employee': employee,
        'salary_slip': {
            'present_days': present_days,
            'total_days': total_days,
            'lop_days': lop_days,
            'net_pay': final_salary,
            'net_pay_in_words': net_pay_in_words,
            'salary_deduction': salary_slip.salary_deduction if salary_slip else 0,
        },
        'declaration': declaration,
        'month': month,
        'year': year,
        'final_salary': final_salary,
        'logo_url': logo_url,
        "total_deductions": total_deductions,
        'is_pdf': True,
    }

    # Render HTML template
    html_string = render_to_string('hr/salary_slip.html', context)

    # Generate PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Payslip_{employee.emp_code}_{month}_{year}.pdf"'

    # xhtml2pdf conversion
    pisa_status = pisa.CreatePDF(
        src=html_string,
        dest=response,
        link_callback=lambda uri, rel: request.build_absolute_uri(uri)
    )

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)

    return response

