# coding=utf-8
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import (
    CreateView, TemplateView, UpdateView, FormView
)
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import login as auth_login

from marketplace.views import define_infra, DEFAULT_INFRA
from repository.models import Infrastructure
from vnfm.manager import Manager
from .models import User
from .forms import *


@login_required
def index(request):
    profile_form = Profile_Form(instance=request.user)
    password_form = PasswordChangeForm(user=request.user)
    if request.method == 'POST':
        if request.POST.get('profile'):
            profile_form = Profile_Form(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile has been updated!')
            else:
                messages.error(request, 'Input Error')
        if request.POST.get('password'):
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Password has been changed!')
            else:
                messages.error(request, 'Input Error')
    context = {'profile_form': profile_form,
               'password_form': password_form}
    return render(request, 'accounts/index.html', context)


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/index.html'


@login_required
def ssh_key(request):
    infras = Infrastructure.objects.all().values('name')
    if request.method == 'POST':
        infra = Infrastructure.objects.get(name=request.POST['infra'])
        infra_info = define_infra(infra)
        manager = Manager()
        if request.POST.get('new_ssh_key', None):
            ssh_key = request.POST['new_ssh_key']
            response = manager.create_ssh_key(request.user.username, ssh_key, infra=infra_info)
        else:
            response = manager.create_ssh_key(request.user.username, None, infra=infra_info)

        if response['status'] == 'OK':
            messages.success(request, 'SSH Key created successfully')
        else:
            messages.error(request, response['error_reason'])

    return render(request, 'accounts/ssh.html', {'infras': infras})


@login_required
def remove_key(request, id):
    infra = Infrastructure.objects.get(infra_id=id)
    infra_info = define_infra(infra)
    manager = Manager()
    response = manager.delete_ssh_key(request.user, infra=infra_info)
    if response['status'] == 'OK':
        messages.success(request, 'SSH Key deleted successfully')
    else:
        messages.error(request, response['error_reason'])
    return redirect('accounts:ssh_key')
