# signals.py

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.shortcuts import redirect

# login view or signals.py (for user_logged_in signal)

@receiver(user_logged_in)
def check_license_after_login(sender, request, user, **kwargs):
    if not request.session.get('license_valid', False):
        return redirect('license_check_view')  # Force the user to enter license

