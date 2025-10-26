from django.shortcuts import render
from datetime import datetime, date
import logging
from master.decorators import custom_login_required

logger = logging.getLogger(__name__)

@custom_login_required
def home_view(request):
    license_end_date = request.session.get('license_end_date')
    is_expiring_soon = False
    license_expiring = False  # For modal

    if license_end_date:
        try:
            # Try multiple date formats
            try:
                end_date = datetime.strptime(license_end_date, "%B %d, %Y").date()
            except ValueError:
                end_date = datetime.strptime(license_end_date, "%Y-%m-%d").date()
            today = date.today()
            delta = (end_date - today).days

            # Expiring soon if license expires within the next 7 days (including today)
            is_expiring_soon = 0 <= delta <= 7
            license_expiring = is_expiring_soon
        except Exception as e:
            logger.warning(f"Invalid license_end_date: {license_end_date} ({e})")
            is_expiring_soon = False
            license_expiring = False
    else:
        is_expiring_soon = False
        license_expiring = False

    context = {
        'license_end_date': license_end_date,
        'is_expiring_soon': is_expiring_soon,
        'license_expiring': license_expiring,
    }

    return render(request, 'license/home.html', context)

@custom_login_required
def activate_license(request):
    if request.method == 'POST':
        license_key = request.POST['license_key']
        license = License.objects.filter(license_key=license_key).first()

        if license:
            print(f"License found: {license}")  # Debugging line
            license.activated = True
            try:
                license.save()
                print(f"License activated: {license}")  # Debugging line
            except Exception as e:
                print(f"Error saving license: {e}")  # If there are any errors while saving

            request.session['license_key'] = license_key
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid License Key.")
            return redirect('license_check_view')


# views.py




@custom_login_required
def license_terms_view(request):
    return render(request, 'license/license_terms.html')

@custom_login_required
def privacy_policy_view(request):
    return render(request, 'license/privacy_policy.html')

@custom_login_required
def terms_and_conditions_view(request):
    return render(request, 'license/terms_and_conditions.html')

@custom_login_required
def create_license_view(request):
    if request.method == 'POST':
        license = License.objects.create(
            license_key='CKP-2025 v1.0.0',
            start_date=date(2025, 6, 5),
            end_date=date(2025, 11, 27),
            activated=True,  # Make sure this is set to True for testing
            client_name="Naveen"
        )
        return HttpResponse(f"License created: {license.license_key}")
    return render(request, 'license/create_license.html')



# In views.py
@custom_login_required
def license_check(request):
    return render(request, 'license/license_check_view.html')

from datetime import datetime, time
from django.utils import timezone

@custom_login_required
def __call__(self, request):
    license = get_license()  # however you're loading it
    if license and license.end_date:
        # Convert date to timezone-aware datetime
        license_end_datetime = datetime.combine(
            license.end_date,
            time.min,
            tzinfo=timezone.get_current_timezone()
        )

        # Now you can safely compare
        if timezone.now() > license_end_datetime:
            return redirect('license_expired')


from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import License

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from datetime import timedelta, datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from license.models import License  # adjust this based on your License model path

@custom_login_required
@user_passes_test(lambda u: u.is_superuser)  # Only allow admins to access this view
def extend_license_view(request, license_id):
    license = get_object_or_404(License, id=license_id)

    if request.method == 'POST':
        extension_days = int(request.POST['extension_days'])
        new_start_date = request.POST['new_start_date']
        new_end_date = request.POST['new_end_date']

        # Extend the license
        license.end_date = new_end_date
        license.start_date = new_start_date
        license.save()

        return redirect('dashboard')  # Redirect back to the dashboard after extension

    return render(request, 'license/extend_license.html', {'license': license})



from datetime import date, timedelta

@custom_login_required
def check_license_expiry(request):
    # Assuming the license is associated with the user
    license = License.objects.filter(client_name=request.user.username).first()

    if license:
        if license.is_expiring_soon():
            request.session['license_expiring'] = True
        else:
            request.session['license_expiring'] = False
    return render(request, 'home.html')

@custom_login_required
def is_valid(self):
    from django.utils import timezone
    current_date = timezone.localdate()
    return self.start_date <= current_date <= self.end_date and self.activated






# from datetime import date
from datetime import date
from django.shortcuts import redirect, render
from .forms import LicenseForm  # assuming your form is defined

from django.shortcuts import redirect, render
from .forms import LicenseForm
 
from datetime import date
 
HARDCODED_KEY = "CKP-2025 v1.0.0"
START_DATE = date(2025, 6, 5)
END_DATE = date(2025, 11, 27)
 
@custom_login_required
def license_check_view(request):
    current_date = date.today()
 
    if request.session.get('license_valid') and START_DATE <= current_date <= END_DATE:
        # Make sure to store the expiry date string in session if not already
        if 'license_end_date' not in request.session:
            request.session['license_end_date'] = END_DATE.strftime("%B %d, %Y")
        return redirect('home')
 
    error_message = None
 
    if request.method == 'POST':
        form = LicenseForm(request.POST)
        if form.is_valid():
            license_key = form.cleaned_data['license_key']
 
            if license_key == HARDCODED_KEY:
                if START_DATE <= current_date <= END_DATE:
                    request.session['license_valid'] = True
                    # Store expiry date in session for later use
                    request.session['license_end_date'] = END_DATE.strftime("%B %d, %Y")
                    return redirect('home')
                else:
                    error_message = 'License expired. Please contact support.'
            else:
                error_message = 'Invalid license key.'
        else:
            error_message = 'Invalid form submission.'
    else:
        form = LicenseForm()
 
    return render(request, 'license/license_check.html', {'form': form, 'error': error_message})

# def license_check_view(request):
#     error_message = None
#     HARDCODED_KEY = "CKP-RAJ-1902"
#     START_DATE = date(2025, 4, 1)
#     END_DATE = date(2025, 5, 18)

#     if request.method == 'POST':
#         form = LicenseForm(request.POST)
#         if form.is_valid():
#             license_key = form.cleaned_data['license_key']
#             current_date = date.today()

#             if license_key == HARDCODED_KEY:
#                 if START_DATE <= current_date <= END_DATE:
#                     request.session['license_valid'] = True
#                     return redirect('home')
#                 else:
#                     error_message = 'License expired. Please contact support.'
#             else:
#                 error_message = 'Invalid license key.'
#         else:
#             error_message = 'Invalid form submission.'
#     else:
#         form = LicenseForm()

#     return render(request, 'license/license_check.html', {'form': form, 'error': error_message})