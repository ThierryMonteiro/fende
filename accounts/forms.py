# coding=utf-8

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms

from .models import User
from django.utils.translation import gettext as _
from django.contrib.auth.models import Group


class UserAdminCreationForm(UserCreationForm):
    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=True,
                                   help_text="Select one Group")

    class Meta:
        model = User
        fields = ['username', 'email', 'group', 'birthdate']

    def save(self, commit=True):
        instance = super(UserAdminCreationForm, self).save(commit=False)
        group = Group.objects.get(name=self.cleaned_data['group'])
        if group:
            if str(self.cleaned_data['group']) == 'Developer':
                instance.avatar = '/static/img/avatars/developer.png'
            if str(self.cleaned_data['group']) == 'Reviewer':
                instance.avatar = '/static/img/avatars/reviewer.png'
        if commit:
            instance.save()
            group.user_set.add(instance)
        return instance


class Profile_Form(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'birthdate']
        widgets = {
            'birthdate': forms.SelectDateWidget(attrs={'class': 'form-control col-4'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class UserCreationForm(UserCreationForm):
    # group = forms.ModelChoiceField(queryset=Group.objects.exclude(name='Reviewer'), required=True,
    #                                help_text="Select one Group",
    #                                widget=forms.Select(attrs={'class': 'form-control form-control-sm'}))

    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}),
                                help_text=_("Enter the same password as before, for verification."))

    class Meta:
        model = User
        fields = ['username', 'email', 'birthdate', 'institution']
        widgets = {
            'birthdate': forms.SelectDateWidget(attrs={'class': 'form-control col-4'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'institution': forms.Select(attrs={'class': 'form-control'}),
        }

    # def save(self, commit=True):
    #     instance = super(UserCreationForm, self).save(commit=False)
    #     group = Group.objects.get(name=self.cleaned_data['group'])
    #     if group:
    #         if str(self.cleaned_data['group']) == 'Developer':
    #             instance.avatar = '/static/img/avatars/developer.png'
    #     if commit:
    #         instance.save()
    #         group.user_set.add(instance)
    #     return instance


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'name', 'is_active', 'is_staff']


class Autenticacao(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(attrs={'class': 'form-control form-control-sm'}))
