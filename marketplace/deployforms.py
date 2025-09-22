from django import forms
from django.forms import formset_factory
import requests
from repository.models.acquisitions import Acquisitions
from repository.models.catalog import Catalog
from .models import *
import requests

import json
from core import settings
import os

from django.forms import inlineformset_factory


def getAcquisitions(user, vnfs):
    ids = []
    for vnf in vnfs:
        ids.append((int(vnf.repository_id), vnf.VNF_name))
    return ids


class DeployForm(forms.Form):

    def INFRAS(self):
        tuple = ()
        try:
            for item in Infrastructure.objects.all():
                tuple += ((str(item.infra_id), str(item.name)+'('+item.technology+')'),)
        except:
            tuple = ((),)
        return tuple

    PARAMETERS = (('CPU', 'CPU Usage'),
                  ('MEM', 'Total memory'),
                  ('BW', 'Bandwidth'))

    name = forms.CharField(label='Instance Name', max_length=40)
    infrastructure = forms.ChoiceField(label='Infrastructure')
    expose_port = forms.IntegerField(label='Expose Port', required=False)
    parameter = forms.ChoiceField(label='Parameter', widget=forms.Select, choices=PARAMETERS)
    type = forms.ChoiceField(label='Traffic Source', help_text='',
                             choices=(('internal', 'Internal'), ('external', 'External')))

    def __init__(self, *args, **kwargs):
        super(DeployForm, self).__init__(*args, **kwargs)
        self.fields['infrastructure'] = forms.ChoiceField(label='Infrastructure', widget=forms.Select,
                                                          choices=self.INFRAS())

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control form-control-sm'
            field.widget.attrs['placeholder'] = field.label


class ACL(forms.Form):
    def getCriterions():
        file = open(os.path.join(settings.BASE_DIR, 'docs/acl.json'), 'r')
        file = file.read()
        file = json.loads(file)

        options = []
        for line in file:
            options.append((line, file[line]['description']))
        return options

    criterion = forms.ChoiceField(label='Criterion', choices=getCriterions(),
                                  help_text='Criterion')
    field = forms.CharField(label='Value', max_length=100,
                            help_text='Value of criterion')

    def __init__(self, *args, **kwargs):
        super(ACL, self).__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control form-control-sm'
            field.widget.attrs['placeholder'] = field.label

    def clean(self):
        cleaned_data = super(ACL, self).clean()
        file = open(os.path.join(settings.BASE_DIR, 'docs/acl.json'), 'r')
        file = file.read()
        file = json.loads(file)
        for acl in cleaned_data.items()[1::2]:
            if file[acl[1]]['type'] == 'string':
                pass
            if file[acl[1]]['type'] == 'integer':
                try:
                    num = int(cleaned_data.get('field'))
                    if not num >= int(file[acl[1]]['in_range'][0]) or not num <= int(file[acl[1]]['in_range'][1]):
                        self.add_error(('field'), 'Input error, insert a Integer value in range ' + str(
                            file[acl[1]]['in_range'][0]) + ' and ' + str(file[acl[1]]['in_range'][1]))
                    cleaned_data['field'] = num
                except ValueError:
                    self.add_error('field', 'Input error, insert a Integer value')
                    # self.add_error('cc_myself', msg)

        return cleaned_data


ACLFormset = formset_factory(ACL, extra=1)
