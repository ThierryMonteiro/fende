def service(request):
    # request.POST['vnffg_id']
    action = request.POST['action']
    if action == 'soft_restart':
        return {'status': 'OK'}

    if action == 'full_restart':
        return {'status': 'OK'}

    if action == 'soft_stop':
        return {'status': 'OK'}

    if action == 'full_stop':
        return {'status': 'OK'}

    if action == 'start':
        return {'status': 'OK'}

    if action == 'update':
        return {'status': 'OK'}

    if action == 'delete_sfc':
        return {'status': 'OK'}


def function(request):
    action = request.POST['action']
    if action == 'restart_vnf':
        return {'status': 'OK'}

    if action == 'stop_vnf':
        return {'status': 'OK'}

    if action == 'delete_vnf':
        return {'status': 'OK'}

    if action == 'update':
        return {'status': 'OK'}

    if action == 'resize_allocation':
        return {'status': 'OK'}

    if action == 'vnf_info':
        return {'status': 'OK'}
