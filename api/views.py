from django.http import JsonResponse
from django.utils import timezone

from api.technologies import cloudstack, kubernetes, libvirt, openstack
import json
from django.core.serializers.json import DjangoJSONEncoder

# Create your views here.
from repository.models import Infrastructure, Instance, SFC, SFCStatus, Status


def service(request):
    response = {'status': 500}
    # GET INFRA
    if request.method == 'POST':
        infra = Infrastructure.objects.get(name=request.POST['infra'])
        if infra.technology == 'openstack':
            response = openstack.service(request)
        if infra.technology == 'cloudstack':
            response = cloudstack.service(request)
        if infra.technology == 'kubernetes':
            response = kubernetes.service(request)
        if infra.technology == 'libvirt':
            response = libvirt.service(request)

    if request.is_ajax():
        return JsonResponse(response, status=200)
    return response


def function(request):
    response = {'status': 500}
    # GET INFRA
    if request.method == 'POST':
        infra = Infrastructure.objects.get(name=request.POST['infra'])
        if infra.technology == 'openstack':
            response = openstack.function(request)
        if infra.technology == 'cloudstack':
            response = cloudstack.function(request)
        if infra.technology == 'kubernetes':
            response = kubernetes.function(request)
        if infra.technology == 'libvirt':
            response = libvirt.function(request)

    if request.is_ajax():
        return JsonResponse(response, status=200)
    return response


def service_logs(request, id):
    try:
        sfc = SFCStatus.objects.get(id=id)
        logs = Status.objects.filter(sfcstatus=sfc).values('message', 'created_date')
    except SFCStatus.DoesNotExist:
        return None

    logs_list = list(logs)  # important: convert the QuerySet to a list object
    return JsonResponse(logs_list, safe=False)


def service_status(request, id):
    try:
        sfc = SFCStatus.objects.get(id=id)
        try:
            status = Status.objects.latest('created_date')
        except Status.DoesNotExist:
            status = Status.objects.create(sfcstatus=sfc, message='No logs registered')
    except SFCStatus.DoesNotExist:
        sfc = SFCStatus.objects.create(id=id)
        status = Status.objects.create(sfc=sfc)

    data = {
        'name': sfc.name,
        'client': sfc.client.username,
        'status': status.message,
        'error': status.error,
        'step': sfc.step,
        'created_date': timezone.localtime(sfc.created_date).strftime("%b. %d %Y %I:%M %p"),
        'last_update': timezone.localtime(status.created_date).strftime("%b. %d %Y %I:%M %p")
    }
    return JsonResponse(data, status=200)
