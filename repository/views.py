# -*- coding: utf-8 -*-
import errno
from shutil import make_archive
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render_to_response, redirect, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.core.urlresolvers import reverse, reverse_lazy, get_script_prefix
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext as _
from django.contrib.auth import authenticate, login
from accounts.models import User, Institution
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve

from django.forms import ModelForm
from .forms import *
import logging
import requests
import re
import pdb
import json
import os

from .models import *

# APIRest Config
server = "http://localhost:5000"
user = "f&=gAt&ejuTHuqUKafaKe=2*"
token = "bUpAnebeC$ac@4asaph#DrEb"
auth = (user, token)


# Acesso: user:token@server

def is_developer(user):
    """Verify if user is a developer."""
    return user.groups.filter(name='Developer').exists()


def is_reviewer(user):
    """Verify if user is a reviewer."""
    return user.groups.filter(name='Reviewer').exists()


def is_consultant(user):
    """Verify if user is a reviewer."""
    return user.groups.filter(name='Consultant').exists()


def move_repository(name_id):
    """move a repository."""
    url = "%s/move/%s" % (server, name_id)
    requests.get(url, auth=auth)


def create_repository(name_id, url):
    """Clone a repository (git clone)."""

    url = "%s/repository/create/%s/%s" % (server, name_id, url)
    requests.get(url, auth=auth)


def update_repository(name_id):
    """Update a local repository (git pull)."""

    url = "%s/repository/update/%s" % (server, name_id)
    requests.get(url, auth=auth)


def get_config(name_id):
    """Get the config file."""

    url = "%s/config/%s" % (server, name_id)
    config = requests.get(url, auth=auth).json()
    return config['config_data']


def get_name_id(obj):
    """
    # Cria o name_id = vnf_name-version-developer
    """

    return '-'.join([str(obj.VNF_name), str(obj.version), str(obj.developer)]) \
        .replace(' ', '')


@login_required
@user_passes_test(is_developer)
def dev_dashboard(request):
    """Developers dashboard."""

    template = loader.get_template('dev_dashboard.html')
    return HttpResponse(template.render({}, request))


@login_required
@user_passes_test(is_developer)
def dev_publish(request):
    """Process and store requisition form requests."""

    if request.method == "POST":
        form = RequestForm(request.POST)
        if form.is_valid():
            submit = form.save(commit=False)
            submit.tag = 'New'
            submit.developer = request.user
            submit.save()
            vnf_list = [vnf for vnf in Request.objects.filter(developer=request.user)]
            vnfd_list = [vnf for vnf in RequestVNFD.objects.filter(developer=request.user)]
            return render(request, 'Publish/status.html', {
                "vnf_list": vnf_list,
                "vnfd_list": vnfd_list,
            })
    else:
        form = RequestForm()
    return render(request, 'Publish/publish.html', {'form': form})


descriptor = {
    "vnfd": {
        "name": "Ubuntu-VNFD",
        "description": "Ubuntu template",
        "service_types": [
            {
                "service_type": "vnfd"
            }
        ],
        "attributes": {
            "vnfd": {
                "tosca_definitions_version": "tosca_simple_profile_for_nfv_1_0_0",
                "metadata": {
                    "template_name": "sample-tosca-vnfd"
                },
                "topology_template": {
                    "node_templates": {
                        "VDU1": {
                            "type": "tosca.nodes.nfv.VDU.Tacker",
                            "capabilities": {
                                "nfv_compute": {
                                    "properties": {
                                        "num_cpus": 1,
                                        "mem_size": "512 MB",
                                        "disk_size": "5 GB"
                                    }
                                }
                            },
                            "properties": {
                                "image": "ubuntu-18.10",
                                "availability_zone": "nova",
                                "mgmt_driver": "noop"
                            }
                        },
                        "CP_mgmt": {
                            "type": "tosca.nodes.nfv.CP.Tacker",
                            "properties": {
                                "order": 0,
                                "management": 'true',
                                "anti_spoofing_protection": 'false'
                            },
                            "requirements": [
                                {
                                    "virtualLink": {
                                        "node": "VL22"
                                    }
                                },
                                {
                                    "virtualBinding": {
                                        "node": "VDU1"
                                    }
                                }
                            ]
                        },
                        "CP_traffic": {
                            "type": "tosca.nodes.nfv.CP.Tacker",
                            "properties": {
                                "order": 1,
                                "management": 'false',
                                "anti_spoofing_protection": 'false'
                            },
                            "requirements": [
                                {
                                    "virtualLink": {
                                        "node": "VL23"
                                    }
                                },
                                {
                                    "virtualBinding": {
                                        "node": "VDU1"
                                    }
                                }
                            ]
                        },
                        "VL22": {
                            "type": "tosca.nodes.nfv.VL",
                            "properties": {
                                "vendor": "Tacker",
                                "network_name": "net_mgmt"
                            }
                        },
                        "VL23": {
                            "type": "tosca.nodes.nfv.VL",
                            "properties": {
                                "vendor": "Tacker",
                                "network_name": "private"
                            }
                        }
                    }
                }
            }
        }
    }
}


@login_required
@user_passes_test(is_developer)
def vnf_publish(request):
    form = ManagementForm()
    scriptsform = ScriptsForm()
    apiform = APIForm()
    zipform = ZipForm()
    formset = CallFormset()

    dados = {}
    descriptor_json = descriptor

    seletores = [('see_source_code', 'Who can see the VNF source code?'), ('contract_VNF', 'Who can contract the VNF?'),
                 ('fork', 'Can this package be used by other developer? i.e., fork')]

    if request.method == 'POST':
        version = request.POST['version']
        vnfname = request.POST['name'].replace(' ', '')
        Abstract = request.POST['abstract']
        category = Category.objects.get(id=int(request.POST['category']))
        institution = Institution.objects.get(id=int(request.POST['institution']))

        dir = '/var/lib/fende/temp/' + vnfname + '-' + version + '-' + request.user.username + '/'

        managementdir = dir + 'Management/'
        management = managementdir + 'management.json'

        configsdir = dir + 'Configs/'
        config = configsdir + 'config.json'

        descriptorsdir = dir + 'Descriptors/'
        vnfd = descriptorsdir + 'vnfd.json'

        scripts = managementdir + 'Scripts/'
        install = scripts + 'install.sh'
        start = scripts + 'start.sh'
        stop = scripts + 'stop.sh'

        API = managementdir + 'API/'

        # CONFIG JSON
        config_json = {'FENDE': {'permissions': {}}}

        for seletor in seletores:
            if request.POST[seletor[0]] is not 'none':
                config_json['FENDE']['permissions'][seletor[0]] = request.POST[seletor[0]].replace(',', ';')

        # DESCRIPTOR JSON
        descriptor_json['vnfd']['name'] = vnfname
        descriptor_json['vnfd']['description'] = request.POST['description']

        if not os.path.exists(os.path.dirname(dir)):
            try:
                os.makedirs(os.path.dirname(dir))
                os.makedirs(os.path.dirname(managementdir))
                os.makedirs(os.path.dirname(configsdir))
                os.makedirs(os.path.dirname(descriptorsdir))
                os.makedirs(os.path.dirname(scripts))

            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        if request.FILES.get('file'):
            zipform = ZipForm(request.POST, request.FILES, dir=scripts)
            if zipform.is_valid():
                pass
            else:
                messages.error(request, 'Upload invalido')

        else:
            scriptsform = ScriptsForm(request.POST)
            if scriptsform.is_valid():
                install_text = request.POST['install']
                stop_text = request.POST['stop']
                start_text = request.POST['start']
                install_file = open(install, 'w')
                install_file.write(install_text)
                start_file = open(start, 'w')
                start_file.write(start_text)
                stop_file = open(stop, 'w')
                stop_file.write(stop_text)

        dados["lifecycle_events"] = []
        dados["lifecycle_events"].append({
            "event": "INSTALL",
            "lifecycle_events": ["Scripts/install.sh", ]
        })
        dados["lifecycle_events"].append({
            "event": "START",
            "lifecycle_events": ["Scripts/start.sh", ]
        })
        dados["lifecycle_events"].append({
            "event": "STOP",
            "lifecycle_events": ["Scripts/stop.sh", ]
        })

        form = ManagementForm(request.POST)
        if form.is_valid():
            dados["log_file"] = form.cleaned_data['logfile']

        if request.POST.get('active'):
            apiform = APIForm(request.POST, request.FILES, dir=API)
            if apiform.is_valid():
                dados["VNF_api"] = {}
                dados["VNF_api"]["run_file"] = apiform.cleaned_data['run_file']
                dados["VNF_api"]["stop_file"] = apiform.cleaned_data['stop_file']
                dados["VNF_api"]["port"] = apiform.cleaned_data['port']
                dados["VNF_api"]["authenticationParameters"] = {}
                dados["VNF_api"]["authenticationParameters"]["username"] = apiform.cleaned_data['username']
                dados["VNF_api"]["authenticationParameters"]["password"] = apiform.cleaned_data['password']

            formset = CallFormset(request.POST)
            if formset.is_valid():
                dados['calls'] = []
                for form in formset:
                    dics = {'method': form.cleaned_data['method'], 'methodType': form.cleaned_data['methodType'],
                            'call': form.cleaned_data['call'], 'description': form.cleaned_data['description'],
                            'parameters': form.cleaned_data['parameters']}
                    dados['calls'].append(dics)

        # SALVA OS JSON
        with open(management, 'w+') as json_file:
            json.dump(dados, json_file)

        with open(config, 'w+') as json_file:
            json.dump(config_json, json_file)

        with open(vnfd, 'w+') as json_file:
            json.dump(descriptor_json, json_file)

        # todo: puxar institution do user?

        Request.objects.create(tag='New', review_tag="To Review", developer=request.user,
                               institution=institution, VNF_name=vnfname,
                               version=request.POST['version'], category=category, abstract=Abstract,
                               full_description=request.POST.get('description', ''),
                               link='Package Constructor')

        messages.success(request, 'Package VNF created!')
        return redirect('Repository:dev_submission_status')

    institutions = Institution.objects.all()
    categories = Category.objects.all()
    return render(request, 'Publish/vnf_publish.html', {'scriptsform': scriptsform,
                                                        'apiform': apiform,
                                                        'zipform': zipform,
                                                        'formset': formset,
                                                        'form': form,
                                                        'seletores': seletores,
                                                        'categories': categories,
                                                        'institutions': institutions})


@login_required
@user_passes_test(is_developer)
def dev_myrepositories(request):
    """List all developers VNFs."""

    # get VNFs from Catalog and return it to dashboard.
    vnf_list = [vnf for vnf in Catalog.objects.filter(developer=request.user)]

    return render(request, 'my_repositories.html', {
        "vnf_list": vnf_list,
    })


@login_required
@user_passes_test(is_developer)
def dev_policy_update(request):
    """Update policies to access and contract a VNF."""

    if request.method == "POST":
        code = request.POST.get('code_source')
        contract = request.POST.get('contract_vnf')
        vnf_id = request.POST.get('vnf_id')

        # Search for the old permission and delete it
        obj = Permission.objects.filter(VNF=vnf_id)
        for p in obj:
            p.delete()
        # Create and save a new permission
        new_permission = Permission(VNF=vnf_id, code_source=code, contract_vnf=contract)
        new_permission.save()

    # get VNFs from Catalog and return it to dashboard.
    vnf_list = [vnf for vnf in Catalog.objects.filter(developer=request.user)]

    return render(request, 'my_repositories.html', {
        "vnf_list": vnf_list,
    })


@login_required
@user_passes_test(is_developer)
def dev_updateform(request):
    """Update form subimssion."""

    url = request.path
    data = url.split("/")

    # Search repository through VNF name and version from URL
    obj = Catalog.objects.filter(VNF_name=data[5], version=data[6])
    for o in obj:
        name = o.VNF_name
        institution = o.institution

    # security test: avoid that a different user from developer try
    # to update VNF through URL.
    if o.developer != request.user:
        return render(request, 'dev_dashboard.html')

    if request.method == "POST":
        form = UpdateForm(request.POST or None)
        if form.is_valid():
            submit = form.save(commit=False)
            submit.tag = 'Update'
            submit.developer = request.user
            submit.VNF_name = name
            submit.institution = institution
            submit.save()
            return render(request, 'dev_dashboard.html')
    else:
        form = UpdateForm()
    return render(request, 'Publish/update.html', {'form': form})


@login_required
@user_passes_test(is_developer)
def dev_VNFD_update(request):
    """Create a Request with the new VNFD content to review."""
    if request.method == "POST":
        repository = request.POST.get('vnf_id')
        content = request.FILES.get('vnfd_content')
        vnfd_comments = request.POST.get('vnfd_comments')
        data = repository.split("-")
        obj = Catalog.objects.filter(VNF_name=data[0], version=data[1], developer=request.user)[0]
        name_id = get_name_id(obj)
        # Store the new VNFD file
        arq = open('/var/lib/fende/%s/Descriptors/new_vnfd.json' % name_id, 'w')
        arq.writelines(content)
        arq.close()

        new_VNFD = RequestVNFD(institution=obj.institution, developer=request.user, VNF_name=obj.VNF_name,
                               version=obj.version, category=obj.category, abstract=obj.abstract, link=obj.link,
                               details=vnfd_comments)
        new_VNFD.save()

    return HttpResponseRedirect('/repository/dev/my_repositories/')


@login_required
@user_passes_test(is_reviewer)
def review_list(request):
    """List all review pending repositories"""

    # search repository through ID from URL
    repository = Request.objects.filter(review_tag="To Review")

    # get all pending requests from Request table
    review_list = [review for review in Request.objects.filter(review_tag='To Review')]

    return render(request, 'Review/review_list.html', {
        "review_list": review_list,
        "repository": repository,
    })


@login_required
@user_passes_test(is_reviewer)
def vnfd_list(request):
    """List all review pending VNFDs update"""

    # get all pending requests from Request table
    review_list = [review for review in RequestVNFD.objects.filter(review_tag='To Review')]

    return render(request, 'Review/vnfd_list.html', {
        "review_list": review_list
    })


@login_required
@user_passes_test(is_reviewer)
def vnfd_download(request):
    """Provide the content of new VNFD file to the Reviewer."""
    url = request.path
    data = url.split("/")
    name_id = data[5].replace(" ", "")
    filepath = '/var/lib/fende/%s/Descriptors/new_vnfd.json' % name_id
    return serve(request, os.path.basename(filepath), os.path.dirname(filepath))


@login_required
@user_passes_test(is_reviewer)
def review_details(request):
    """Show details of a review request."""

    url = request.path
    data = url.split("/")

    # search repository through ID from URL
    obj = Request.objects.filter(request_id=data[4])[0]

    return render(request, 'Review/details.html', {
        "repository": obj,
    })


@login_required
@user_passes_test(is_reviewer)
def repository_accept(request):
    """Accept repository for index."""

    if request.method == "POST":
        data = request.POST.get('repository')
        reviews = request.POST.get('comments')

        # Search repository and generate the name_id.
        obj = Request.objects.filter(request_id=data)[0]
        name_id = get_name_id(obj)
        control = str(obj.tag)

        if obj.link == 'Package Constructor':
            move_repository(name_id)
        else:
            # clone repository locally
            create_repository(name_id, obj.link)

        # get file with necessary configs for FENDE
        try:
            config = get_config(name_id)
        except:
            messages.error(request, 'config_data not found')
            return HttpResponseRedirect('/repository/review/')

        # policy parser
        data = json.loads(config)
        code_policy = data["FENDE"]["permissions"]["see_source_code"]  # all/none/<inst1;inst2;inst3;...>
        contract_policy = data["FENDE"]["permissions"]["contract_VNF"]  # all/none/<inst1;inst2;inst3;...>

        if control == 'New':
            # create a new Catalog object
            new_catalog = Catalog(
                institution=obj.institution,
                developer=obj.developer,
                VNF_name=obj.VNF_name,
                version=obj.version,
                category=obj.category,
                abstract=obj.abstract,
                full_description=obj.full_description,
                link=obj.link
            )
            new_catalog.save()

            # create new permission policy
            new_policy = Permission(
                VNF=name_id,
                code_source=code_policy,
                contract_vnf=contract_policy
            )
            new_policy.save()

        if control == 'Update':
            # search for entry through Developer+VNF_Name key
            catalog_obj = Catalog.objects.filter(developer=obj.developer, VNF_name=obj.VNF_name)

            for p in catalog_obj:
                # create a copy of current VNF for table Versions
                new_version = Version(
                    institution=p.institution,
                    developer=p.developer,
                    VNF_name=p.VNF_name,
                    version=p.version,
                    category=p.category,
                    abstract=p.abstract,
                    full_description=p.full_description,
                    link=p.link
                )

                # create new object of type Catalog
                version_to_catalog = Catalog(
                    institution=p.institution,
                    developer=p.developer,
                    VNF_name=p.VNF_name,
                    version=obj.version,
                    category=obj.category,
                    abstract=obj.abstract,
                    full_description=obj.full_description,
                    link=obj.link
                )
                # delete current version from Catalog
                p.delete()

            # save updated object on Catalog table
            version_to_catalog.save()

            # save previous version on Version table
            new_version.save()

        # Update object in Request table
        obj.review_tag = 'Accepted'
        obj.comments = reviews
        obj.save()

        return HttpResponseRedirect('/repository/review/')


@login_required
@user_passes_test(is_reviewer)
def repository_reject(request):
    """Reject a repository."""

    if request.method == "POST":
        data = request.POST.get('repository')
        reviews = request.POST.get('comments')
        obj = Request.objects.filter(request_id=data)[0]

        # Update object in Request table
        obj.review_tag = 'Rejected'
        obj.comments = reviews
        obj.save()

        return HttpResponseRedirect('/repository/review/')


@login_required
@user_passes_test(is_developer)
def dev_submission_status(request):
    """Show status and comments of each submission (accepted or rejected)."""

    # get VNFs from Requests and return it to table.
    vnf_list = [vnf for vnf in Request.objects.filter(developer=request.user)]
    vnfd_list = [vnf for vnf in RequestVNFD.objects.filter(developer=request.user)]

    return render(request, 'Publish/status.html', {
        "vnf_list": vnf_list,
        "vnfd_list": vnfd_list,
    })


@login_required
@user_passes_test(is_reviewer)
def download(request, id):
    """
    A django view to zip files in directory and send it as downloadable response to the browser.
    Args:
      @request: Django request object
      @file_name: Name of the directory to be zipped
    Returns:
      A downloadable Http response
    """

    obj = Request.objects.get(request_id=id)
    file_name = obj.VNF_name.replace(' ', '') + '-' + obj.version + '-' + request.user.username
    file_path = '/var/lib/fende/temp/'
    file_path += file_name
    path_to_zip = make_archive(file_path, "zip", file_path)
    response = HttpResponse(FileWrapper(open(path_to_zip, 'rb')), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="{filename}.zip"'.format(
        filename=file_name.replace(" ", "_")
    )
    return response


@login_required
@user_passes_test(is_reviewer)
def vnfd_reject(request):
    """Reject a VNFD update."""

    if request.method == "POST":
        data = request.POST.get('repository')
        reviews = request.POST.get('comments')
        obj = RequestVNFD.objects.filter(request_id=data)[0]

        # Update object in Request table
        obj.review_tag = 'Rejected'
        obj.comments = reviews
        obj.save()

        return HttpResponseRedirect('/repository/review/vnfd/')


@login_required
@user_passes_test(is_reviewer)
def vnfd_accept(request):
    """Accept a request for VNFD update."""

    if request.method == "POST":
        data = request.POST.get('repository')
        reviews = request.POST.get('comments')

        # Search repository and generate the name_id.
        obj = RequestVNFD.objects.filter(request_id=data)[0]
        name_id = get_name_id(obj)
        # Update the current VNFD file. The last VNFD is maintened as a backup
        os.system('mv /var/lib/fende/%s/Descriptors/vnfd.json /var/lib/fende/%s/Descriptors/old_vnfd.json' % (
            name_id, name_id))
        os.system('mv /var/lib/fende/%s/Descriptors/new_vnfd.json /var/lib/fende/%s/Descriptors/vnfd.json' % (
            name_id, name_id))

        # Update object in VNFD Request table
        obj.review_tag = 'Accepted'
        obj.comments = reviews
        obj.save()

        return HttpResponseRedirect('/repository/review/vnfd/')


@login_required
@user_passes_test(is_developer)
def tutorial(request, tutorial):
    return render(request, 'tutorial/%s.html' % tutorial)


@login_required
@user_passes_test(is_developer)
def dev_package_upload(request):
    form = UploadForm(initial={'institution': request.user.institution})
    if request.method == 'POST':
        version = request.POST['version']
        vnfname = request.POST['VNF_name'].replace(' ', '')
        dir = '/var/lib/fende/temp/' + vnfname + '-' + version + '-' + request.user.username + '/'
        form = UploadForm(request.POST, request.FILES, dir=dir)
        if form.is_valid():
            if not os.path.exists(os.path.dirname(dir)):
                try:
                    os.makedirs(os.path.dirname(dir))
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

            submit = form.save(commit=False)
            submit.tag = 'New'
            submit.link = 'Package Constructor'
            submit.developer = request.user
            submit.save()
            messages.success(request, 'Package VNF created!')
            return redirect('Repository:dev_submission_status')
        else:
            pass

    return render(request, 'Publish/dev_package_upload.html', {'form': form})



