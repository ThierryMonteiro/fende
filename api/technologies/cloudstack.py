from django.contrib import messages
from django.contrib.auth.decorators import login_required

from marketplace.views import define_infra
from repository.models import Infrastructure, SFC, Instance
from vnfm.cloudstack_manager import *
import time

"""
    SFC Functions
"""
@login_required
def sfc_soft_restart(request):
    """Soft restarts a SFC.
    A soft restart will restart all VNF functions in the chain, but not the SFC itself.
    """
    if request.method == "POST":
        cloudstack_manager= CloudstackManager()
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]
        vnf_ids = sfc.vnf_ids.split(',')

        # restart all VNF functions from the chain
        for vnf_id in vnf_ids:
            vnf = Instance.objects.get(vnf_id=vnf_id)
            infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
            infra_info = define_infra(infra)
            response = cloudstack_manager.vnf_restart(vnf_id, infra_info)

            if response['status'] != 'OK':
                # error_reason
                return response

        sfc.stop_type = ''
        sfc.save()
        return {'status': 200, 'text': 'SFC %s successfully restarted.' % vnffg_id}

@login_required
def sfc_soft_stop(request):
    """Soft stops a SFC.
    A soft stop will stop all VNF functions in the chain, but not the SFC itself.
    """
    if request.method == "POST":
        cloudstack_manager= CloudstackManager()
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]
        vnf_ids = sfc.vnf_ids.split(',')

        # stop all VNF functions from the chain
        for vnf_id in vnf_ids:
            vnf = Instance.objects.get(vnf_id=vnf_id)
            infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
            infra_info = define_infra(infra)
            response = cloudstack_manager.vnf_stop(vnf_id, infra_info)

            if response['status'] != 'OK':
                # error_reason
                return response

        sfc.stop_type = ''
        sfc.save()
        return {'status': 200, 'text': 'SFC %s successfully stoped.' % vnffg_id}

@login_required
def sfc_start(request):
    """Start a SFC.
    """
    if request.method == "POST":
        cloudstack_manager= CloudstackManager()
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]
        vnf_ids = sfc.vnf_ids.split(',')

        # start all VNF functions from the chain
        for vnf_id in vnf_ids:
            vnf = Instance.objects.get(vnf_id=vnf_id)
            infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
            infra_info = define_infra(infra)
            response = cloudstack_manager._vnf_vm_start(vnf_id, infra_info)

            if response['status'] != 'OK':
                # error_reason
                return response

        sfc.stop_type = ''
        sfc.save()
        time.sleep(1)
        response = sfc_soft_restart(request)
        if response['status']!=200:
            return response
        return {'status': 200, 'text': 'SFC %s successfully started.' % vnffg_id}


@login_required
def sfc_stop(request):
    """Stops a SFC.
    Stop all VNF functions in the chain.
    """
    if request.method == "POST":
        cloudstack_manager= CloudstackManager()
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]
        vnf_ids = sfc.vnf_ids.split(',')

        # stop all VNF functions from the chain
        for vnf_id in vnf_ids:
            vnf = Instance.objects.get(vnf_id=vnf_id)
            infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
            infra_info = define_infra(infra)
            response = cloudstack_manager._vnf_vm_stop(vnf_id, infra_info)

            if response['status'] != 'OK':
                # error_reason
                return response

        sfc.stop_type = ''
        sfc.save()
        return {'status': 200, 'text': "SFC %s chain successfully stopped." % vnffg_id}


@login_required
def sfc_restart(request):
    """Restart a SFC.
    Restart all VNF functions (and VMs) in the chain.
    """
    response = sfc_soft_stop(request) # stops all functions to speed up next step
    if response['status'] == 'OK':
        if request.method == "POST":
            cloudstack_manager= CloudstackManager()
            vnffg_id = request.POST.get('vnffg_id')
            sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]
            vnf_ids = sfc.vnf_ids.split(',')

            # stop all VNF functions from the chain
            for vnf_id in vnf_ids:
                vnf = Instance.objects.get(vnf_id=vnf_id)
                infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
                infra_info = define_infra(infra)
                response = cloudstack_manager._vnf_vm_restart(vnf_id, infra_info)

                if response['status'] != 'OK':
                    # error_reason
                    return response

            sfc.stop_type = ''
            sfc.save()
            time.sleep(5)
            return sfc_soft_restart(request)
    else:
        return {'status': 200, 'text': 'SFC %s successfully restarted.' % vnffg_id}


@login_required
def sfc_delete(request):
    """Delete a SFC.
    Delete all VNF functions (and VMs) in the chain.
    """
    if request.method == "POST":
        cloudstack_manager= CloudstackManager()
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]
        vnf_ids = sfc.vnf_ids.split(',')

        # deletes all VMs of VNFs from the chain
        for vnf_id in vnf_ids:
            vnf = Instance.objects.get(vnf_id=vnf_id)
            infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
            infra_info = define_infra(infra)
            response = cloudstack_manager.vnf_delete(vnf_id, infra_info)

            if response['status'] != 'OK':
                return response # error_reason
            vnf.delete()
        sfc.delete() # deletes SFC registry
        return {'status': 200, 'text': "SFC %s chain successfully deleted." % vnffg_id}



"""
    VFN Functions
"""
@login_required
def vnf_restart(request):
    """Restart a VNF."""

    if request.method == "POST":
        cloudstack_manager= CloudstackManager()
        vnf_id = request.POST.get('vnf_id')
        vnf = Instance.objects.get(vnf_id=vnf_id)
        infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
        infra_info = define_infra(infra)
        response = cloudstack_manager.vnf_restart(vnf_id, infra_info)

        if response['status'] != 'OK':
            error_reason = "Error while restarting VNF: " + response['error_reason']
            return {'status': 500, 'text': error_reason}

        return {'status': 200, 'text': "VNF function successfully restarted."}



@login_required
def vnf_stop(request):
    """Stop a VNF."""

    if request.method == "POST":
        cloudstack_manager= CloudstackManager()
        vnf_id = request.POST.get('vnf_id')
        vnf = Instance.objects.get(vnf_id=vnf_id)
        infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
        infra_info = define_infra(infra)
        response = cloudstack_manager.vnf_stop(vnf_id, infra_info)

        if response['status'] != 'OK':
            error_reason = "Error while stopping VNF: " + response['error_reason']
            return {'status': 500, 'text': error_reason}

        return {'status': 200, 'text': "VNF function successfully stopped."}




"""
    Actions Request
"""
def service(request):
    action = request.POST['action']

    if action == 'soft_restart':
        return sfc_soft_restart(request)

    elif action == 'full_restart':
        return sfc_restart(request)

    elif action == 'soft_stop':
        return sfc_soft_stop(request)

    elif action == 'full_stop':
        return sfc_stop(request)

    elif action == 'start':
        return sfc_start(request)

    elif action == 'update':
        return {'status': 404, 'text': "Not implemented."}

    elif action == 'delete_sfc':
        return sfc_delete(request)

    return {'status': 500}


def function(request):
    action = request.POST['action']

    if action == 'restart_vnf':
        return vnf_restart(request)

    elif action == 'stop_vnf':
        return vnf_stop(request)

    elif action == 'update':
        return {'status': 404, 'text': "Not implemented."}

    elif action == 'resize_allocation':
        return {'status': 404, 'text': "Not implemented."}

    return {'status': 500}
