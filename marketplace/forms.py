from django import forms

from .models import *
import requests
# Utility functions
from marketplace.utils import *
import json

from django.utils.translation import gettext as _
from django.forms import inlineformset_factory

# AES Crypto
from hashlib import md5
from base64 import b64decode
from base64 import b64encode
from Crypto import Random
from Crypto.Cipher import AES


# CATALOGO
class CatalogForm(forms.ModelForm):
    def getCPs(self, vnf):
        server = "http://localhost:5000"
        user = "f&=gAt&ejuTHuqUKafaKe=2*"
        token = "bUpAnebeC$ac@4asaph#DrEb"
        auth = (user, token)

        obj = Catalog.objects.get(repository_id=vnf)  # vnf_id eh o valor do campo anterior
        name_id = get_name_id(obj)
        url = "%s/vnfd/%s" % (server, name_id)
        try:
            vnfd = requests.get(url, auth=auth)
        except:
            return ((None, 'Sem conexao'),)
        vnfd = json.loads(vnfd.content)
        vnfd = json.loads(vnfd['vnfd_data'])
        node_templates = vnfd['vnfd']['attributes']['vnfd']['topology_template']['node_templates']
        cp_keys = [atr for atr in node_templates.keys() if atr.startswith('CP')]
        cp_tuples = list()
        for cp in cp_keys:
            cp_tuples.append((cp, str(cp)))
        return cp_tuples

    class Meta:
        model = Catalog_SFC
        exclude = ['consultant', 'vnfs']
        widgets = {'full_description': forms.Textarea(
            attrs={'class': 'form-control form-control-sm', 'placeholder': 'Full Description'}),
            'sfc_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'SFC Name'}),
            'institution': forms.TextInput(
                attrs={'class': 'form-control form-control-sm', 'placeholder': 'Institution'}),
            'price': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'version': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Version'}),
            'category': forms.Select(attrs={'class': 'select2'}),
            'tag': forms.SelectMultiple(attrs={'class': 'select2'})}

    def __init__(self, *args, **kwargs):
        self.vnfs = kwargs.pop('vnfs')
        super(CatalogForm, self).__init__(*args, **kwargs)
        i = 0
        for vnf in self.vnfs:
            name = Catalog.objects.get(repository_id=vnf).VNF_name
            self.fields['name' + str(i)] = forms.CharField(label='VNF Name:',
                                                           help_text='Name of VNF:',
                                                           initial=name,
                                                           widget=forms.TextInput(attrs={'readonly': 'True',
                                                                                         'class': 'form-control form-control-sm'})
                                                           )
            self.fields['repository' + str(i)] = forms.CharField(label='Repository',
                                                                 initial=int(vnf),
                                                                 widget=forms.TextInput(attrs={'type': 'hidden',
                                                                                               'class': 'form-control form-control-sm'})
                                                                 )
            self.fields['input' + str(i)] = forms.ChoiceField(label='Input', choices=self.getCPs(vnf),
                                                              widget=forms.Select(attrs={'class': 'select2'}))
            self.fields['output' + str(i)] = forms.ChoiceField(label='Output', choices=self.getCPs(vnf),
                                                               widget=forms.Select(attrs={'class': 'select2'}))
            i += 1


# PRINTFormSet
class PrintForm(forms.ModelForm):
    class Meta:
        model = Print
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(PrintForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


PrintFormSet = inlineformset_factory(Catalog_SFC, Print,
                                     form=PrintForm, extra=1)


class AESCipher:
    """
    Usage:
        c = AESCipher('password').encrypt('message')
        m = AESCipher('password').decrypt(c)
    """

    def __init__(self, key):
        self.key = md5(key.encode('utf8')).hexdigest()

    def encrypt(self, raw):
        raw = pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(enc[16:])).decode('utf8')


# AES Settings
BLOCK_SIZE = 16  # Bytes
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * \
                chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]
pwd = "43!91$%82947mff320148rs1048210#@"


class InfrastructureForm(forms.ModelForm):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(), required=False)

    class Meta:
        model = Infrastructure
        exclude = ('owner',)

    def clean_password(self):
        password = self.cleaned_data['password']

        if password != '':
            password = AESCipher(pwd).encrypt(password)
            return password
        else:
            password = self.instance.password
        return password

    def clean(self):

        # Then call the clean() method of the super  class
        cleaned_data = super(InfrastructureForm, self).clean()
        if cleaned_data['technology'] == 'openstack':
            if cleaned_data['tenant'] == '':
                raise forms.ValidationError(
                    "Tenant can not be null"
                )
            if cleaned_data['username'] == '':
                raise forms.ValidationError(
                    "Username can not be null"
                )

        if cleaned_data['technology'] == 'cloudstack':
            if cleaned_data['zone_id'] == '':
                raise forms.ValidationError(
                    "Zone id can not be null"
                )
            if cleaned_data['host_id'] == '':
                raise forms.ValidationError(
                    "Host id can not be null"
                )
            if cleaned_data['api_key'] == '':
                raise forms.ValidationError(
                    "Api Key can not be null"
                )
            if cleaned_data['secret_key'] == '':
                raise forms.ValidationError(
                    "Secret Key can not be null"
                )

        if cleaned_data['technology'] == 'kubernetes':
            if cleaned_data['token'] == '':
                raise forms.ValidationError(
                    "Token can not be null"
                )
            if cleaned_data['gateway_port'] == '':
                raise forms.ValidationError(
                    "Gateway can not be null"
                )
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super(InfrastructureForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
