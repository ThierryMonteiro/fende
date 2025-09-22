from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from django.views.generic.edit import CreateView

from marketplace.models import Catalog_SFC
from repository.models.catalog import Catalog
from accounts.models import User
from accounts.forms import UserCreationForm, Autenticacao

import time

from celery import shared_task




@login_required
def index(request):
    return HttpResponseRedirect("/marketplace/")


def about(request):
    active_view = 'about'
    context = {
        'active_view': active_view,
        'form': Autenticacao,
        'formup': UserCreationForm,
    }
    return render(request, 'core/about.html', context)


def team(request):
    active_view = 'team'
    context = {
        'active_view': active_view,
        'form': Autenticacao,
        'formup': UserCreationForm,
    }
    return render(request, 'core/team.html', context)


def services(request, id):
    active_view = 'services'
    service = Catalog_SFC.objects.get(id=id)
    context = {
        'active_view': active_view,
        'form': Autenticacao,
        'formup': UserCreationForm,
        'service': service,
    }
    return render(request, 'core/services.html', context)


def publications(request):
    active_view = 'publications'
    context = {
        'active_view': active_view,
        'form': Autenticacao,
        'formup': UserCreationForm,
    }
    return render(request, 'core/publications.html', context)


def actor(request, type):
    if type == 'consultant':
        if request.user.groups.filter(name='Consultant').exists():
            request.session['actor'] = 'consultant'
            return redirect('Marketplace:catalog_vnfs')
    if type == 'developer':
        if request.user.groups.filter(name='Developer').exists():
            request.session['actor'] = 'developer'
            return redirect('Repository:dev_myrepositories')
    if type == 'reviewer':
        if request.user.groups.filter(name='Reviewer').exists():
            request.session['actor'] = 'reviewer'
            return redirect('Repository:review_list')
    else:
        request.session['actor'] = 'tenant'
        return redirect('Marketplace:index')


class UserCreate(CreateView):
    model = User
    template_name = 'core/home.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        valid = super(UserCreate, self).form_valid(form)
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        new_user = authenticate(username=username, password=password)
        login(self.request, new_user)
        return valid

    def get_context_data(self, **kwargs):
        ctx = super(UserCreate, self).get_context_data(**kwargs)
        ctx['services'] = Catalog_SFC.objects.all()
        ctx['formup'] = self.get_form()
        ctx['form'] = Autenticacao
        return ctx
