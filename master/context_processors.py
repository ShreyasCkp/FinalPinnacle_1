from django.contrib.auth.models import User as AuthUser
from .models import UserPermission, UserCustom

def user_form_permissions(request):
    user_id = request.session.get('user_id')
    user = None
    if user_id:
        try:
            user = UserCustom.objects.get(id=user_id)
        except UserCustom.DoesNotExist:
            user = None

    if user is None and request.user.is_authenticated:
        user = UserCustom.objects.filter(username=request.user.username).first()

    form_permissions = {}
    is_admin_user = False
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        is_admin_user = True
    elif user:
        auth_user = AuthUser.objects.filter(username=user.username, is_active=True).only(
            'is_staff',
            'is_superuser',
        ).first()
        if auth_user:
            is_admin_user = auth_user.is_staff or auth_user.is_superuser

    if is_admin_user:
        all_forms = [
            'employee_attendance_form', 'pu_admission_form', 'degree_admission_form',
            'schedule_follow_up_form', 'enquiry_form', 'student_attendance_form',
            'academic_year', 'fee_type', 'fee_declaration', 'timetable_form',
            'communication_dashboard', 'calendar_form', 'student_database',
            'employee_form', 'course_type', 'course_form', 'subject_form',
            'transport_form', 'recent_activity_view', 'promotion_history',
            'user_list', 'role_permissions',
        ]

        for form in all_forms:
            form_permissions[form] = {
                'view': True,
                'add': True,
                'edit': True,
                'delete': True,
                'access': True,
            }
    elif user:
        # Load permissions from DB
        permissions = UserPermission.objects.filter(user=user)
        for perm in permissions:
            form_permissions[perm.form_name] = {
                'view': perm.can_view,
                'add': perm.can_add,
                'edit': perm.can_edit,
                'delete': perm.can_delete,
                'access': perm.can_access,
            }

    return {
        'form_permissions': form_permissions,
        'custom_user': user
    }
