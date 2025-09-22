from django import template
import datetime

from marketplace.views import define_infra
from repository.models import Infrastructure
from vnfm.manager import Manager

register = template.Library()


@register.simple_tag()
def get_keys(user):
    keys = []
    infras = Infrastructure.objects.all()
    manager = Manager()
    for infra in infras:
        infra_info = define_infra(infra)
        response = Manager.get_ssh_key(manager, user, infra=infra_info)
        if response['status'] == 'OK':
            keys.append(response)
    return keys
