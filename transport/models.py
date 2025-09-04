from django.db import models
from admission.models import ConfirmedAdmission  # or your actual student model

class MasterTransport(models.Model):
    vehicle_no = models.CharField(max_length=20)
    driver_name = models.CharField(max_length=100)
    driver_phone = models.CharField(max_length=15)
    route_name = models.CharField(max_length=100)
    total_seats = models.IntegerField()
    available_seats = models.IntegerField()
    vehicle_type = models.CharField(max_length=50)
    active = models.BooleanField(default=True)


    def __str__(self):
        return self.vehicle_no

    class Meta:
        managed = False
        db_table = 'master_transport'  # exact name in your MySQL database


class TransportRoute(models.Model):
    route_name = models.CharField(max_length=100)
    total_stops = models.IntegerField()
    distance_km = models.DecimalField(max_digits=5, decimal_places=2)
    estimated_time = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.route_name

    class Meta:
        managed = False
        db_table = 'transport_route'


class TransportStop(models.Model):
    route = models.ForeignKey(TransportRoute, on_delete=models.CASCADE)
    stop_name = models.CharField(max_length=100)
    stop_order = models.IntegerField()
    pickup_time = models.TimeField()
    drop_time = models.TimeField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return f"{self.stop_name} ({self.route.route_name})"

    class Meta:
        managed = False
        db_table = 'transport_stop'


class StudentTransportMapping(models.Model):
    student = models.ForeignKey(ConfirmedAdmission, on_delete=models.CASCADE)
    academic_year_id = models.IntegerField()
    transport = models.ForeignKey(MasterTransport, on_delete=models.CASCADE)
    pickup_stop = models.ForeignKey(TransportStop, on_delete=models.CASCADE, related_name='pickup_stop')
    drop_stop = models.ForeignKey(TransportStop, on_delete=models.CASCADE, related_name='drop_stop')
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2)
    assigned_on = models.DateField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'student_transport_mapping'


class DriverTrackingLocation(models.Model):
    transport = models.ForeignKey(MasterTransport, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'driver_tracking_location'


class StopArrivalLog(models.Model):
    student = models.ForeignKey(ConfirmedAdmission, on_delete=models.CASCADE)
    stop = models.ForeignKey(TransportStop, on_delete=models.CASCADE)
    reached_at = models.DateTimeField(auto_now_add=True)
    message_sent = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'stop_arrival_logs'


class TransportFeeStructure(models.Model):
    stop = models.ForeignKey(TransportStop, on_delete=models.CASCADE)
    academic_year_id = models.IntegerField()
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'transport_fee_structure'
