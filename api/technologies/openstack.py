import json
import requests

from django.contrib.auth.decorators import login_required

from marketplace.views import define_infra, sfc_compose
from marketplace.utils import get_name_id
from repository.models import Infrastructure, SFC, Instance, Catalog
from vnfm.manager import Manager

server = "http://localhost:5000"
user = "f&=gAt&ejuTHuqUKafaKe=2*"
token = "bUpAnebeC$ac@4asaph#DrEb"
auth = (user, token)


@login_required
def sfc_soft_restart(request):
    """Soft restarts a SFC.
    A soft restart will restart all VNF functions in the chain, but not the SFC itself.
    """

    if request.method == "POST":
        manager = Manager()
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]
        vnf_ids = sfc.vnf_ids.split(',')

        # restart all VNF functions from the chain
        for vnf_id in vnf_ids:
            vnf = Instance.objects.get(vnf_id=vnf_id)
            infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
            infra_info = define_infra(infra)
            response = manager.vnf_restart(vnf_id, infra=infra_info)

            if response['status'] != 'OK':
                error_reason = "VNF " + vnf_id + " could not be restarted: " + response['error_reason']
                return {'status': 500, 'text': error_reason}

        sfc.stop_type = ''
        sfc.save()

        return {'status': 200, 'text': 'SFC %s successfully restarted.' % vnffg_id}


@login_required
def sfc_full_restart(request):
    """Fully restarts a SFC.
    A full restart will remove all SFC components (VNFFG, VNFFGD, chains) and will redo the SFC.
    """

    if request.method == "POST":
        manager = Manager()
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]

        infra = Infrastructure.objects.filter(name=sfc.infrastructure)[0]
        infra_info = define_infra(infra)

        if sfc.stop_type != '':
            error_reason = "SFC is currently stopped and can be started using the Start option."
            return {'status': 500, 'text': error_reason}

        # request VNFM to delete VNFFG and VNFFGD
        response = manager.sfc_delete(sfc.vnffg_id, sfc.vnffgd_id, sfc.vnf_ids, infra=infra_info)

        if response['status'] != 'OK':
            error_reason = "Error while deleting SFC: " + response['error_reason']
            return {'status': 500, 'text': error_reason}

        # delete all VNFs from SFC
        vnf_ids = sfc.vnf_ids.split(',')
        for vnf_id in vnf_ids:
            vnf = Instance.objects.filter(vnf_id=vnf_id)[0]
            delete(vnf_id, vnf.vnfd_id)

        # get high-level descriptor
        raw_data = sfc.vnffgd
        vnffgd = raw_data.replace("'", "\"")
        vnffgd = vnffgd.replace('u\"', '\"')
        vnffgd = json.loads(vnffgd)

        # start all SFC components
        response = sfc_compose(request.user, vnffgd)

        if response['status'] != 'OK':
            error_reason = "Error while creating SFC: " + response['error_reason']
            return {'status': 500, 'text': error_reason}

        # update SFC entry
        sfc.vnffgd_id = response['vnffgd_id']
        sfc.vnffg_id = response['vnffg_id']
        sfc.name = response['sfc_name']
        sfc.vnf_ids = response['vnf_ids']
        sfc.vnfds = response['vnfds']
        sfc.save()

        return {'status': 200, 'text': 'SFC %s successfully restarted.' % vnffg_id}


@login_required
def sfc_soft_stop(request):
    """Soft stop a SFC.
    A soft stop will stop all VNF functions in the chain, but not the SFC itself.
    """

    if request.method == "POST":
        manager = Manager()
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]

        if sfc.stop_type != '':
            error_reason = "SFC is already stopped."
            return {'status': 500, 'text': error_reason}

        vnf_ids = sfc.vnf_ids.split(',')

        # stop all VNF functions from the chain
        for vnf_id in vnf_ids:
            vnf = Instance.objects.get(vnf_id=vnf_id)
            infra = Infrastructure.objects.get(name=vnf.infrastructure)
            infra_info = define_infra(infra)
            response = manager.vnf_stop(vnf_id, infra=infra_info)

            if response['status'] != 'OK':
                error_reason = "Error while stopping SFC: " + response['error_reason']
                return {'status': 500, 'text': error_reason}

        sfc.stop_type = 'soft'
        sfc.save()

        return {'status': 200, 'text': "SFC %s chain successfully stopped." % vnffg_id}


@login_required
def sfc_full_stop(request):
    """Fully stop a SFC.
    A full stop will stop all SFC components, but will not start automatically.
    """

    if request.method == "POST":
        manager = Manager()
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]

        infra = Infrastructure.objects.filter(name=sfc.infrastructure)[0]
        infra_info = define_infra(infra)

        if sfc.stop_type != '':
            error_reason = "SFC is already stopped."
            return {'status': 500, 'text': error_reason}

        # request to VNFM to delete VNFFG and VNFFGD
        response = manager.sfc_delete(sfc.vnffg_id, sfc.vnffgd_id, sfc.vnf_ids, infra=infra_info)

        if response['status'] != 'OK':
            error_reason = "Error while stopping SFC: " + response['error_reason']
            return {'status': 500, 'text': error_reason}

        # delete all VNFs from SFC
        vnf_ids = sfc.vnf_ids.split(',')
        for vnf_id in vnf_ids:
            vnf = Instance.objects.filter(vnf_id=vnf_id)[0]
            delete(vnf_id, vnf.vnfd_id)

        sfc.stop_type = 'full'
        sfc.vnffgd_id = 'None'
        sfc.vnffg_id = 'None'
        sfc.save()

        return {'status': 200, 'text': "SFC %s successfully stopped." % vnffg_id}


@login_required
def sfc_start(request):
    """Start a SFC."""

    if request.method == "POST":
        manager = Manager()
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]

        if sfc.stop_type == 'soft':
            # just need to start VNF functions
            vnf_ids = sfc.vnf_ids.split(',')

            for vnf_id in vnf_ids:
                vnf = Instance.objects.get(vnf_id=vnf_id)
                infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
                infra_info = define_infra(infra)
                response = manager.vnf_function_start(vnf_id, vnf.vnf_ip, infra=infra_info)

                if response['status'] != 'OK':
                    error_reason = "Error while starting SFC: " + response['error_reason']
                    return {'status': 500, 'text': error_reason}

        elif sfc.stop_type == 'full':
            # get high-level descriptor
            raw_data = sfc.vnffgd
            vnffgd = raw_data.replace("'", "\"")
            vnffgd = vnffgd.replace('u\"', '\"')
            vnffgd = json.loads(vnffgd)

            # start all SFC components
            response = sfc_compose(request.user, vnffgd)

            if response['status'] != 'OK':
                error_reason = "Error while creating SFC: " + response['error_reason']
                return {'status': 500, 'text': error_reason}

            # update SFC entry
            sfc.vnffgd_id = response['vnffgd_id']
            sfc.vnffg_id = response['vnffg_id']
            sfc.name = response['sfc_name']
            sfc.vnf_ids = response['vnf_ids']
            sfc.vnfds = response['vnfds']

        else:
            error_reason = "SFC is already started."
            return {'status': 500, 'text': error_reason}

        sfc.stop_type = ''
        sfc.save()

        return {'status': 200, 'text': "SFC %s successfully started." % vnffg_id}


@login_required
def sfc_update(request):
    """Update SFC's chain and ACL."""

    if request.method == "POST":
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]

        vnf_ids = sfc.vnf_ids.split(',')
        for vnf_id in vnf_ids:
            response = vnf_update(vnf_id)

            if response['status'] != 'OK':
                error_reason = "Error while updating SFC. VNF %s could not be updated. %s" % (
                vnf_id, response['error_reason'])
                return {'status': 500, 'text': error_reason}

        return {'status': 200, 'text': "SFC %s successfully updated." % vnffg_id}


@login_required
def sfc_delete(request):
    """Delete a instantiated SFC."""

    if request.method == "POST":
        manager = Manager()
        vnffg_id = request.POST.get('vnffg_id')
        sfc = SFC.objects.filter(vnffg_id=vnffg_id)[0]

        infra = Infrastructure.objects.filter(name=sfc.infrastructure)[0]
        infra_info = define_infra(infra)

        # request to VNFM to delete VNFFG and VNFFGD
        response = manager.sfc_delete(sfc.vnffg_id, sfc.vnffgd_id, sfc.vnf_ids, infra=infra_info)

        if response['status'] != 'OK':
            error_reason = "Error while deleting SFC: " + response['error_reason']
            return {'status': 500, 'text': error_reason}

        # delete all VNFs from SFC
        vnf_ids = sfc.vnf_ids.split(',')
        for vnf_id in vnf_ids:
            vnf = Instance.objects.filter(vnf_id=vnf_id)[0]
            delete(vnf_id, vnf.vnfd_id)

        sfc.delete()

        return {'status': 200, 'text': "SFC %s successfully deleted." % vnffg_id}


@login_required
def vnf_restart(request):
    """Restart a VNF."""

    if request.method == "POST":
        manager = Manager()
        vnf_id = request.POST.get('vnf_id')
        vnf = Instance.objects.get(vnf_id=vnf_id)
        infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
        infra_info = define_infra(infra)
        response = manager.vnf_restart(vnf_id, infra=infra_info)

        if response['status'] != 'OK':
            error_reason = "Error while restarting VNF: " + response['error_reason']
            return {'status': 500, 'text': error_reason}

        return {'status': 200, 'text': "VNF function successfully restarted."}


@login_required
def vnf_stop(request):
    """Stop a VNF."""

    if request.method == "POST":
        manager = Manager()
        vnf_id = request.POST.get('vnf_id')
        vnf = Instance.objects.get(vnf_id=vnf_id)
        infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
        infra_info = define_infra(infra)
        response = manager.vnf_stop(vnf_id, infra=infra_info)

        if response['status'] != 'OK':
            error_reason = "Error while stopping VNF: " + response['error_reason']
            return {'status': 500, 'text': error_reason}

        return {'status': 200, 'text': "VNF function successfully stopped."}


def delete(vnf_id, vnfd_id):
    manager = Manager()
    vnf = Instance.objects.get(vnf_id=vnf_id)
    infra = Infrastructure.objects.get(name=vnf.infrastructure)
    infra_info = define_infra(infra)

    # delete VNF
    response = manager.vnf_delete(vnf_id, infra=infra_info)

    # remove VNFD from catalog
    response = manager.vnfd_delete(vnfd_id, infra=infra_info)

    # remove VNF from Instance table
    vnf = Instance.objects.filter(vnf_id=vnf_id)
    vnf.delete()

    return ("OK", None)


@login_required
def vnf_delete(request):
    """Delete a instantiated VNF."""

    if request.method == "POST":
        vnf_id = request.POST.get('vnf_id')
        vnfd_id = request.POST.get('vnfd_id')

        response = delete(vnf_id, vnfd_id)

        if response[0] == "OK":
            return {'status': 200, 'text': "VNF successfully deleted."}

        return {'status': 500, 'text': "Error while deleting VNF: " + response[1]}


@login_required
def update(request):
    """Update a instantiated VNF.

    This function will update the local repository and will
    replace both vnfd and vnf function on the instantiated VNF.
    """

    if request.method == "POST":
        vnf_id = request.POST.get('vnf_id')

        return vnf_update(vnf_id)


def vnf_update(request):
    """Update repository and VNFD."""

    if request.method == "POST":
        manager = Manager()
        vnf_id = request.POST.get('vnf_id')
        repository_id = request.POST.get('repository_id')

        vnf = Instance.objects.get(vnf_id=vnf_id)
        infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
        infra_info = define_infra(infra)

        # Search repository and generate the name_id.
        obj = Catalog.objects.filter(repository_id=repository_id)[0]
        name_id = get_name_id(obj)

        # update local repository
        url = "%s/repository/update/%s" % (server, name_id)
        response = requests.get(url, auth=auth)

        # verify if git pull was successful
        if not response.json()['success']:
            return {'status': 500, 'text': "Error while updating VNF: could not update repository."}

        # get updated vnfd
        url = "%s/vnfd/%s" % (server, name_id)
        vnfd = requests.get(url, auth=auth).json()
        vnfd_data = json.loads(vnfd['vnfd_data'])
        os_type = vnfd_data['vnfd']['attributes']['vnfd']['topology_template']['node_templates']['VDU1']['properties']['image']
        VDU_config = vnfd_data['vnfd']['attributes']['vnfd']['topology_template']['node_templates']['VDU1']

        # update VNFD
        response = manager.vnf_update(vnf_id, VDU_config, infra=infra_info)

        if response['status'] != 'OK':
            return {'status': 500, 'text': "Error while updating VNF: " + response['error_reason']}

        # get updated VNF function
        # if VNF is click-on-osv based, send click function
        # otherwise, send the entire repository
        if os_type == 'click-on-osv':
            url = "%s/vnf/function/%s" % (server, name_id)
            function = requests.get(url, auth=auth).json()
            function_data = function['function_data']
        elif os_type == 'ubuntu-18.10':
            url = "%s/vnf/repository/%s" % (server, name_id)
            function = requests.get(url, auth=auth).json()
            # open repository zip in binary to send to VNFM
            function_data = function['repository_path']

        if not function_data:
            error_reason = "Could not get VNF function."
            return {'status': 500, 'text': "Error while updating VNF: " + error_reason}

        response = manager.vnf_function_update(vnf_id, os_type, function_data, infra=infra_info)

        if response['status'] != 'OK':
            return {'status': 500, 'text': "Error while updating VNF: " + response['error_reason']}

        return {'status': 200, 'text': "VNF successfully updated."}


@login_required
def vnf_resize(request):
    """Update resources of a instantiated VNF."""

    if request.method == "POST":
        manager = Manager()
        mem_size = request.POST.get('mem_size')
        num_cpus = request.POST.get('num_cpus')
        disk_size = request.POST.get('disk_size')

        vnf_id = request.POST.get('vnf_id')
        repository_id = request.POST.get('repository')

        vnf = Instance.objects.get(vnf_id=vnf_id)
        infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
        infra_info = define_infra(infra)

        properties = {
            'mem_size': mem_size,
            'num_cpus': num_cpus,
            'disk_size': disk_size
        }

        # Search repository and generate the name_id.
        obj = Catalog.objects.filter(repository_id=repository_id)[0]
        name_id = get_name_id(obj)

        # get VNFD
        url = "%s/vnfd/%s" % (server, name_id)
        vnfd = requests.get(url, auth=auth).json()
        vnfd = json.loads(vnfd['vnfd_data'])

        # replace vnfd with updated properties
        vnfd['vnfd'] \
            ['attributes'] \
            ['vnfd'] \
            ['topology_template'] \
            ['node_templates'] \
            ['VDU1'] \
            ['capabilities'] \
            ['nfv_compute'] \
            ['properties'] = properties
        vnfd = json.dumps(vnfd)

        response = manager.vnf_update(vnf_id, vnfd, infra=infra_info)

        if response['status'] != 'OK':
            error_reason = "Error while updating VNF: " + response['error_reason']
            return {'status': 500, 'text': error_reason}

    return {'status': 200, 'text': "VNF successfully updated."}


def service(request):
    action = request.POST['action']

    if action == 'soft_restart':
        return sfc_soft_restart(request)

    elif action == 'full_restart':
        return sfc_full_restart(request)

    elif action == 'soft_stop':
        return sfc_soft_stop(request)

    elif action == 'full_stop':
        return sfc_full_stop(request)

    elif action == 'start':
        return sfc_start(request)

    elif action == 'update':
        return sfc_update(request)

    elif action == 'delete_sfc':
        return sfc_delete(request)

    return {'status': 500}


def function(request):
    action = request.POST['action']

    if action == 'restart_vnf':
        return vnf_restart(request)

    elif action == 'stop_vnf':
        return vnf_stop(request)

    elif action == 'delete_vnf':
        return vnf_delete(request)

    elif action == 'update':
        return vnf_update(request)

    elif action == 'resize_allocation':
        return vnf_resize(request)

    return {'status': 500}
