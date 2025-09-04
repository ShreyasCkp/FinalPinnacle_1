from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from .forms import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone

# 1. MasterTransport Views

def master_transport_list(request):
    transports = MasterTransport.objects.all()
    return render(request, 'transport/master_transport_list.html', {'transports': transports})

def master_transport_create(request):
    form = MasterTransportForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('master_transport_list')
    return render(request, 'transport/form.html', {'form': form, 'title': 'Add Vehicle'})

def master_transport_edit(request, pk):
    transport = get_object_or_404(MasterTransport, pk=pk)
    form = MasterTransportForm(request.POST or None, instance=transport)
    if form.is_valid():
        form.save()
        return redirect('master_transport_list')
    return render(request, 'transport/form.html', {'form': form, 'title': 'Edit Vehicle'})


# 2. TransportRoute Views

def route_list(request):
    routes = TransportRoute.objects.all()
    return render(request, 'transport/route_list.html', {'routes': routes})

def route_create(request):
    form = TransportRouteForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('route_list')
    return render(request, 'transport/form.html', {'form': form, 'title': 'Add Route'})

def route_edit(request, pk):
    route = get_object_or_404(TransportRoute, pk=pk)
    form = TransportRouteForm(request.POST or None, instance=route)
    if form.is_valid():
        form.save()
        return redirect('route_list')
    return render(request, 'transport/form.html', {'form': form, 'title': 'Edit Route'})


# 3. TransportStop Views

def stop_list(request):
    stops = TransportStop.objects.select_related('route').order_by('route', 'stop_order')
    return render(request, 'transport/stop_list.html', {'stops': stops})

def stop_create(request):
    form = TransportStopForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('stop_list')
    return render(request, 'transport/form.html', {'form': form, 'title': 'Add Stop'})

def stop_edit(request, pk):
    stop = get_object_or_404(TransportStop, pk=pk)
    form = TransportStopForm(request.POST or None, instance=stop)
    if form.is_valid():
        form.save()
        return redirect('stop_list')
    return render(request, 'transport/form.html', {'form': form, 'title': 'Edit Stop'})


# 4. StudentTransportMapping Views

def mapping_list(request):
    mappings = StudentTransportMapping.objects.select_related('student', 'transport', 'pickup_stop', 'drop_stop')
    return render(request, 'transport/mapping_list.html', {'mappings': mappings})

def mapping_create(request):
    form = StudentTransportMappingForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('mapping_list')
    return render(request, 'transport/form.html', {'form': form, 'title': 'Assign Transport to Student'})

def mapping_edit(request, pk):
    mapping = get_object_or_404(StudentTransportMapping, pk=pk)
    form = StudentTransportMappingForm(request.POST or None, instance=mapping)
    if form.is_valid():
        form.save()
        return redirect('mapping_list')
    return render(request, 'transport/form.html', {'form': form, 'title': 'Edit Student Transport Assignment'})


# 5. StopArrivalLog - Read Only

def arrival_logs(request):
    logs = StopArrivalLog.objects.select_related('student', 'stop').order_by('-reached_at')
    return render(request, 'transport/arrival_logs.html', {'logs': logs})


# 6. API: Receive GPS from Driver App

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import DriverTrackingLocation
from .utils import check_and_log_arrival_for_stop  # Make sure utils.py exists

@csrf_exempt
def update_location_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            transport_id = data.get("transport_id")
            lat = data.get("latitude")
            lng = data.get("longitude")

            if not (transport_id and lat and lng):
                return JsonResponse({"status": "error", "message": "Missing data"}, status=400)

            # Save location
            DriverTrackingLocation.objects.create(
                transport_id=transport_id,
                latitude=lat,
                longitude=lng
            )

            # Check if near stop
            check_and_log_arrival_for_stop(transport_id, lat, lng)

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)





from .utils import check_and_log_arrival_for_stop , estimate_time_minutes
from django.contrib import messages

def simulate_bus_location(request):
    transports = MasterTransport.objects.all()
    if request.method == "POST":
        transport_id = request.POST.get("transport_id")
        lat = request.POST.get("latitude")
        lng = request.POST.get("longitude")

        check_and_log_arrival_for_stop(transport_id, lat, lng)
        messages.success(request, "Tracking simulated and stop check triggered.")
        return redirect('simulate_tracking')

    return render(request, 'transport/simulate_tracking.html', {'transports': transports})
    


def get_latest_bus_locations(request):
    data = []
    for transport in MasterTransport.objects.all():
        latest = DriverTrackingLocation.objects.filter(transport=transport).order_by('-timestamp').first()
        if latest:
            data.append({
                'vehicle_no': transport.vehicle_no,
                'lat': float(latest.latitude),
                'lng': float(latest.longitude),
                'timestamp': latest.timestamp,
                'route': transport.route_name,
            })
    return JsonResponse(data, safe=False)




def parent_tracking_view(request, student_id):
    student = get_object_or_404(ConfirmedAdmission, pk=student_id)
    mapping = StudentTransportMapping.objects.get(student=student)
    transport = mapping.transport
    latest = DriverTrackingLocation.objects.filter(transport=transport).order_by('-timestamp').first()

    next_stop = mapping.pickup_stop  # or drop_stop if evening
    eta = estimate_time_minutes(
        float(latest.latitude), float(latest.longitude),
        float(next_stop.latitude), float(next_stop.longitude)
    )

    return render(request, 'transport/parent_tracking.html', {
        'student': student,
        'bus_location': latest,
        'stop': next_stop,
        'eta': eta
    })



def transport_home(request):
    return render(request, 'transport/transport_home.html')
