import requests
from django import template

from marketplace.utils import get_name_id

register = template.Library()


@register.simple_tag()
def get_parameters(metodo, management):
    for item in management:
        if item['method'] == metodo:
            print('ACHOOOU', metodo)


@register.simple_tag()
def get_management(auth, instance):
    obj = instance.repository
    name_id = get_name_id(obj)
    url = "%s/management/%s" % (auth['server'], name_id)
    try:
        exists = requests.get(url, auth=auth['auth']).json()['management_data']
        return True
    except:
        return False
