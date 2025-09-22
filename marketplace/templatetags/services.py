import requests
from django import template
from django.utils.safestring import mark_safe, SafeData
from django.template.defaultfilters import stringfilter

from marketplace.views import server, auth
from repository.models import Catalog
from repository.views import get_name_id

register = template.Library()

@register.filter
@stringfilter
def split(string, sep):
    """Return the string split by sep.

    Example usage: {{ value|split:"/" }}
    """
    return string.split(sep)

@register.filter
@stringfilter
def get_vnfs(string):
    string = string.split(',')
    vnfs = []
    while len(string)>0:
        vnfs.append((string[0], string[1]))
        string = string[2:]
    return vnfs


@register.simple_tag()
def get_vnfd(repo_id):
    obj = Catalog.objects.filter(repository_id=repo_id)[0]
    name_id = get_name_id(obj)
    url = "%s/vnfd/%s" % (server, name_id)
    vnfd = requests.get(url, auth=auth).json()['vnfd_data']
    return vnfd


@register.filter
@stringfilter
def get_step(string):
    string = float(string)

    x = (string * 100) / 8

    return str(x)
