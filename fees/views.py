from django.shortcuts import render

from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from .models import FeeDeclaration
from .forms import FeeDeclarationForm, FeeDeclarationDetailFormSet
from django.contrib import messages

from master.models import CourseType, AcademicYear, Course
from .models import FeeDeclaration
from .forms import FeeDeclarationForm, FeeDeclarationDetailFormSet
from master.decorators import custom_login_required


@custom_login_required 
def fee_declaration_list(request):
    declarations = FeeDeclaration.objects.all()
    return render(request, 'fees/fee_declaration_list.html', {'declarations': declarations})







from django.shortcuts import render, redirect, get_object_or_404
from .models import FeeDeclaration, FeeDeclarationDetail
from .forms import FeeDeclarationForm, FeeDeclarationDetailFormSet
from master.models import AcademicYear, CourseType, Course

from django.shortcuts import render, redirect, get_object_or_404
from .forms import FeeDeclarationForm, FeeDeclarationDetailFormSet
from master.models import AcademicYear, CourseType, Course
from .models import FeeDeclaration
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

@custom_login_required
def fee_declaration_add(request):
    program_types = CourseType.objects.all().order_by('name')

    selected_program_type_id = request.POST.get('course_type') or request.GET.get('course_type')
    selected_academic_year_id = request.POST.get('academic_year') or request.GET.get('academic_year')
    selected_course_id = request.POST.get('course') or request.GET.get('course')
    selected_semester_or_year = request.POST.get('semester_or_year') or request.GET.get('semester_or_year')

    academic_years = AcademicYear.objects.none()
    courses = []
    semester_or_years = []
    is_pu = False

    if selected_program_type_id:
        academic_years = AcademicYear.objects.filter(
            coursetype__id=selected_program_type_id
        ).distinct().order_by('-year')

        courses = Course.objects.filter(course_type_id=selected_program_type_id).order_by('name')

        if selected_course_id:
            selected_course = get_object_or_404(Course, id=selected_course_id)
            is_pu = selected_course.course_type.name.strip().lower() == "puc regular"
            total = selected_course.duration_years if is_pu else selected_course.total_semesters or 0

            semester_or_years = [{'number': i, 'name': f"{selected_course.name} {i}"} for i in range(1, total + 1)]

            if not semester_or_years:
                semester_or_years.append({'number': 0, 'name': "NOT APPLICABLE"})

    if request.method == 'POST':
        form = FeeDeclarationForm(request.POST)
        formset = FeeDeclarationDetailFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            academic_year = form.cleaned_data.get('academic_year')
            course_type = form.cleaned_data.get('course_type')
            course = form.cleaned_data.get('course')

            if is_pu:
                current_year = int(selected_semester_or_year) if selected_semester_or_year else None
                semester = None
            else:
                semester = int(selected_semester_or_year) if selected_semester_or_year else None
                current_year = None

            duplicate = FeeDeclaration.objects.filter(
                academic_year=academic_year,
                course_type=course_type,
                course=course,
                semester=semester,
                current_year=current_year
            ).exists()

            if duplicate:
                form.add_error(None, "A fee declaration already exists for the selected combination. Please edit the existing declaration to add or update fee details.")
            else:
                fee_dec = form.save(commit=False)
                fee_dec.current_year = current_year
                fee_dec.semester = semester
                fee_dec.save()
                formset.instance = fee_dec
                formset.save()
                messages.success(request, "Fee Declaration added successfully.")
                return redirect('fee_declaration_list')
        else:
            messages.error(request, "")
    else:
        form = FeeDeclarationForm(initial={
            'course_type': selected_program_type_id,
            'academic_year': selected_academic_year_id,
            'course': selected_course_id,
        })
        formset = FeeDeclarationDetailFormSet()
        mode = 'add'

    return render(request, 'fees/fee_declaration_form.html', {
        'form': form,
        'mode': 'add',
        'formset': formset,
        'course_types': program_types,
        'academic_years': academic_years,
        'courses': courses,
        'semester_or_years': semester_or_years,
        'selected_course_type_id': int(selected_program_type_id) if selected_program_type_id else None,
        'selected_academic_year_id': int(selected_academic_year_id) if selected_academic_year_id else None,
        'selected_course': int(selected_course_id) if selected_course_id else None,
        'selected_sem_or_year': int(selected_semester_or_year) if selected_semester_or_year else None,
        'is_pu': is_pu,
        'title': 'Add Fee Declaration',
    })



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import FeeDeclarationForm, FeeDeclarationDetailFormSet
from .models import FeeDeclaration
from master.models import AcademicYear, CourseType, Course

@custom_login_required
def fee_declaration_edit(request, pk):
    declaration = get_object_or_404(FeeDeclaration, pk=pk)

    # For pre-filled selection in GET
    default_course_type_id = declaration.course_type_id
    default_academic_year_id = declaration.academic_year_id
    default_course_id = declaration.course_id
    default_sem_or_year = declaration.current_year if declaration.current_year is not None else declaration.semester

    if request.method == 'POST':
        form = FeeDeclarationForm(request.POST, instance=declaration)
        formset = FeeDeclarationDetailFormSet(request.POST, instance=declaration)

        # Temporary variables tracking posted selections
        posted_course_type = request.POST.get('course_type')
        posted_academic_year = request.POST.get('academic_year')
        posted_course = request.POST.get('course')
        posted_sem_or_year = request.POST.get('semester_or_year')

        if form.is_valid() and formset.is_valid():
            dec = form.save(commit=False)
            # Explicitly set foreign keys from POST
            if posted_course_type:
                dec.course_type_id = int(posted_course_type)
            else:
                dec.course_type = None

            if posted_academic_year:
                dec.academic_year_id = int(posted_academic_year)
            else:
                dec.academic_year = None

            if posted_course:
                dec.course_id = int(posted_course)
            else:
                dec.course = None

            # Handle semester/current_year logic
            if dec.course and dec.course.course_type.name.strip().lower() == 'puc regular':
                dec.current_year = int(posted_sem_or_year) if posted_sem_or_year else None
                dec.semester = None
            else:
                dec.semester = int(posted_sem_or_year) if posted_sem_or_year else None
                dec.current_year = None

            dec.save()
            formset.instance = dec
            formset.save()
            messages.success(request, 'Fee Declaration updated successfully.')
            return redirect('fee_declaration_list')
    else:
        form = FeeDeclarationForm(instance=declaration)
        formset = FeeDeclarationDetailFormSet(instance=declaration)

        # For rendering initial selects
        posted_course_type = default_course_type_id
        posted_academic_year = default_academic_year_id
        posted_course = default_course_id
        posted_sem_or_year = default_sem_or_year
        mode = 'edit'

    # Recalculate dropdown options based on current selection
    course_types = CourseType.objects.all().order_by('name')
    academic_years = AcademicYear.objects.filter(
    coursetype__id=posted_course_type
).distinct().order_by('-year') if posted_course_type else AcademicYear.objects.none()

    courses = Course.objects.filter(course_type_id=posted_course_type).order_by('name') if posted_course_type else []

    is_pu = False
    semester_or_years = []
    if posted_course:
        c = get_object_or_404(Course, id=posted_course)
        is_pu = c.course_type.name.strip().lower() == 'puc regular'
        total = c.duration_years if is_pu else c.total_semesters or 0
        semester_or_years = [{'number': i, 'name': f"{c.name} {i}"} for i in range(1, total + 1)]
        if not semester_or_years:
            semester_or_years = [{'number': 0, 'name': 'NOT APPLICABLE'}]

    

    return render(request, 'fees/fee_declaration_form.html', {
        'form': form,
        'mode': 'edit',
        'formset': formset,
        'course_types': course_types,
        'academic_years': academic_years,
        'courses': courses,
        'semester_or_years': semester_or_years,
        'selected_course_type_id': int(posted_course_type) if posted_course_type else None,
        'selected_academic_year_id': int(posted_academic_year) if posted_academic_year else None,
        'selected_course': int(posted_course) if posted_course else None,
        'selected_sem_or_year': int(posted_sem_or_year) if posted_sem_or_year else None,
        'is_pu': is_pu,
        'title': 'Edit Fee Declaration',
    })



@custom_login_required
def fee_declaration_delete(request, pk):
    declaration = get_object_or_404(FeeDeclaration, pk=pk)
    if request.method == 'POST':
        declaration.delete()
        messages.success(request, 'Fee Declaration deleted successfully.')
        return redirect('fee_declaration_list')
    return render(request, 'fees/fee_declaration_confirm_delete.html', {'declaration': declaration})


from master.models import StudentDatabase, FeeType,CourseType,AcademicYear,Course,Semester

@custom_login_required
def student_fee_list(request):
    course_type_id = request.GET.get('course_type')
    course_id = request.GET.get('course')
    academic_year_id = request.GET.get('academic_year')
    semester_number = request.GET.get('semester')

    try:
        semester_number = int(semester_number) if semester_number else None
    except (ValueError, TypeError):
        semester_number = None

    course_types = CourseType.objects.all()
    academic_years = AcademicYear.objects.all()

    academic_year_obj = AcademicYear.objects.filter(id=academic_year_id).first()
    academic_year_str = academic_year_obj.year if academic_year_obj else None

    courses = Course.objects.filter(course_type_id=course_type_id) if course_type_id else Course.objects.all()

    semesters = []
    if course_id:
        semesters = Semester.objects.filter(course_id=course_id).order_by('number')

    students_data = []

    if all([course_type_id, course_id, academic_year_id, semester_number is not None]):
        course_type = CourseType.objects.filter(id=course_type_id).first()

        if course_type and "PU" in course_type.name.upper():
            students = StudentDatabase.objects.filter(
                course_type_id=course_type_id,
                course_id=course_id,
                current_year=semester_number,
                status="Active",
                student_userid__isnull=False,
                pu_admission__isnull=False,
                academic_year__iexact=academic_year_str
            ).select_related('pu_admission', 'degree_admission')
        else:
            students = StudentDatabase.objects.filter(
                course_type_id=course_type_id,
                course_id=course_id,
                semester=semester_number,
                status="Active",
                student_userid__isnull=False,
                degree_admission__isnull=False,
                academic_year__iexact=academic_year_str
            ).select_related('pu_admission', 'degree_admission')

        for student in students:
            admission = student.pu_admission or student.degree_admission
            if not admission:
                continue

            if not student.academic_year:
                print(f"⚠️ Missing academic year for student: {student.student_name}, ID: {student.student_userid}")
                continue

            students_data.append({
                    'admission_no': admission.admission_no,
                    'student_id': student.student_userid,
                    'student_name': student.student_name,
                    'course': student.course,
                    'course_type': student.course_type,
                    'current_year': student.current_year,
                    'semester': student.semester,
                    'admission_course_type': admission.course_type.name if admission.course_type else "",
                    'admission_course': admission.course.name if admission.course else "",
                    'admission_dob': getattr(admission, 'dob', ""),
                    'admission_academic_year': student.academic_year or "",
                    'admission_father_name': getattr(admission, 'father_name', ""),
                    'admission_father_mobile_no': getattr(admission, 'father_mobile_no', "")
                })
    else:
        print("⚠️ Incomplete parameters. Please ensure all filters are provided.")

    context = {
        'course_types': course_types,
        'courses': courses,
        'academic_years': academic_years,
        'semesters': semesters,
        'selected_academic_year': int(academic_year_id) if academic_year_id else None,
        'selected_course_type': int(course_type_id) if course_type_id else None,
        'selected_course': int(course_id) if course_id else None,
        'selected_semester': semester_number,
        'students': students_data,
    }

    return render(request, 'fees/student_fee_list.html', context)


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import OptionalFee
from master.models import StudentDatabase, FeeType
from django.utils.dateparse import parse_date
from django.urls import reverse

@custom_login_required
def optional_fee(request):
    admission_no = request.GET.get('admission_no')

    student = (
        StudentDatabase.objects.filter(pu_admission__admission_no=admission_no).first() or
        StudentDatabase.objects.filter(degree_admission__admission_no=admission_no).first()
    )

    if not student:
        messages.error(request, "Student not found with the given admission number.")
        return redirect('fee_collection_collect')

    if request.method == 'POST':
        row_keys = [key for key in request.POST if key.startswith('fee_type_')]
        row_ids = [key.split('_')[2] for key in row_keys]

        for row_id in row_ids:
            fee_type_id = request.POST.get(f'fee_type_{row_id}')
            amount = request.POST.get(f'amount_{row_id}')
            due_date_str = request.POST.get(f'due_date_{row_id}')

            if not fee_type_id or not amount:
                continue  # Skip if any required data is missing

            due_date = parse_date(due_date_str) if due_date_str else None

            OptionalFee.objects.create(
                student=student,
                student_name=student.student_name,
                admission_no=admission_no,
                fee_type_id=fee_type_id,
                amount=amount,
                due_date=due_date
            )

        messages.success(request, "Fees added successfully.")
        return redirect(f"{reverse('fee_collection_collect')}?admission_no={admission_no}")

    collected_fee_types = OptionalFee.objects.filter(
        admission_no=admission_no
    ).values_list('fee_type_id', flat=True)

    collected_fee_names = list(OptionalFee.objects.filter(
        admission_no=admission_no
    ).values_list('fee_type__name', flat=True))

    all_fee_types = FeeType.objects.filter(is_optional=True)
    disabled_fee_type_ids = []

    collected_names = [f.strip().lower() for f in collected_fee_names]

    if 'hostel' in collected_names:
        transport = all_fee_types.filter(name__iexact='Transport').first()
        if transport:
            disabled_fee_type_ids.append(transport.id)

    if 'transport' in collected_names:
        hostel = all_fee_types.filter(name__iexact='Hostel').first()
        if hostel:
            disabled_fee_type_ids.append(hostel.id)

    context = {
        'student': student,
        'fee_types': all_fee_types,
        'collected_fee_types': list(collected_fee_types),
        'disabled_fee_type_ids': disabled_fee_type_ids
    }
    return render(request, 'fees/optional_fee.html', context)





 
from django.db.models import Sum, Q
from django.shortcuts import render
from fees.models import StudentFeeCollection

@custom_login_required
def fee_dashboard(request):
    # Total expected = sum of amount field
    total_expected = StudentFeeCollection.objects.aggregate(total=Sum('amount'))['total'] or 0

    # Total collected = sum of paid_amount
    total_collected = StudentFeeCollection.objects.aggregate(collected=Sum('paid_amount'))['collected'] or 0

    # Pending payments = sum of balance_amount
    pending_amount = StudentFeeCollection.objects.aggregate(pending=Sum('balance_amount'))['pending'] or 0

    # Count of students with pending fees
    pending_students = StudentFeeCollection.objects.filter(Q(status='Pending') | Q(status='Partial')).values('student_userid').distinct().count()

    # Collection rate
    collection_rate = (total_collected / total_expected * 100) if total_expected else 0

    context = {
        'total_collected': total_collected,
        'pending_amount': pending_amount,
        'collection_rate': round(collection_rate),
        'pending_students': pending_students,
    }
    return render(request, 'fees/fee_dashboard.html', context)










from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal
from urllib.parse import quote

from admission.models import PUAdmission, DegreeAdmission
from master.models import StudentDatabase, FeeType
from fees.models import FeeDeclaration, FeeDeclarationDetail, OptionalFee, StudentFeeCollection
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from urllib.parse import quote
from decimal import Decimal, InvalidOperation

@custom_login_required
def fee_collection_collect(request):

    if request.method == 'POST':

        admission_no = request.POST.get('admission_no')

        selected_fee_ids = request.POST.getlist('selected_fees')

        payment_mode = request.POST.get('payment_mode')

        payment_id = request.POST.get('payment_id')
 
        for fee_id in selected_fee_ids:

            fee_collection = get_object_or_404(StudentFeeCollection, id=fee_id)
 
            # 🔹 Fetch academic year from StudentDatabase for this admission_no

            student_db = StudentDatabase.objects.filter(

                pu_admission__admission_no=fee_collection.admission_no

            ).first() or StudentDatabase.objects.filter(

                degree_admission__admission_no=fee_collection.admission_no

            ).first()
 
            # ✅ Always keep academic_year as string (never None)

            academic_year = str(getattr(student_db, 'academic_year', '') or '')
 
            raw_paid = request.POST.get(f'paid_amount_{fee_id}', '0').replace(',', '').strip()

            try:

                paid_amount = Decimal(raw_paid) if raw_paid else Decimal('0')

            except InvalidOperation:

                messages.error(request, f"Invalid paid amount entered for fee ID {fee_id}. Please enter a valid number.")

                return redirect('fee_collection_collect')
 
            if paid_amount <= 0:

                continue
 
            total_paid = sum(fc.paid_amount for fc in StudentFeeCollection.objects.filter(

                admission_no=fee_collection.admission_no,

                fee_type=fee_collection.fee_type

            ))

            total_discount = sum(fc.applied_discount for fc in StudentFeeCollection.objects.filter(

                admission_no=fee_collection.admission_no,

                fee_type=fee_collection.fee_type

            ))

            cumulative_total = total_paid + total_discount + paid_amount

            new_balance = max(fee_collection.amount - cumulative_total, Decimal('0'))
 
            # 🔹 Get semester and current year as integers

            semester_val = getattr(student_db, 'semester', None) or getattr(student_db, 'current_year', None)

            try:

                semester = int(semester_val) if semester_val is not None else None

            except (ValueError, TypeError):

                semester = None
 
            StudentFeeCollection.objects.create(

                admission_no=fee_collection.admission_no,

                student_userid=fee_collection.student_userid,

                semester=semester,  # ✅ integer if present

                academic_year=academic_year,  # ✅ always string

                fee_type=fee_collection.fee_type,

                amount=fee_collection.amount,

                paid_amount=paid_amount,

                applied_discount=Decimal('0'),

                balance_amount=new_balance,

                due_date=fee_collection.due_date,

                payment_mode=payment_mode,

                payment_id=payment_id,

                payment_date=timezone.now().date(),

                status='Paid' if new_balance == 0 else 'Partial'

            )
 
        messages.success(request, "Payment recorded successfully.")

        return redirect('generate_receipt', admission_no=quote(admission_no))
 
    # ================= GET request handling =================

 
    # ================= GET request handling =================

    admission_no = request.GET.get('admission_no')

    admission = PUAdmission.objects.filter(admission_no=admission_no).first() or DegreeAdmission.objects.filter(admission_no=admission_no).first()

    if not admission:

        messages.error(request, "Admission not found.")

        return redirect('student_fee_list')
 
    student_db = StudentDatabase.objects.filter(

        pu_admission=admission if isinstance(admission, PUAdmission) else None,

        degree_admission=admission if isinstance(admission, DegreeAdmission) else None

    ).first()
 
    # ✅ Always keep academic_year as string

    academic_year = str(getattr(student_db, 'academic_year', '') or '')
 
    scholarship_fee_type = FeeType.objects.filter(name__iexact='discount').first()

    scholarship_amount = Decimal('0')

    if scholarship_fee_type:

        scholarship_optional_fee = OptionalFee.objects.filter(

            admission_no=admission.admission_no,

            fee_type=scholarship_fee_type

        ).first()

        if scholarship_optional_fee:

            scholarship_amount = scholarship_optional_fee.amount
 
    declarations = FeeDeclaration.objects.filter(

        course_type=admission.course_type,

        course=admission.course,

    )

    if hasattr(admission, 'semester') and admission.semester:

        declarations = declarations.filter(semester=admission.semester)

    elif hasattr(student_db, 'current_year') and student_db.current_year:

        declarations = declarations.filter(current_year=student_db.current_year)
 
    declaration_details = FeeDeclarationDetail.objects.filter(

        declaration__in=declarations

    ).select_related('fee_type').order_by('due_date')
 
    fee_collections = []

    discount_applied = False  # Apply scholarship only once
 
    for detail in declaration_details:

        fee_type_instance = detail.fee_type

        fee_amount = detail.amount
 
        paid_total = sum(fc.paid_amount for fc in StudentFeeCollection.objects.filter(

            admission_no=admission.admission_no, fee_type=fee_type_instance))

        discount_total = sum(fc.applied_discount for fc in StudentFeeCollection.objects.filter(

            admission_no=admission.admission_no, fee_type=fee_type_instance))
 
        applied_discount = Decimal('0')

        if not discount_applied and fee_type_instance.is_deductible and scholarship_amount > 0:

            applied_discount = scholarship_amount

            discount_applied = True
 
        balance = fee_amount - paid_total - discount_total - applied_discount
 
        existing = StudentFeeCollection.objects.filter(

            admission_no=admission.admission_no,

            fee_type=fee_type_instance

        ).order_by('payment_date').last()
 
        if existing:

            existing.amount = fee_amount

            existing.due_date = detail.due_date

            existing.save()

            fee_collections.append(existing)

        else:

            fee_collections.append(StudentFeeCollection.objects.create(

                admission_no=admission.admission_no,

                student_userid=getattr(student_db, 'student_userid', '') if student_db else '',

                semester=getattr(student_db, 'semester', None) or getattr(student_db, 'current_year', None),

                academic_year=academic_year,  # ✅ always string

                fee_type=fee_type_instance,

                amount=fee_amount,

                paid_amount=Decimal('0'),

                applied_discount=applied_discount,

                balance_amount=balance,

                due_date=detail.due_date,

                payment_date=timezone.now().date(),  # ✅ Always set payment_date

                status='Pending' if balance > 0 else 'Paid'

            ))
 
    optional_fees = OptionalFee.objects.filter(admission_no=admission.admission_no).exclude(fee_type=scholarship_fee_type)

    for opt_fee in optional_fees:

        fee_type_instance = opt_fee.fee_type

        paid_total = sum(fc.paid_amount for fc in StudentFeeCollection.objects.filter(

            admission_no=admission.admission_no, fee_type=fee_type_instance))

        discount_total = sum(fc.applied_discount for fc in StudentFeeCollection.objects.filter(

            admission_no=admission.admission_no, fee_type=fee_type_instance))

        balance = opt_fee.amount - paid_total - discount_total
 
        existing = StudentFeeCollection.objects.filter(

            admission_no=admission.admission_no, fee_type=fee_type_instance

        ).order_by('payment_date').last()
 
        if existing:

            existing.amount = opt_fee.amount

            existing.due_date = opt_fee.due_date

            existing.save()

            fee_collections.append(existing)

        else:

            fee_collections.append(StudentFeeCollection.objects.create(

                admission_no=admission.admission_no,

                student_userid=getattr(student_db, 'student_userid', '') if student_db else '',

                semester=getattr(student_db, 'semester', None) or getattr(student_db, 'current_year', None),

                academic_year=academic_year,  # ✅ always string

                fee_type=fee_type_instance,

                amount=opt_fee.amount,

                paid_amount=Decimal('0'),

                applied_discount=Decimal('0'),

                balance_amount=balance,

                due_date=opt_fee.due_date,

                payment_date=timezone.now().date(),

                status='Pending'

            ))
 
    # Remove scholarship from display

    fee_collections = [f for f in fee_collections if f.fee_type.name.lower() != 'scholarship']

    fee_collections = sorted(fee_collections, key=lambda x: x.due_date or timezone.datetime.max.date())
 
    fee_display_list = []

    for fee in fee_collections:

        total_paid = sum(fc.paid_amount for fc in StudentFeeCollection.objects.filter(

            admission_no=fee.admission_no, fee_type=fee.fee_type))

        total_discount = sum(fc.applied_discount for fc in StudentFeeCollection.objects.filter(

            admission_no=fee.admission_no, fee_type=fee.fee_type))

        balance = fee.amount - total_paid - total_discount
 
        fee_display_list.append({

            'id': fee.id,

            'fee_type': fee.fee_type,

            'due_date': fee.due_date,

            'amount': fee.amount,

            'paid_amount': total_paid,

            'balance_amount': balance,

            'status': 'Paid' if balance == 0 else 'Partial' if total_paid > 0 else 'Pending',

            'applied_discount': total_discount,

            'total_paid': total_paid + total_discount,

        })
 
    context = {

        'student': {

            'admission_no': admission.admission_no,

            'student_name': admission.student_name,

            'admission_course_type': admission.course_type.name,

            'admission_course': admission.course.name,

            'admission_dob': admission.dob,

            'admission_father_name': admission.father_name,

            'admission_father_mobile_no': admission.father_mobile_no,

            'category': admission.category,

            'roll_number': getattr(student_db, 'student_userid', '') if student_db else '',

            'semester': getattr(student_db, 'semester', None),

            'current_year': getattr(student_db, 'current_year', None),

        },

        'fee_collections': fee_display_list,

        'now': timezone.now()

    }
 
    return render(request, 'fees/fee_collection_collect.html', context)

 









# def fee_collection_collect(request):
#     if request.method == 'POST':
#         admission_no = request.POST.get('admission_no')
#         selected_fee_ids = request.POST.getlist('selected_fees')
#         payment_mode = request.POST.get('payment_mode')
#         payment_id = request.POST.get('payment_id')

#         for fee_id in selected_fee_ids:
#             fee_collection = get_object_or_404(StudentFeeCollection, id=fee_id)
#             paid_amount_str = request.POST.get(f'paid_amount_{fee_id}', '0')
#             paid_amount = Decimal(paid_amount_str) if paid_amount_str else Decimal('0')

#             if paid_amount <= 0:
#                 continue

#             new_paid_amount = fee_collection.paid_amount + paid_amount
#             new_balance = max(fee_collection.amount - new_paid_amount, Decimal('0'))
#             status = 'Paid' if new_balance == 0 else 'Partial'

#             fee_collection.paid_amount = new_paid_amount
#             fee_collection.balance_amount = new_balance
#             fee_collection.payment_mode = payment_mode
#             fee_collection.payment_id = payment_id
#             fee_collection.payment_date = timezone.now()
#             fee_collection.status = status
#             fee_collection.save()

#         messages.success(request, "Payment recorded successfully.")
#         return redirect('generate_receipt', admission_no=quote(admission_no))


#     admission_no = request.GET.get('admission_no')
#     admission = None

#     try:
#         admission = PUAdmission.objects.get(admission_no=admission_no)
#     except PUAdmission.DoesNotExist:
#         try:
#             admission = DegreeAdmission.objects.get(admission_no=admission_no)
#         except DegreeAdmission.DoesNotExist:
#             messages.error(request, "Admission not found.")
#             return redirect('student_fee_list')

#     student_db = StudentDatabase.objects.filter(
#         pu_admission=admission if isinstance(admission, PUAdmission) else None,
#         degree_admission=admission if isinstance(admission, DegreeAdmission) else None
#     ).first()

#     scholarship_fee_type = FeeType.objects.filter(name__iexact='discount').first()
#     scholarship_amount = Decimal('0')
#     if scholarship_fee_type:
#         scholarship_optional_fee = OptionalFee.objects.filter(
#             admission_no=admission.admission_no,
#             fee_type=scholarship_fee_type
#         ).first()
#         if scholarship_optional_fee:
#             scholarship_amount = scholarship_optional_fee.amount

#     declarations = FeeDeclaration.objects.filter(
#         course_type=admission.course_type,
#         course=admission.course,
#     )
#     if hasattr(admission, 'semester') and admission.semester:
#         declarations = declarations.filter(semester=admission.semester)
#     elif hasattr(admission, 'current_year') and admission.current_year:
#         declarations = declarations.filter(current_year=admission.current_year)

#     declaration_details = FeeDeclarationDetail.objects.filter(declaration__in=declarations).select_related('fee_type').order_by('due_date')

#     fee_collections = []
#     remaining_scholarship = scholarship_amount
#     for detail in declaration_details:
#         fee_type_instance = detail.fee_type
#         fee_amount = detail.amount
#         applied_discount = Decimal('0')

#         if fee_type_instance.is_deductible and remaining_scholarship > 0:
#             deduction = min(fee_amount, remaining_scholarship)
#             fee_amount -= deduction
#             applied_discount = deduction
#             remaining_scholarship -= deduction

#         existing = StudentFeeCollection.objects.filter(
#             admission_no=admission.admission_no,
#             fee_type=fee_type_instance,
#         ).first()

#         if existing:
#             existing.amount = fee_amount
#             existing.balance_amount = fee_amount - existing.paid_amount
#             existing.due_date = detail.due_date
#             existing.save()
#             existing.applied_discount = applied_discount
#             fee_collections.append(existing)
#         else:
#             new_record = StudentFeeCollection.objects.create(
#                 admission_no=admission.admission_no,
#                 student_userid=getattr(student_db, 'student_userid', '') if student_db else '',
#                 semester=getattr(admission, 'semester', None),
#                 fee_type=fee_type_instance,
#                 amount=fee_amount,
#                 paid_amount=Decimal('0'),
#                 balance_amount=fee_amount,
#                 due_date=detail.due_date,
#                 status='Pending'
#             )
#             new_record.applied_discount = applied_discount
#             fee_collections.append(new_record)

#     optional_fees = OptionalFee.objects.filter(admission_no=admission.admission_no).exclude(fee_type=scholarship_fee_type)
#     for opt_fee in optional_fees:
#         fee_type_instance = opt_fee.fee_type
#         existing = StudentFeeCollection.objects.filter(
#             admission_no=admission.admission_no,
#             fee_type=fee_type_instance,
#         ).first()

#         if existing:
#             existing.amount = opt_fee.amount
#             existing.balance_amount = opt_fee.amount - existing.paid_amount
#             existing.due_date = opt_fee.due_date
#             existing.save()
#             existing.applied_discount = Decimal('0')
#             fee_collections.append(existing)
#         else:
#             new_record = StudentFeeCollection.objects.create(
#                 admission_no=admission.admission_no,
#                 student_userid=getattr(student_db, 'student_userid', '') if student_db else '',
#                 semester=getattr(admission, 'semester', None),
#                 fee_type=fee_type_instance,
#                 amount=opt_fee.amount,
#                 paid_amount=Decimal('0'),
#                 balance_amount=opt_fee.amount,
#                 due_date=opt_fee.due_date,
#                 status='Pending'
#             )
#             new_record.applied_discount = Decimal('0')
#             fee_collections.append(new_record)

#     fee_collections = [f for f in fee_collections if f.fee_type.name.lower() != 'scholarship']
#     fee_collections = sorted(fee_collections, key=lambda x: x.due_date or timezone.datetime.max.date())

#     # Attach discount cleanly to avoid template confusion
#     fee_display_list = []
#     for fee in fee_collections:
#         fee_display_list.append({
#             'id': fee.id,
#             'fee_type': fee.fee_type,
#             'due_date': fee.due_date,
#             'amount': fee.amount,
#             'paid_amount': fee.paid_amount,
#             'balance_amount': fee.balance_amount,
#             'status': fee.status,
#             'applied_discount': getattr(fee, 'applied_discount', Decimal('0'))
#         })

#     context = {
#         'student': {
#             'admission_no': admission.admission_no,
#             'student_name': admission.student_name,
#             'admission_course_type': admission.course_type.name,
#             'admission_course': admission.course.name,
#             'admission_dob': admission.dob,
#             'admission_father_name': admission.father_name,
#             'admission_father_mobile_no': admission.father_mobile_no,
#             'category': admission.category,
#             'roll_number': getattr(student_db, 'student_userid', '') if student_db else '',
#         },
#         'fee_collections': fee_display_list,
#         'now': timezone.now()
#     }
#     return render(request, 'fees/fee_collection_collect.html', context)






from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from fees.models import StudentFeeCollection


@custom_login_required
@csrf_exempt
def collect_fee_payment_page(request):
    now = timezone.now()

    if request.method == "POST":
        admission_no = request.POST.get("admission_no")
        fee_ids = request.POST.getlist("selected_fees")
        payment_mode = request.POST.get("payment_mode")
        payment_reference = request.POST.get("payment_reference", "").strip()

        for fee_id in fee_ids:
            try:
                paid_amount_str = request.POST.get(f"paid_amount_{fee_id}", "0").strip()
                if not paid_amount_str:
                    continue

                paid_amount = float(paid_amount_str)
                fee_obj = StudentFeeCollection.objects.get(id=fee_id)

                # Update fee collection
                fee_obj.paid_amount += paid_amount
                fee_obj.balance_amount = max(fee_obj.amount - fee_obj.paid_amount, 0)
                fee_obj.payment_mode = payment_mode
                fee_obj.payment_reference = payment_reference
                fee_obj.payment_date = now.date()
                fee_obj.status = "Paid" if fee_obj.balance_amount == 0 else "Partial"
                fee_obj.save()

                # Save payment history
                StudentPaymentHistory.objects.create(
                    admission_no=admission_no,
                    fee=fee_obj,
                    paid_amount=paid_amount,
                    payment_mode=payment_mode,
                    payment_reference=payment_reference,
                )

                print(f"✅ Payment done for Fee ID {fee_id}")

            except Exception as e:
                print(f"❌ Error for Fee ID {fee_id}: {e}")

        return redirect("student_fee_list")

    return redirect("student_fee_list")



# admission/views.py

import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.views.decorators.http import require_GET

# admission/views.py


@custom_login_required
@require_GET
def generate_qr_dynamic(request):
    amount = request.GET.get("amount")
    if not amount:
        return HttpResponse("Amount is required", status=400)

    upi_id = "9483508971@ybl"
    upi_link = f"upi://pay?pa={upi_id}&pn=Your College Name&am={amount}&cu=INR"

    qr = qrcode.make(upi_link)
    buffer = BytesIO()
    qr.save(buffer)
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type="image/png")







from decimal import Decimal
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML
from fees.models import StudentFeeCollection
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from admission.models import PUAdmission, DegreeAdmission
from master.models import StudentDatabase
from urllib.parse import unquote
 
from django.utils import timezone
from django.db.models import Q
from django.utils.timezone import now
from django.db import transaction


import logging
from datetime import date


logger = logging.getLogger(__name__)

from django.utils.timezone import localdate
import logging

logger = logging.getLogger(__name__)



from decimal import Decimal
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML
from fees.models import StudentFeeCollection
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from admission.models import PUAdmission, DegreeAdmission
from master.models import StudentDatabase
from urllib.parse import unquote
 
from django.utils import timezone
from django.db.models import Q
from django.utils.timezone import now
from django.db import transaction


import logging
from datetime import date


logger = logging.getLogger(__name__)

from django.utils.timezone import localdate
import logging
import re

logger = logging.getLogger(__name__)


from collections import defaultdict

from django.template.loader import get_template

from weasyprint import HTML


from django.utils.timezone import localdate
from django.db import transaction
from collections import defaultdict
from django.utils.timezone import now as timezone_now
from decimal import Decimal
from django.template.loader import get_template
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from urllib.parse import unquote
import re

# from django.shortcuts import get_object_or_404
# from django.utils.timezone import localdate, now as timezone_now
# from collections import defaultdict
# from decimal import Decimal
# from django.db import transaction
# from django.db.models import Q
# from django.http import HttpResponse
# from django.template.loader import get_template
# from weasyprint import HTML
# import re
# from urllib.parse import unquote


# @custom_login_required
# def generate_receipt(request, admission_no):
#     admission_no = unquote(admission_no).split(" - ")[0].strip()

#     # Fetch admission object
#     admission = PUAdmission.objects.filter(admission_no__iexact=admission_no).first()
#     if not admission:
#         admission = get_object_or_404(DegreeAdmission, admission_no__iexact=admission_no)

#     # Get student DB
#     student_db = (
#         StudentDatabase.objects.filter(pu_admission=admission).first()
#         if isinstance(admission, PUAdmission)
#         else StudentDatabase.objects.filter(degree_admission=admission).first()
#     )

#     today = localdate()

#     # All fee collections
#     all_fee_collections = StudentFeeCollection.objects.filter(
#         admission_no=admission.admission_no
#     ).order_by('fee_type__name', 'id')

#     # Filter today's payments
#     fee_collections_today = all_fee_collections.filter(
#         payment_date=today
#     ).filter(Q(paid_amount__gt=0) | Q(applied_discount__gt=0))

#     # 🚨 LOG: Today's Fee Collections
#     print("\n===== DEBUG: Today's Fee Collections =====")
#     for fee in fee_collections_today:
#         print(f"FeeType: {fee.fee_type.name}, Paid: {fee.paid_amount}, Discount: {fee.applied_discount}, Payment Date: {fee.payment_date}, Receipt: {fee.receipt_no}, Mode: {fee.payment_mode}")

#     # Assign receipt numbers
#     with transaction.atomic():
#         for fee in fee_collections_today:
#             current_year = timezone_now().year
#             next_year = current_year + 1
#             promotion_cycle = f"{current_year}-{str(next_year)[-2:]}"
#             course_name = admission.course.name.replace(" ", "").upper()[:4]
#             prefix = f"PSCM-001-{promotion_cycle}-{course_name}-"

#             last_receipt = StudentFeeCollection.objects.filter(
#                 receipt_no__startswith=prefix
#             ).order_by('-receipt_no').values_list('receipt_no', flat=True).first()

#             last_number = int(re.search(r'(\d{4})$', last_receipt).group(1)) if last_receipt else 0
#             new_receipt = f"{prefix}{str(last_number + 1).zfill(4)}"

#             fee.receipt_no = new_receipt
#             fee.receipt_date = today
#             fee.save()

#             print(f"Assigned Receipt No: {new_receipt} to FeeType: {fee.fee_type.name}")

#     # Grouping and calculating
#     fee_group_map = defaultdict(list)
#     for fee in all_fee_collections:
#         fee_group_map[fee.fee_type].append(fee)

#     grouped_fees = []
#     total_paid = Decimal('0.00')
#     total_discount = Decimal('0.00')
#     total_amount = Decimal('0.00')

#     print("\n===== DEBUG: Grouped Fee Summary =====")
#     for fee_type, entries in fee_group_map.items():
#         today_paid = sum(e.paid_amount or Decimal('0.00') for e in entries if e.payment_date == today)
#         today_discount = sum(e.applied_discount or Decimal('0.00') for e in entries if e.payment_date == today)
#         has_today_activity = any(
#                 e.payment_date == today and ((e.paid_amount or 0) > 0 or (e.applied_discount or 0) > 0)
#                 for e in entries
#             )
#         if not has_today_activity:
#              continue



#         fee_name = fee_type.name
#         if fee_name[-1].isdigit():
#             prefix, number = fee_name[:-1], fee_name[-1]
#             display_name = f"{prefix} (Installment {number})"
#         else:
#             display_name = fee_name

#         amount = entries[0].amount
#         total_paid_for_type = sum(e.paid_amount or Decimal('0.00') for e in entries)
#         total_discount_for_type = sum(e.applied_discount or Decimal('0.00') for e in entries)
#         balance_amount = amount - total_paid_for_type - total_discount_for_type

#         print(f"Type: {display_name}, Amt: {amount}, Paid Today: {today_paid}, Discount Today: {today_discount}, Balance: {balance_amount}")

#         grouped_fees.append({
#             'display_fee_type': display_name,
#             'amount': amount,
#             'paid_amount': today_paid,
#             'applied_discount': today_discount,
#             'balance_amount': balance_amount,
#             'due_date': entries[0].due_date
#         })

#         total_paid += today_paid
#         total_discount += today_discount
#         total_amount += amount

#     student = {
#         'admission_no': admission.admission_no,
#         'student_name': admission.student_name,
#         'admission_course_type': getattr(admission, 'course_type', ''),
#         'admission_course': getattr(admission, 'course', ''),
#         'roll_number': getattr(student_db, 'student_userid', ''),
#         'semester': getattr(student_db, 'semester', None),
#         'current_year': getattr(student_db, 'current_year', None),
#     }

#     context = {
#         'admission': admission,
#         'student': student,
#         'fee_collections': grouped_fees,
#         'total_paid': total_paid,
#         'applied_discount': total_discount,
#         'total_amount': total_amount,
#         'total_due': sum(f['balance_amount'] for f in grouped_fees),
#         'now': timezone_now(),
#         'receipt_no': fee_collections_today[0].receipt_no if fee_collections_today else None,
#         'receipt_date': fee_collections_today[0].receipt_date if fee_collections_today else None,
#         'payment_mode': fee_collections_today[0].payment_mode if fee_collections_today else '',
#     }

#     html_string = get_template('fees/student_receipt_pdf.html').render(context)
#     html = HTML(string=html_string)
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'inline; filename="Receipt_{admission.admission_no}.pdf"'
#     html.write_pdf(target=response)

#     return response





import os
import re
from decimal import Decimal
from collections import defaultdict
from urllib.parse import unquote

from django.shortcuts import get_object_or_404
from django.utils.timezone import localdate, now as timezone_now
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import get_template

import pdfkit
from django.conf import settings


@custom_login_required
def generate_receipt(request, admission_no):
    admission_no = unquote(admission_no).split(" - ")[0].strip()

    # Fetch admission object
    admission = PUAdmission.objects.filter(admission_no__iexact=admission_no).first()
    if not admission:
        admission = get_object_or_404(DegreeAdmission, admission_no__iexact=admission_no)

    # Get student DB
    student_db = (
        StudentDatabase.objects.filter(pu_admission=admission).first()
        if isinstance(admission, PUAdmission)
        else StudentDatabase.objects.filter(degree_admission=admission).first()
    )

    today = localdate()

    # All fee collections
    all_fee_collections = StudentFeeCollection.objects.filter(
        admission_no=admission.admission_no
    ).order_by('fee_type__name', 'id')

    # Filter today's payments
    fee_collections_today = all_fee_collections.filter(
        payment_date=today
    ).filter(Q(paid_amount__gt=0) | Q(applied_discount__gt=0))

    # Debug log
    print("\n===== DEBUG: Today's Fee Collections =====")
    for fee in fee_collections_today:
        print(f"FeeType: {fee.fee_type.name}, Paid: {fee.paid_amount}, Discount: {fee.applied_discount}, "
              f"Payment Date: {fee.payment_date}, Receipt: {fee.receipt_no}, Mode: {fee.payment_mode}")

    # Assign receipt numbers
    with transaction.atomic():
        for fee in fee_collections_today:
            current_year = timezone_now().year
            next_year = current_year + 1
            promotion_cycle = f"{current_year}-{str(next_year)[-2:]}"
            course_name = admission.course.name.replace(" ", "").upper()[:4]
            prefix = f"PSCM-001-{promotion_cycle}-{course_name}-"

            last_receipt = StudentFeeCollection.objects.filter(
                receipt_no__startswith=prefix
            ).order_by('-receipt_no').values_list('receipt_no', flat=True).first()

            last_number = int(re.search(r'(\d{4})$', last_receipt).group(1)) if last_receipt else 0
            new_receipt = f"{prefix}{str(last_number + 1).zfill(4)}"

            fee.receipt_no = new_receipt
            fee.receipt_date = today
            fee.save()

            print(f"Assigned Receipt No: {new_receipt} to FeeType: {fee.fee_type.name}")

    # Grouping and calculating
    fee_group_map = defaultdict(list)
    for fee in all_fee_collections:
        fee_group_map[fee.fee_type].append(fee)

    grouped_fees = []
    total_paid = Decimal('0.00')
    total_discount = Decimal('0.00')
    total_amount = Decimal('0.00')

    print("\n===== DEBUG: Grouped Fee Summary =====")
    for fee_type, entries in fee_group_map.items():
        today_paid = sum(e.paid_amount or Decimal('0.00') for e in entries if e.payment_date == today)
        today_discount = sum(e.applied_discount or Decimal('0.00') for e in entries if e.payment_date == today)
        has_today_activity = any(
            e.payment_date == today and ((e.paid_amount or 0) > 0 or (e.applied_discount or 0) > 0)
            for e in entries
        )
        if not has_today_activity:
            continue

        fee_name = fee_type.name
        if fee_name[-1].isdigit():
            prefix, number = fee_name[:-1], fee_name[-1]
            display_name = f"{prefix} (Installment {number})"
        else:
            display_name = fee_name

        amount = entries[0].amount
        total_paid_for_type = sum(e.paid_amount or Decimal('0.00') for e in entries)
        total_discount_for_type = sum(e.applied_discount or Decimal('0.00') for e in entries)
        balance_amount = amount - total_paid_for_type - total_discount_for_type

        print(f"Type: {display_name}, Amt: {amount}, Paid Today: {today_paid}, "
              f"Discount Today: {today_discount}, Balance: {balance_amount}")

        grouped_fees.append({
            'display_fee_type': display_name,
            'amount': amount,
            'paid_amount': today_paid,
            'applied_discount': today_discount,
            'balance_amount': balance_amount,
            'due_date': entries[0].due_date
        })

        total_paid += today_paid
        total_discount += today_discount
        total_amount += amount

    # Student details
    student = {
        'admission_no': admission.admission_no,
        'student_name': admission.student_name,
        'admission_course_type': getattr(admission, 'course_type', ''),
        'admission_course': getattr(admission, 'course', ''),
        'roll_number': getattr(student_db, 'student_userid', ''),
        'semester': getattr(student_db, 'semester', None),
        'current_year': getattr(student_db, 'current_year', None),
    }

    # Template context
    context = {
        'admission': admission,
        'student': student,
        'fee_collections': grouped_fees,
        'total_paid': total_paid,
        'applied_discount': total_discount,
        'total_amount': total_amount,
        'total_due': sum(f['balance_amount'] for f in grouped_fees),
        'now': timezone_now(),
        'receipt_no': fee_collections_today[0].receipt_no if fee_collections_today else None,
        'receipt_date': fee_collections_today[0].receipt_date if fee_collections_today else None,
        'payment_mode': fee_collections_today[0].payment_mode if fee_collections_today else '',
    }

    # Render HTML
    html_string = get_template('fees/student_receipt_pdf.html').render(context)

    # ✅ Configure wkhtmltopdf path
    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

    # ✅ PDF options (A5 layout + margins)
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

    # ✅ Return PDF as inline display (like WeasyPrint version)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="Receipt_{admission.admission_no}.pdf"'
    return response

