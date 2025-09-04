from .models import UserPermission, UserCustom

def user_form_permissions(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return {
            'custom_user': None,
            'form_permissions': {}
        }

    try:
        user = UserCustom.objects.get(id=user_id)
    except UserCustom.DoesNotExist:
        return {
            'custom_user': None,
            'form_permissions': {}
        }

    # Check if the user should have full access
    is_super = user.id == 1 or user.username.lower() == 'dean'

    form_permissions = {}

    if is_super:
        # Grant full access to all known forms
        all_forms = [
           'employee_attendance_form','pu_admission_form','degree_admission_form','schedule_follow_up_form','enquiry_form','student_attendance_form','academic_year','fee_type','fee_declaration','timetable_form','communication_dashboard','calendar_form','student_database','employee_form','course_type','course_form','subject_form','transport_form','recent_activity_view','promotion_history']

        for form in all_forms:
            form_permissions[form] = {
                'view': True,
                'add': True,
                'edit': True,
                'delete': True,
                 'access': True, 
            }
    else:
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
