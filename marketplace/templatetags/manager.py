from django import template

from marketplace.views import define_infra
from repository.models import Infrastructure
from vnfm.manager import Manager
from vnfm.cloudstack_manager import CloudstackManager

register = template.Library()


@register.simple_tag()
def get_vnclink(id, infra):
    try:
        infra_name = Infrastructure.objects.get(name=infra)
        infra_info = define_infra(infra_name)

        manager = Manager()
        cloudstack_manager = CloudstackManager()

        if infra_info['technology']=='openstack':
            data = Manager.get_vnc(manager, id, infra=infra_info)
        else:
            data = CloudstackManager.get_vnc(cloudstack_manager, id, infra_info)

        if data['status'] == 'OK':
            return data['vnc_url']
        else:
            return False
    except:
        return False
