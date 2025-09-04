from functools import wraps
from django.core.exceptions import PermissionDenied
from .models import UserCustom, UserPermission

def role_permission_required(form_name, action='view'):
    """
    Decorator to enforce user permission on views without redirect.
    Raises 403 if permission is not granted.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_id = request.session.get('user_id')
            if not user_id:
                raise PermissionDenied("Login required.")

            try:
                user = UserCustom.objects.get(id=user_id)
            except UserCustom.DoesNotExist:
                raise PermissionDenied("Invalid user.")

            # Allow full access to admins
            if user.username.lower() in ['naveen', 'ambreesh']:
                return view_func(request, *args, **kwargs)

            try:
                perm = UserPermission.objects.get(user=user, form_name=form_name)
                if getattr(perm, f'can_{action}', False):
                    return view_func(request, *args, **kwargs)
            except UserPermission.DoesNotExist:
                pass

            raise PermissionDenied("Access denied.")

        return _wrapped_view
    return decorator
from functools import wraps
from django.shortcuts import redirect
 
def custom_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')  # Use the URL name of your login view
        return view_func(request, *args, **kwargs)
    return _wrapped_view