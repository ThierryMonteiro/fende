from django import forms
from django.forms import formset_factory

from .models import Request
import zipfile


class ManagementForm(forms.Form):
    logfile = forms.CharField(label='Logfile', max_length=100, required=False)

    def clean_logfile(self):
        logfile = self.cleaned_data['logfile']
        if logfile == '':
            return "/var/log/syslog"
        return logfile


class CallForm(forms.Form):
    types = (('post', 'POST'),
             ('get', 'GET'))

    method = forms.CharField(label='Method', max_length=20,
                             widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Method'}))
    methodType = forms.ChoiceField(label='Method Type', choices=types,
                                   widget=forms.Select(attrs={'class': 'construct_select'}))
    call = forms.CharField(label='Call', max_length=20,
                           widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Call'}))
    parameters = forms.CharField(label='Parameters (separated by commas)', max_length=200,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Parameters'}))
    description = forms.CharField(label='Description', max_length=200,
                                  widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}))


class ScriptsForm(forms.Form):
    install = forms.CharField(label='Install', max_length=200,
                              widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}))
    start = forms.CharField(label='Start', max_length=200,
                            widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}))
    stop = forms.CharField(label='Stop', max_length=200,
                           widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}))


class APIForm(forms.Form):
    username = forms.SlugField(label='Username', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    port = forms.IntegerField(label='Port', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    files = forms.FileField('File', widget=forms.FileInput(attrs={'class': 'form-control-file mt-1'}))
    run_file = forms.CharField(label='Run API', max_length=200,
                               widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}))
    stop_file = forms.CharField(label='Stop API', max_length=200,
                                widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}))

    def clean_files(self):
        file = self.cleaned_data['files']
        if file.size > 2097152:
            raise forms.ValidationError("Tamanho do arquivo excedido")
        if file.name.split('.')[1] != 'zip':
            raise forms.ValidationError("Use formato ZIP")
        with zipfile.ZipFile(file, 'r') as files_zip:
            for name in files_zip.namelist():
                files_zip.extract(name, self.dir)
        return file

    def __init__(self, *args, **kwargs):
        self.dir = kwargs.pop('dir', '')
        super(APIForm, self).__init__(*args, **kwargs)


class ZipForm(forms.Form):
    file = forms.FileField('File')

    def clean_file(self):
        file = self.cleaned_data['file']
        if file.size > 2097152:
            raise forms.ValidationError("Tamanho do arquivo excedido")
        if file.name.split('.')[1] != 'zip':
            raise forms.ValidationError("Use formato ZIP")
        with zipfile.ZipFile(file, 'r') as files_zip:
            if 'install.sh' not in files_zip.namelist():
                raise forms.ValidationError("O arquivo ZIP deve conter um arquivo install.sh")
            if 'start.sh' not in files_zip.namelist():
                raise forms.ValidationError("O arquivo ZIP deve conter um arquivo start.sh")
            if 'stop.sh' not in files_zip.namelist():
                raise forms.ValidationError("O arquivo ZIP deve conter um arquivo stop.sh")
            for name in files_zip.namelist():
                files_zip.extract(name, self.dir)
        return file

    def __init__(self, *args, **kwargs):
        self.dir = kwargs.pop('dir', '')
        super(ZipForm, self).__init__(*args, **kwargs)


CallFormset = formset_factory(CallForm, extra=1)


class UploadForm(forms.ModelForm):
    abstract = forms.CharField(label='Abstract', max_length=200, widget=forms.Textarea(attrs={'rows': 5}))
    full_description = forms.CharField(label='Full Description', max_length=200,
                                       widget=forms.Textarea(attrs={'rows': 5}))
    file = forms.FileField('File')

    class Meta:
        model = Request
        fields = ('institution', 'VNF_name', 'version', 'category', 'abstract', 'full_description')

    def clean_file(self):
        file = self.cleaned_data['file']
        if file.size > 2097152:
            raise forms.ValidationError("Tamanho do arquivo excedido")
        if file.name.split('.')[1] != 'zip':
            raise forms.ValidationError("Use formato ZIP")
        with zipfile.ZipFile(file, 'r') as files_zip:
            for name in files_zip.namelist():
                files_zip.extract(name, self.dir)
        return file

    def __init__(self, *args, **kwargs):
        self.dir = kwargs.pop('dir', '')
        super(UploadForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class RequestForm(forms.ModelForm):
    abstract = forms.CharField(label='Abstract', max_length=200, widget=forms.Textarea(attrs={'rows': 3}))
    full_description = forms.CharField(label='Full Description', max_length=200,
                                       widget=forms.Textarea(attrs={'rows': 5}))

    class Meta:
        model = Request
        fields = ('institution', 'VNF_name', 'version', 'category', 'abstract', 'full_description', 'link')

    def __init__(self, *args, **kwargs):
        super(RequestForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class UpdateForm(forms.ModelForm):
    class Meta:
        model = Request
        exclude = ('institution', 'VNF_name')
        fields = ('version', 'category', 'abstract', 'full_description', 'link')
