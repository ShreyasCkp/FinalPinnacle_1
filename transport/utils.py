import math
from django.utils import timezone
from datetime import timedelta
from .models import TransportStop, StudentTransportMapping, StopArrivalLog, MasterTransport

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c
from geopy.distance import geodesic
from datetime import datetime
from .models import StudentTransportMapping, TransportStop, StopArrivalLog

def check_and_log_arrival_for_stop(transport_id, lat, lng):
    try:
        mappings = StudentTransportMapping.objects.filter(transport_id=transport_id)
        for mapping in mappings:
            stops = [mapping.pickup_stop, mapping.drop_stop]

            for stop in stops:
                stop_coords = (float(stop.latitude), float(stop.longitude))
                bus_coords = (float(lat), float(lng))
                distance = geodesic(stop_coords, bus_coords).meters

                if distance <= 50:  # within 50 meters
                    already_logged = StopArrivalLog.objects.filter(
                        student=mapping.student,
                        stop=stop,
                        reached_at__date=datetime.now().date()
                    ).exists()

                    if not already_logged:
                        StopArrivalLog.objects.create(
                            student=mapping.student,
                            stop=stop,
                            message_sent=False
                        )
                        print(f"[INFO] Reached {stop.stop_name} for {mapping.student}")
    except Exception as e:
        print(f"[ERROR] in check_and_log_arrival_for_stop: {str(e)}")






from geopy.distance import geodesic
import math

def estimate_time_minutes(lat1, lng1, lat2, lng2, speed_kmph=30):
    distance_km = geodesic((lat1, lng1), (lat2, lng2)).km
    if speed_kmph == 0:
        return 0
    time_min = (distance_km / speed_kmph) * 60
    return round(time_min, 2)





