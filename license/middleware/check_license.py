#1
# # license/middleware/check_license.py

from django.shortcuts import redirect
from django.urls import reverse

class LicenseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exempt_urls = [
            reverse('login'),
            reverse('logout'),
            reverse('license_check_view'),
            '/admin/',  # Optional: allow Django admin
        ]

        if request.user.is_authenticated:
            license_valid = request.session.get('license_valid', False)
            current_path = request.path

            if not license_valid and not any(current_path.startswith(url) for url in exempt_urls):
                return redirect('license_check_view')

        return self.get_response(request)




#sai 2
# from django.shortcuts import redirect

# from django.urls import reverse
 
# class LicenseCheckMiddleware:

#     def __init__(self, get_response):

#         self.get_response = get_response
 
#     def __call__(self, request):

#         print("🔥 LicenseCheckMiddleware activated - Path:", request.path)
 
#         exempt_paths = [

#             reverse('login'),

#             reverse('logout'),

#             reverse('license_check_view'),

#         ]

#         exempt_prefixes = ['/admin/', '/static/', '/media/']
 
#         if any(request.path.startswith(p) for p in exempt_paths + exempt_prefixes):

#             return self.get_response(request)
 
#         print("🔑 Authenticated:", request.user.is_authenticated)
 
#         if not request.user.is_authenticated:

#             return redirect(reverse('login'))
 
#         license_valid = request.session.get('license_valid', False)

#         print("🔐 License Valid:", license_valid)
 
#         if not license_valid:

#             return redirect(reverse('license_check_view'))
 
#         return self.get_response(request)



 
# from django.shortcuts import redirect
# from django.urls import reverse
# from datetime import date

# START_DATE = date(2025, 4, 1)
# END_DATE = date(2025, 5, 15)

# class LicenseCheckMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         print("🔥 LicenseCheckMiddleware activated - Path:", request.path)

#         exempt_paths = [
#             reverse('login'),
#             reverse('logout'),
#             reverse('license_check_view'),
#             reverse('home'),  # or whatever your main view is called
#         ]
#         exempt_prefixes = ['/admin/', '/static/', '/media/']

#         if any(request.path.startswith(p) for p in exempt_paths + exempt_prefixes):
#             return self.get_response(request)

#         if not request.user.is_authenticated:
#             return redirect(reverse('login'))

#         license_valid = request.session.get('license_valid', False)
#         current_date = date.today()
#         print("🔐 License Valid:", license_valid)

#         if not license_valid or not (START_DATE <= current_date <= END_DATE):
#             return redirect(reverse('license_check_view'))

#         return self.get_response(request)
