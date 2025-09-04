
from django.shortcuts import render, get_object_or_404
from master.models import Semester, Employee, Subject, Course, CourseType
from .models import TimetableEntry, TimeSlot
from .forms import TimeSlotForm, TimetableEntryForm
from datetime import datetime
import sys
from master.decorators import custom_login_required

@custom_login_required
def timetable_dashboard(request):
    # Active Programs: all CourseTypes
    program_qs = CourseType.objects.all()
    active_programs_count = program_qs.count()
    active_programs_names = ", ".join(program_qs.values_list('name', flat=True))

    # Current time and weekday (server timezone, adjust if needed)
    now = datetime.now()
    today_weekday = now.strftime('%A')  # e.g., "Friday"
    # Cross-platform hour formatting (no leading zero)
    current_time = now.strftime('%I:%M %p').lstrip('0')
    # Total Classes Today (all TimetableEntries scheduled for today)
    total_classes_today = TimetableEntry.objects.filter(day=today_weekday).count()

    # Weekly Classes (all entries in a week)
    weekly_classes = TimetableEntry.objects.count()

    # Total subjects (for your summary, if needed)
    total_subjects = Subject.objects.count()

    context = {
        'total_classes_today': total_classes_today,
        'active_programs_count': active_programs_count,
        'active_programs_names': active_programs_names,
        'current_time': current_time,
        'today_weekday': today_weekday,
        'weekly_classes': weekly_classes,
        'total_subjects': total_subjects,
    }
    return render(request, 'timetable/timetable_dashboard.html', context)


   





from django.shortcuts import render
from django.utils import timezone
from .models import TimetableEntry, TimeSlot
from master.models import Semester, Course, CourseType
from django.shortcuts import render
from django.utils import timezone


from django.shortcuts import render
from django.utils import timezone
from timetable.models import TimetableEntry
from master.models import Course, CourseType, Semester

from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import date, datetime
from .models import TimetableEntry, TimeSlot
from master.models import Semester, Course, CourseType
from attendence.models import attendance
from master.models import Employee  # Adjust the import as per your model location



def get_date_for_weekday(reference_date, weekday_name):
    weekday_map = {
        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
        'Thursday': 3, 'Friday': 4
    }
    target_weekday = weekday_map.get(weekday_name)
    if target_weekday is None:
        return reference_date
    return reference_date - timezone.timedelta(days=(reference_date.weekday() - target_weekday) % 7)
from datetime import timedelta
from django.utils import timezone
from .models import DailySubstitution  # Ensure this import is present

from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import TimetableEntry, DailySubstitution
from master.models import Course, CourseType
from attendence.models import attendance

def get_date_for_weekday(base_date, target_weekday):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    if target_weekday not in days:
        return base_date
    current_weekday = base_date.weekday()  # 0 = Monday
    target_weekday_index = days.index(target_weekday)
    delta = target_weekday_index - current_weekday
    return base_date + timedelta(days=delta)




from django.utils import timezone
from django.utils.dateparse import parse_date
from django.shortcuts import render
from .models import TimetableEntry, TimeSlot, DailySubstitution
from master.models import Course, Semester
from core.utils import get_logged_in_user, log_activity
from attendence.models import attendance

@custom_login_required
def daily_timetable(request):
    week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    today = timezone.now()
    today_day = today.strftime('%A')
    if today_day not in week_days:
        today_day = 'Monday'

    raw_date = request.GET.get('date')
    selected_date = parse_date(raw_date) if raw_date else today.date()

    selected_day = request.GET.get('day') or today_day
    course_type_id = request.GET.get('course_type')
    academic_year_id = request.GET.get('academic_year')
    course_id = request.GET.get('course')
    semester_number = request.GET.get('semester')

    # Filter courses and semesters dynamically
    course_type = CourseType.objects.filter(id=course_type_id).first() if course_type_id else None
    academic_year = AcademicYear.objects.filter(id=academic_year_id).first() if academic_year_id else None

    filtered_courses = Course.objects.filter(is_active=True)
    if course_type:
        filtered_courses = filtered_courses.filter(course_type=course_type)
    if academic_year:
        filtered_courses = filtered_courses.filter(academic_year=academic_year)

    filtered_semesters = Semester.objects.filter(course_id=course_id) if course_id else Semester.objects.none()

    # Default course and semester if not provided
    if not course_id:
        first_course = filtered_courses.first()
        if first_course:
            course_id = str(first_course.id)

    if not semester_number:
        first_sem = Semester.objects.filter(course_id=course_id).first()
        if first_sem:
            semester_number = str(first_sem.number)

    filters = {'day__iexact': selected_day}
    if course_id:
        filters['course_id'] = course_id
    if semester_number:
        filters['semester_number'] = semester_number

    time_slots = TimeSlot.objects.all().order_by('start_time')
    entries = TimetableEntry.objects.filter(**filters).select_related('faculty', 'subject', 'time_slot')

    timetable = {}
    for slot in time_slots:
        entry = entries.filter(time_slot=slot).first()
        if entry:
            substitution = DailySubstitution.objects.filter(
                timetable_entry=entry,
                date=selected_date
            ).select_related('substitute_faculty', 'updated_subject').first()

            if substitution:
                entry.faculty = substitution.substitute_faculty
                entry.subject = substitution.updated_subject
                entry.is_substituted = True
                entry.substitution_id = substitution.id
            else:
                entry.is_substituted = False

            att = attendance.objects.filter(employee=entry.faculty, date=selected_date).first()
            entry.attendance_status = att.status if att else "N/A"

        timetable[slot] = entry

    # Log viewing
    user = get_logged_in_user(request)
    if user:
        course_name = Course.objects.filter(id=course_id).first()
        log_activity(
            user=request.user,
            action='viewed',
            instance=None,
            message=f"Viewed daily timetable for {selected_day} - {course_name.name if course_name else 'Unknown Course'} - Semester {semester_number}"
        )

    return render(request, 'timetable/daily.html', {
        'program_types': CourseType.objects.all(),
        'academic_years': AcademicYear.objects.all(),
        'courses': filtered_courses,
        'semesters': filtered_semesters,
        'selected_course_type_id': course_type_id,
        'selected_academic_year_id': academic_year_id,
        'selected_course_id': course_id,
        'selected_semester_number': semester_number,
        'selected_day': selected_day,
        'today_day': today_day,
        'week_days': week_days,
        'selected_date': selected_date,
        'time_slots': time_slots,
        'timetable': timetable,
        'entries': entries,
    })





from django.shortcuts import render, get_object_or_404, redirect
from .models import TimetableEntry, Employee, DailySubstitution, Subject
from datetime import datetime
from master.models import Subject
from django.utils.dateparse import parse_date
from datetime import datetime
from attendence.models import attendance  
from core.utils import get_logged_in_user,log_activity

from django.contrib import messages  # ✅ Add this import at the top if not already

@custom_login_required
def timetable_form_edit(request, entry_id):
    entry = get_object_or_404(TimetableEntry, id=entry_id)
    
    # Get the date
    raw_date = request.GET.get('date')
    date = parse_date(raw_date) if raw_date else datetime.today().date()

    day = entry.day
    timeslot = entry.time_slot
    entry_start = timeslot.start_time
    entry_end = timeslot.end_time

    # Eligible faculties
    eligible_faculties = Employee.objects.filter(role__in=['Primary', 'Secondary'])

    # Busy faculties
    busy_faculties = TimetableEntry.objects.filter(
        day=day,
        time_slot__start_time__lt=entry_end,
        time_slot__end_time__gt=entry_start,
    ).values_list('faculty_id', flat=True)

    free_faculties = eligible_faculties.exclude(id__in=busy_faculties)

    # Present faculties
    present_faculty_ids = attendance.objects.filter(
        date=date,
        status__in=['Present', 'Late']
    ).values_list('employee_id', flat=True)

    available_faculties = free_faculties.filter(id__in=present_faculty_ids)

    if request.method == 'POST':
        faculty_id = request.POST.get('faculty')
        subject_id = request.POST.get('subject')

        faculty = get_object_or_404(Employee, id=faculty_id)
        subject = get_object_or_404(Subject, id=subject_id)

        substitution_obj, created = DailySubstitution.objects.update_or_create(
            timetable_entry=entry,
            date=date,
            defaults={
                'substitute_faculty': faculty,
                'updated_subject': subject
            }
        )

        user = get_logged_in_user(request)
        log_activity(user, 'assigned', substitution_obj)

        # ✅ Snackbar success message
        messages.success(
            request,
            f"Substitution assigned to {faculty.name} for {subject.name} on {date.strftime('%d-%b-%Y')}."
        )

        return redirect('daily_timetable')

    context = {
        'entry': entry,
        'free_faculties': available_faculties,
        'subjects': Subject.objects.all(),
        'date': date,
    }
    return render(request, 'timetable/substitute_timetable_entry.html', context)


from django.shortcuts import get_object_or_404, redirect, render
from .models import DailySubstitution

@custom_login_required
def timetable_form_delete(request, substitution_id):
    substitution = get_object_or_404(DailySubstitution, id=substitution_id)
    substitution.delete()

    # Redirect to the timetable page (you can add ?date=... later if needed)
    return redirect('daily_timetable')

from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_date
from datetime import datetime

@custom_login_required
def timetable_form_view(request, entry_id):
    entry = get_object_or_404(TimetableEntry, id=entry_id)

    raw_date = request.GET.get('date')
    date = parse_date(raw_date) if raw_date else datetime.today().date()

    substitution = DailySubstitution.objects.filter(timetable_entry=entry, date=date).first()

    free_faculties = [substitution.substitute_faculty] if substitution else []
    subjects = [substitution.updated_subject or entry.subject] if substitution else []

    context = {
        'entry': entry,
        'free_faculties': free_faculties,
        'subjects': subjects,
        'date': date,
        'readonly': True,
        'substitution': substitution,
    }
    return render(request, 'timetable/substitute_timetable_entry.html', context)



from django.http import JsonResponse
from master.models import Course
 
@custom_login_required
def get_semesters_by_course(request):
    if request.method == "POST":
        course_id = request.POST.get("course_id")
 
        if not course_id or not course_id.isdigit():
            return JsonResponse({'error': 'Invalid course ID'}, status=400)
 
        try:
            course = Course.objects.get(id=int(course_id))
            semester_list = []
 
            course_type_name = course.course_type.name.strip().lower()
            course_name = course.name
 
            # Debug logging
            print(f"Course selected: {course_name} (Type: {course_type_name})")
 
            # PU or similar types use duration_years
            if "pu" in course_type_name:
                total = course.duration_years or 0
                for i in range(1, total + 1):
                    semester_list.append({
                        'number': i,
                        'name': f"{course_name} Year {i}"
                    })
            else:
                total = course.total_semesters or 0
                for i in range(1, total + 1):
                    semester_list.append({
                        'number': i,
                        'name': f"{course_name} Semester {i}"
                    })
 
            if not semester_list:
                semester_list.append({
                    'number': 0,
                    'name': "NOT APPLICABLE"
                })
 
            return JsonResponse({'semesters': semester_list})
 
        except Course.DoesNotExist:
            return JsonResponse({'error': 'Course not found'}, status=404)
 
    return JsonResponse({'error': 'Invalid request method'}, status=400)





from django.shortcuts import render
from datetime import date, timedelta
from .models import TimetableEntry, TimeSlot
from master.models import Course
from attendence.models import attendance


def get_date_for_weekday(base_date, target_weekday):
    week_day_map = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    base_weekday = base_date.weekday()  # 0 = Monday
    target_index = week_day_map.index(target_weekday)
    delta = target_index - base_weekday
    return base_date + timedelta(days=delta)


from django.shortcuts import render
from datetime import date
from .models import TimetableEntry
from master.models import Course, Semester
from attendence.models import attendance
from core.utils import log_activity 

@custom_login_required
def weekly_timetable_view(request, course_id=None, semester_number=None):
    from datetime import date
    from django.db.models import Q
    from attendence.models import attendance
    from timetable.models import TimetableEntry, TimeSlot
    from master.models import CourseType, AcademicYear, Course, Semester

    week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    today = date.today()

    # Step 1: Get selected filters from GET or fallback to URL kwargs
    selected_program_type = request.GET.get('course_type', '')
    selected_academic_year = request.GET.get('academic_year', '')
    selected_course_id = request.GET.get('course') or (str(course_id) if course_id else '')
    selected_semester_number = request.GET.get('semester') or (str(semester_number) if semester_number else '')

    # Step 2: Initial querysets
    program_types = CourseType.objects.all()
    academic_years = AcademicYear.objects.all()
    courses = Course.objects.filter(is_active=True)
    semesters = Semester.objects.none()

    # Step 3: Apply dynamic filtering
    if selected_program_type:
        courses = courses.filter(course_type_id=selected_program_type)
        academic_year_ids = courses.values_list('academic_year_id', flat=True).distinct()
        academic_years = AcademicYear.objects.filter(id__in=academic_year_ids)

    if selected_academic_year:
        courses = courses.filter(academic_year_id=selected_academic_year)

    if selected_course_id:
        semesters = Semester.objects.filter(course_id=selected_course_id)

    # Step 4: Auto-select defaults if not provided
    if not selected_course_id and courses.exists():
        selected_course = courses.first()
        selected_course_id = str(selected_course.id)
        semesters = Semester.objects.filter(course=selected_course)

    if not selected_semester_number and semesters.exists():
        selected_semester_number = str(semesters.first().number)

    # Step 5: Fetch timetable
    timetable = {}
    time_slots_set = set()

    if selected_course_id and selected_semester_number:
        for day in week_days:
            entries = list(TimetableEntry.objects.filter(
                course_id=selected_course_id,
                semester_number=selected_semester_number,
                day=day
            ).select_related('time_slot', 'subject', 'faculty').order_by('time_slot__start_time'))

            target_date = get_date_for_weekday(today, day)
            for entry in entries:
                if entry.faculty:
                    att = attendance.objects.filter(employee=entry.faculty, date=target_date).first()
                    entry.attendance_status = att.status if att else 'Absent'
                else:
                    entry.attendance_status = 'Absent'

            timetable[day] = entries
            for entry in entries:
                time_slots_set.add(entry.time_slot)

    time_slots = sorted(time_slots_set, key=lambda ts: ts.start_time)
    selected_course_name = Course.objects.filter(id=selected_course_id).first()

    log_activity(
        user=request.user,
        action='viewed',
        instance=None,
        message=f"Viewed weekly timetable - Course: {selected_course_name.name if selected_course_name else 'Unknown'} - Semester: {selected_semester_number}"
    )

    return render(request, 'timetable/weekly.html', {
        'program_types': program_types,
        'academic_years': academic_years,
        'courses': courses,
        'semesters': semesters,
        'selected_program_type': selected_program_type,
        'selected_academic_year': selected_academic_year,
        'selected_course_id': selected_course_id,
        'selected_semester_number': selected_semester_number,
        'week_days': week_days,
        'timetable': timetable,
        'time_slots': time_slots,
    })




# def weekly_timetable_view(request, course_id, semester_number):
#     semester = get_object_or_404(Semester, course__id=course_id, number=semester_number)
#     week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
#     timetable = {
#         day: TimetableEntry.objects.filter(semester=semester, day=day).order_by('time_slot')
#         for day in week_days
#     }
#     return render(request, 'timetable/weekly.html', {
#         'timetable': timetable, 'semester': semester
#     })


@custom_login_required
def faculty_timetable_view(request, faculty_id):
    faculty = get_object_or_404(Employee, id=faculty_id)
    entries = TimetableEntry.objects.filter(faculty=faculty).order_by('day', 'time_slot')
    return render(request, 'timetable/faculty.html', {
        'faculty': faculty, 'entries': entries
    })



from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse

from .forms import TimetableEntryForm
from .models import TimetableEntry
from master.models import Semester, Course, Subject, Employee, EmployeeSubjectAssignment
from core.utils import get_logged_in_user, log_activity


@custom_login_required
def timetable_form_add(request):
    if request.method == 'POST':
        form = TimetableEntryForm(request.POST)

        # --- Dynamically populate semester choices ---
        course_id = request.POST.get('course')
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                course_type_name = course.course_type.name.strip().lower()
                semester_list = []

                if course_type_name == "puc regular":
                    total = course.duration_years or 0
                    for i in range(1, total + 1):
                        semester_list.append((str(i), f"{course.name} {i}"))
                else:
                    total = course.total_semesters or 0
                    for i in range(1, total + 1):
                        semester_list.append((str(i), f"{course.name} {i}"))

                if not semester_list:
                    semester_list = [('0', "NOT APPLICABLE")]

                form.fields['semester_number'].choices = semester_list

            except Course.DoesNotExist:
                pass

        # --- Filter subjects based on selected course and semester ---
        semester_number = request.POST.get('semester_number')
        subject_id = request.POST.get('subject')
        if course_id and semester_number:
            subjects = Subject.objects.filter(
                course_id=course_id,
                semester=semester_number
            ).order_by('name')
            form.fields['subject'].queryset = subjects

        # --- Filter faculty based on subject assignment ---
        if course_id and semester_number and subject_id:
            assigned_faculty_qs = EmployeeSubjectAssignment.objects.filter(
                course_id=course_id,
                semester=semester_number,
                subject_id=subject_id
            ).select_related('employee')

            faculty_ids = [a.employee.id for a in assigned_faculty_qs]
            faculty_queryset = Employee.objects.filter(id__in=faculty_ids)

            form.fields['faculty'].queryset = faculty_queryset

            # ✅ Preselect the first faculty if none selected
            if not request.POST.get('faculty') and faculty_queryset.exists():
                form.initial['faculty'] = faculty_queryset.first().id

        # --- Save logic ---
        if form.is_valid():
            cleaned_data = form.cleaned_data
            day = cleaned_data['day']
            time_slot = cleaned_data['time_slot']
            course = cleaned_data['course']
            semester_number = cleaned_data['semester_number']

            existing_entry = TimetableEntry.objects.filter(
                day=day,
                time_slot=time_slot,
                course=course,
                semester_number=semester_number
            ).first()

            if existing_entry:
                existing_entry.subject = cleaned_data['subject']
                existing_entry.faculty = cleaned_data['faculty']
                existing_entry.room = cleaned_data['room']
                existing_entry.save()

                user = get_logged_in_user(request)
                log_activity(
                    user=request.user,
                    action='updated',
                    instance=existing_entry
                )

                messages.success(request, "Existing timetable entry updated successfully.")
            else:
                saved_entry = form.save(commit=False)
                user = get_logged_in_user(request)
                saved_entry.save()
                log_activity(user, 'created', saved_entry)

                messages.success(request, "Timetable entry saved successfully.")

            # ✅ Redirect to weekly timetable for same course and semester, with filters as query params
            course_type_id = course.course_type.id
            batch_id = course.batch.id if hasattr(course, 'batch') else ''

            return redirect(
                f"{reverse('weekly_timetable', kwargs={'course_id': course.id, 'semester_number': semester_number})}"
                f"?course_type={course.course_type.id}&academic_year={(course.batch.id if hasattr(course, 'batch') else '')}"
            )


        else:
            messages.error(request, "Form submission failed. Please correct the highlighted errors.")

    else:
        form = TimetableEntryForm()

    return render(request, 'timetable/add_entry.html', {'form': form})

from django.http import JsonResponse
from .models import Course, AcademicYear

@custom_login_required
def get_courses_and_years_by_program_type(request):
    program_type_id = request.GET.get('program_type_id')

    if not program_type_id:
        return JsonResponse({'courses': [], 'academic_years': []})

    # Get all academic years linked with this CourseType
    academic_years = AcademicYear.objects.filter(
        id__in=Course.objects.filter(course_type_id=program_type_id)
                              .values_list('academic_year_id', flat=True)
                              .distinct()
    ).values('id', 'year')

    # Get all courses for this CourseType
    courses = Course.objects.filter(course_type_id=program_type_id) \
                            .values('id', 'name', 'academic_year_id')

    return JsonResponse({
        'courses': list(courses),
        'academic_years': list(academic_years)
    })



from django.views.decorators.csrf import csrf_exempt

@custom_login_required
@csrf_exempt
def get_subjects_by_course_and_semester(request):
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        semester = str(request.POST.get('semester')).strip()  # 🔁 Ensure string comparison

        print(f"🔵 View called\nCourse ID: {course_id}\nSemester: {semester} (type: {type(semester)})")

        subjects = Subject.objects.filter(course_id=course_id, semester=semester)

        print(f"Subjects found: {subjects}")
        print(f"SQL Query: {subjects.query}")

        subject_data = [{'id': subject.id, 'name': subject.name} for subject in subjects]
        return JsonResponse({'subjects': subject_data})


# from django.http import JsonResponse
# from .models import Subject


from django.http import JsonResponse
from master.models import Subject, EmployeeSubjectAssignment

@custom_login_required
def get_faculty_by_subject(request):
    if request.method != "GET":
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    subject_id = request.GET.get('subject_id')
    if not subject_id:
        return JsonResponse({'error': 'Subject ID is required'}, status=400)

    try:
        assignments = EmployeeSubjectAssignment.objects.filter(subject_id=subject_id).select_related('employee')

        faculty_list = []
        for assignment in assignments:
            employee = assignment.employee
            name_with_role = f"{employee.name} ({employee.role})" if employee.role else employee.name
            faculty_list.append({
                'id': employee.id,
                'name': name_with_role
            })

        default_faculty = assignments.first().employee.id if assignments.exists() else None

        return JsonResponse({
            'faculty': faculty_list,
            'default': default_faculty
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.shortcuts import render
from django.db.models import Count
from timetable.models import TimetableEntry
from master.models import Course
 
 
@custom_login_required
def faculty_classes_table(request):
    courses = Course.objects.all()
    course_param = request.GET.get('course')
    semester_param = request.GET.get('semester')
 
    selected_course_id = int(course_param) if course_param and course_param.isdigit() else None
    selected_semester = int(semester_param) if semester_param and semester_param.isdigit() else None
 
    faculty_subject_class_counts = TimetableEntry.objects.filter(faculty__isnull=False)
 
    semesters = []
    if selected_course_id:
       faculty_subject_class_counts = faculty_subject_class_counts.filter(subject__course__id=selected_course_id)
 
    course = Course.objects.filter(id=selected_course_id).first()
    if course:
        course_type_name = course.course_type.name.strip().lower()
        if "pu" in course_type_name:
            total = course.duration_years or 0
            semesters = [{'number': i, 'name': f'{course.name}  {i}'} for i in range(1, total + 1)]
        else:
            total = course.total_semesters or 0
            semesters = [{'number': i, 'name': f'{course.name}  {i}'} for i in range(1, total + 1)]
 
 
 
    if selected_semester:
        faculty_subject_class_counts = faculty_subject_class_counts.filter(semester_number=selected_semester)
 
    faculty_subject_class_counts = faculty_subject_class_counts.values(
        'faculty__id',
        'faculty__name',
        'subject__id',
        'subject__name',
        'subject__course__name'
    ).annotate(class_count=Count('id')).order_by('faculty__name', 'subject__name')
 
    return render(request, 'timetable/faculty_classes_table.html', {
        'faculty_subject_class_counts': faculty_subject_class_counts,
        'courses': courses,
        'semesters': semesters,
        'selected_course_id': selected_course_id,
        'selected_semester': selected_semester
    })


