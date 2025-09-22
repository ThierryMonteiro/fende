from django import template
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse, get_script_prefix, NoReverseMatch
from django.utils.translation import ugettext as _
import json

register = template.Library()

@register.inclusion_tag('advanced_inputs/widgets.html')
def fende_widget(location='end', widget_type='default', id=None, title=None, tutorial=None, size=None, icon='fa-list-alt', coluna='12'):
    return {'widget_type': widget_type, 'location': location, 'id': id, 'title': title, 'tutorial': tutorial, 'size': size, 'icon': icon, 'coluna': coluna}
