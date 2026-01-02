from django.db import models
from django.utils import timezone
from datetime import timedelta

from django.db import models
from django.utils import timezone
from datetime import timedelta

class License(models.Model):
    license_key = models.CharField(max_length=255, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    activated = models.BooleanField(default=False)
    client_name = models.CharField(max_length=255)  # Make sure this field is present

    def is_valid(self):
        from django.utils import timezone
        if not self.start_date or not self.end_date:
            return False
        current_date = timezone.localdate()
        return self.start_date <= current_date <= self.end_date and self.activated

    def is_expiring_soon(self):
        """Check if the license is expiring in the next 7 days."""
        if not self.end_date:
            return False
        return self.end_date <= timezone.localdate() + timedelta(days=7)

    def __str__(self):
        return self.license_key



































# # models.py
# from django.db import models
# from datetime import date
# from datetime import timedelta

# class License(models.Model):
#     license_key = models.CharField(max_length=255, unique=True)
#     start_date = models.DateField()
#     end_date = models.DateField()
#     activated = models.BooleanField(default=False)
#     client_name = models.CharField(max_length=255)  # Make sure this field is present

#     def is_valid(self):
#         """Check if the license is valid."""
#         from django.utils import timezone
#         current_date = timezone.localdate()
#         return self.start_date <= current_date <= self.end_date and self.activated

#     def is_expiring_soon(self):
#         # Check if the license is expiring in the next 7 days
#         return self.end_date <= date.today() + timedelta(days=7)

#     def __str__(self):
#         return self.license_key


