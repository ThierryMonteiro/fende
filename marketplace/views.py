# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponse
from django.template import loader
from django.contrib import messages
from django.utils.decorators import method_decorator

from repository.utils import status_service
from .forms import *
from .deployforms import *
from django.views.generic.edit import CreateView, UpdateView

# AES Crypto
from hashlib import md5
from base64 import b64decode
from base64 import b64encode
from Crypto import Random
from Crypto.Cipher import AES

# Models
from repository.models.instances import *

# Utility functions
from utils import *

# SFC Status
from repository.utils import *

# VNF Manager module
from vnfm.manager import *
from vnfm.cloudstack_manager import *
from vnfm.kubernetes_manager import *

from core import settings

from watson import search as watson
from .models import *

from django.http import JsonResponse

from celery import shared_task

server = "http://localhost:5000"
user = "f&=gAt&ejuTHuqUKafaKe=2*"
token = "bUpAnebeC$ac@4asaph#DrEb"
auth = (user, token)

DEFAULT_INFRA = "UFPR (Default)"

logger = logging.getLogger(__name__)

manager = None

# AES Settings
BLOCK_SIZE = 16  # Bytes
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * \
                chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]
pwd = "43!91$%82947mff320148rs1048210#@"


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


if not settings.DEV_MODE:
    # initialize VNFM interface
    manager = Manager()
    cloudstack_manager = CloudstackManager()
    kubernetes_manager = KubernetesManager()


@login_required
def vnf_api(request, id):
    instance = Instance.objects.get(vnf_id=id)
    name_id = get_name_id(instance.repository)
    url = "%s/management/%s" % (server, name_id)
    calls = ''
    link = ''
    infra = Infrastructure.objects.get(name=instance.infrastructure)
    infra_info = define_infra(infra)
    try:
        calls = requests.get(url, auth=auth).json()['management_data']
        calls = json.loads(calls)
        link = instance.vnf_ip + ':' + str(calls['VNF_api']['port'])
        calls = calls['VNF_api']['calls']
    except:
        messages.error(request, 'Error not found management_data')
    return render(request, 'marketplace/vnf_api.html',
                  {'management': calls, 'link': link, 'infra_ip': infra_info['ip'],
                   'gateway_port': infra_info['gateway_port']})


@login_required
def resize(request, id):
    """Update resources of a instantiated VNF."""
    url = '/marketplace/sfc/sfc_path/' + str(id)
    if request.method == "POST":
        mem_size = request.POST.get('mem_size')
        num_cpus = request.POST.get('num_cpus')
        disk_size = request.POST.get('disk_size')
        vnf_id = request.POST.get('vnf_id')
        repository_id = request.POST.get('repository')

        vnf = Instance.objects.get(vnf_id=vnf_id)
        infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
        infra_info = define_infra(infra)

        properties = {
            'mem_size': mem_size,
            'num_cpus': num_cpus,
            'disk_size': disk_size
        }

        # Search repository and generate the name_id.
        obj = Catalog.objects.filter(repository_id=repository_id)[0]
        name_id = get_name_id(obj)

        # get vnfd
        url = "%s/vnfd/%s" % (server, name_id)
        vnfd = requests.get(url, auth=auth).json()
        vnfd = json.loads(vnfd['vnfd_data'])

        # replace vnfd with updated properties
        vnfd['vnfd'] \
            ['attributes'] \
            ['vnfd'] \
            ['topology_template'] \
            ['node_templates'] \
            ['VDU1'] \
            ['capabilities'] \
            ['nfv_compute'] \
            ['properties'] = properties
        vnfd = json.dumps(vnfd)

        response = manager.vnf_update(vnf_id, vnfd, infra=infra_info)

        if response['status'] != 'OK':
            error_reason = response['error_reason']
            messages.error(request, "Could not update VNF: " + error_reason)
            return redirect(url)

    messages.success(request, "VNF successfully updated.")

    return redirect(url)


def service(request, id):
    service = Catalog_SFC.objects.get(id=id)
    return render(request, 'marketplace/service.html', {'service': service})


@login_required
def deploy(request, id):
    service = Catalog_SFC.objects.get(id=id)
    list_cp = CP.objects.filter(service=service)

    if request.method == 'GET':
        formset = ACLFormset(request.GET or None)
        form = DeployForm()

    elif request.method == 'POST':
        form = DeployForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            formset = ACLFormset(request.POST)
            if formset.is_valid():
                vnffg = dict(name=data['name'], source={})
                vnffg['source']['type'] = str(data['type'])

                if request.POST['select'] == 'parameter':
                    parameter = data['parameter']
                    response = select_infrastructure(parameter)

                    if response[0] == "ERROR":
                        messages.error(request, "Error while creating VNF: " + response[1])
                        return redirect('Marketplace:deploy', id=service.id)
                    else:
                        infrastructure = response[1]
                else:
                    infrastructure = Infrastructure.objects.get(infra_id=data['infrastructure']).name
                vnffg['source']['infrastructure'] = infrastructure

                if data['type'] == 'internal':
                    origin = service.vnfs.all().first()
                    vnffg['source']['repository'] = str(origin.catalog.repository_id)
                    vnffg['source']['input'] = list_cp.get(service=service, position=0).input
                vnffg['path'] = []
                i = 0
                for vnf in service.vnfs.all():
                    insert = dict(repository=vnf.catalog.repository_id, input=list_cp.get(position=i).input,
                                  output=list_cp.get(position=i).output)
                    vnffg['path'].append(insert)
                    i += 1

                vnffg['expose_port'] = data['expose_port']

                vnffg['acl'] = {}
                for form in formset:
                    vnffg['acl'][form.cleaned_data['criterion']] = form.cleaned_data['field']

                vnffg['service_id'] = service.id

                # Creating SFC Status (Loading)
                status_service(request.user, data['name'], 'Beginning to create service')

                if sfc_create.delay(request.user.username, vnffg, data['name']):
                    return redirect('Marketplace:deployments')
                else:
                    messages.error(request)
            else:
                messages.error(request, 'error ACL Field')
        else:
            formset = None
            messages.error(request, 'Invalid Input')

    file = open(os.path.join(settings.BASE_DIR, 'docs/acl.json'), 'r')
    file = file.read()
    file = json.loads(file)
    acls = []

    for acl in file:
        file[acl]['name'] = acl
        acls.append(file[acl])

    context = {'form': form,
               'formset': formset,
               'service': service,
               'acls': acls}
    return render(request, 'marketplace/deploy.html', context)


class sfc_construct(CreateView):
    model = Catalog_SFC
    form_class = CatalogForm
    # fields = ['institution', 'sfc_name', 'category', 'version', 'price', 'full_description']
    success_url = reverse_lazy('Marketplace:index')
    template_name = 'marketplace/sfc_construct.html'

    def get_form_kwargs(self):
        kwargs = super(sfc_construct, self).get_form_kwargs()
        string = self.request.GET['vnfs']
        string = string.split(',')
        vnfs = []
        while len(string) > 0:
            vnfs.append(string[0])
            string = string[2:]
        kwargs['vnfs'] = vnfs
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(sfc_construct, self).get_context_data(**kwargs)
        if self.request.POST:
            data['vnfs'] = []
            count = int(self.request.POST.get('vnfs-count', '0'))
            for i in range(count):
                data['vnfs'].append(self.request.POST['vnf-' + str(i + 1)])
        data['title_page'] = 'Building Service'
        return data

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid Input')
        return super(sfc_construct, self).form_invalid(form)

    def form_valid(self, form):
        context = self.get_context_data()
        self.object = form.save(commit=False)
        self.object.consultant = self.request.user
        self.object.save()

        i = 0
        for vnf in context['vnfs']:
            path = VNFService.objects.create(service=self.object, catalog=Catalog.objects.get(repository_id=vnf))
            self.object.vnfs.add(path)
            CP.objects.create(service=self.object, position=i, input=self.request.POST['input' + str(i)],
                              output=self.request.POST['output' + str(i)])
            i += 1

        for afile in self.request.FILES.getlist('files'):
            pic = Print()
            pic.image = afile
            pic.catalog = self.object
            pic.save()
        return super(sfc_construct, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
class ServiceUpdate(SuccessMessageMixin, UpdateView):
    model = Catalog_SFC
    form_class = CatalogForm
    success_url = reverse_lazy('Marketplace:index')
    template_name = 'marketplace/sfc_construct.html'
    success_message = 'Serviço Atualizado'
    extra_context = {}

    def get_context_data(self, **kwargs):
        data = super(ServiceUpdate, self).get_context_data(**kwargs)
        data['title_page'] = 'Edit Service'
        return data

    def get_form_kwargs(self):
        kwargs = super(ServiceUpdate, self).get_form_kwargs()
        string = self.request.GET['vnfs']
        string = string.split(',')
        vnfs = []
        while len(string) > 0:
            vnfs.append(string[0])
            string = string[2:]
        kwargs['vnfs'] = vnfs
        return kwargs


edit_service = ServiceUpdate.as_view()


@login_required
def catalog_vnfs(request):
    """Show all available VNFs."""

    vnf_list = Catalog.objects.all()

    # Get all repositories ids acquired by the client.
    # This is used to verify if a client already bought a VNF.
    repositories_ids = [int(vnf.repository) for vnf in Acquisitions.objects.filter(client=request.user)]

    # Count the number of instances of each VNF.
    instances = {}

    # first count the number of each instantiated vnf
    for vnf in Instance.objects.filter(client=request.user):
        r_id = int(vnf.repository.repository_id)
        if r_id not in instances:
            instances[r_id] = 1
        else:
            instances[r_id] += 1

    # then, update original vnf_list with computed values
    for vnf in vnf_list:
        r_id = int(vnf.repository_id)
        if r_id not in instances:
            vnf.instances = 0
        else:
            vnf.instances = instances[r_id]

    template = loader.get_template('marketplace/catalog_vnfs.html')
    return HttpResponse(template.render(
        {
            'vnf_list': vnf_list,
            'repositories_ids': repositories_ids,
        }, request))


@login_required
def services(request):
    services = Catalog_SFC.objects.exclude(consultant=request.user)
    my_services = Catalog_SFC.objects.filter(consultant=request.user)
    return render(request, 'marketplace/services.html', {'services': services,
                                                         'my_services': my_services})


@login_required
def marketplace(request, category=None):
    """Show all available VNFs."""

    if not request.session.get('actor', False):
        request.session['actor'] = 'tenant'

    if request.session.get('actor', False) == 'consultant':
        return services(request)

    # Get all VNFs from Catalog and return it to marketplace.
    categories = Category.objects.all()
    tags = TAG.objects.all()
    if category:
        vnf_list = Catalog_SFC.objects.filter(category__name=category)
    else:
        vnf_list = Catalog_SFC.objects.all()

    q = request.GET.get('q', '')
    if q:
        vnf_list = watson.filter(vnf_list, q)

    listtags = []
    for tag in tags:
        if request.POST.get(tag.name):
            listtags.append(tag)

    if listtags:
        vnf_list = vnf_list.filter(tag__in=listtags).distinct()

    # Get all repositories ids acquired by the client.
    # This is used to verify if a client already bought a VNF.
    repositories_ids = [int(vnf.repository) for vnf in Acquisitions.objects.filter(client=request.user)]

    template = loader.get_template('marketplace.html')
    return HttpResponse(template.render(
        {
            'service_list': vnf_list,
            'repositories_ids': repositories_ids,
            'categories': categories,
            'tags': tags,
            'listtags': listtags,
            'category': category,
        }, request))


@login_required
def buy(request):
    """Adds a VNF to a client's catalog."""
    if request.method == "POST":
        repository_id = request.POST.get('repository')
        user = request.user
        acquisition = Acquisitions(
            repository=repository_id,
            client=user
        )
        try:
            acquisition.save()
            messages.success(request, "Service successfully acquired.")
        except:
            messages.error(request, "Error while acquiring Service.")
        return HttpResponse(request)


@login_required
def vnfs(request):
    """Show all acquired VNFs of a client."""

    # Get all repositories ids acquired by the client.
    repositories_ids = [vnf.repository for vnf in Acquisitions.objects.filter(client=request.user)]

    # Get all VNFs with those repositories ids.
    services = [service for service in Catalog_SFC.objects.filter(id__in=repositories_ids)]

    # Get available infrastructures
    infrastructures = [infra for infra in Infrastructure.objects.all()]

    template = loader.get_template('purchased.html')
    return HttpResponse(template.render({"services": services, "infrastructures": infrastructures}, request))


@login_required
def instances(request):
    """Show all instantiated VNFs of a client."""

    vnfs = []

    # Get all VNFs from Instance and return it to marketplace.
    active_vnfs = [vnf for vnf in Instance.objects.filter(client=request.user)]

    # Get VNF status
    for vnf in active_vnfs:
        if settings.DEV_MODE:
            vnf.status = 'false'
        else:
            infra = Infrastructure.objects.get(name=vnf.infrastructure)
            infra_info = define_infra(infra)

            if infra_info['technology'] == 'openstack':
                response = manager.vnf_status(vnf.vnf_ip, infra=infra_info)
            elif infra_info['technology'] == 'cloudstack':
                response = cloudstack_manager.vnf_status(vnf.vnf_ip, infra=infra_info)
            elif infra_info['technology'] == 'kubernetes':
                response = kubernetes_manager.vnf_status(vnf.vnf_ip, infra=infra_info)
            else:
                response = {'status': 'ERROR'}

            if response['status'] == 'ERROR':
                vnf.status = 'false'
            else:
                vnf.status = response['vnf_status']

        vnfs.append(vnf)

    catalog = []
    # todo: sql view
    for obj in active_vnfs:
        catalog.append(Catalog.objects.get(repository_id=obj.repository))
    # todo: excluir funções e template info
    # todo: testar com mais de 1 catalog
    template = loader.get_template('instances.html')
    return HttpResponse(template.render({"active_vnfs": vnfs, 'catalog': catalog}, request))


@login_required
def sfc_list(request):
    """Load SFCs information."""

    sfcs = []  # list of SFCs with status

    sfc_list = [sfc for sfc in SFC.objects.filter(client=request.user)]

    for sfc in sfc_list:
        # if SFC is already stopped, set status to inactive
        if sfc.stop_type != '':
            sfc.status = 'false'
            sfcs.append(sfc)
            continue

        vnf_ids = sfc.vnf_ids.split(',')
        path = []
        status_array = []

        # verify if SFC functions are running
        sfc.status = 'true'

        for vnf_id in vnf_ids:
            vnf = Instance.objects.get(vnf_id=vnf_id)
            infra = Infrastructure.objects.get(name=vnf.infrastructure)
            infra_info = define_infra(infra)

            if infra_info['technology'] == 'openstack':
                response = manager.vnf_status(vnf.vnf_ip, infra=infra_info)
            elif infra_info['technology'] == 'cloudstack':
                response = cloudstack_manager.vnf_status(vnf.vnf_ip, infra=infra_info)
            elif infra_info['technology'] == 'kubernetes':
                response = kubernetes_manager.vnf_status(vnf.vnf_ip, infra=infra_info)
            else:
                response = {'status': 'ERROR'}

            if response['status'] == 'ERROR':
                vnf_status = 'false'
            else:
                vnf_status = response['vnf_status']

            path.append(vnf.VNF_name)
            status_array.append(vnf_status)

        sfc.path = zip(path, status_array)

        if 'false' in status_array:
            sfc.status = 'false'

        # pretty print TOSCA VNFFGD
        raw_vnffgd = sfc.tosca_vnffgd.replace("'", "\"")
        raw_vnffgd = raw_vnffgd.replace('u\"', '\"')
        vnffgd_parsed = json.loads(raw_vnffgd)
        sfc.tosca_vnffgd = json.dumps(vnffgd_parsed, indent=2)

        # parse high-level descriptor to show ACLs
        raw_data = sfc.vnffgd
        vnffgd = raw_data.replace("'", "\"")
        vnffgd = vnffgd.replace('u\"', '\"')
        vnffgd = json.loads(vnffgd)

        criteria = [];
        value = []
        for acl in vnffgd['acl']:
            # criteria_key = acl.keys()[0].replace("u\'", "\'")
            criteria_key = acl
            criteria_description = acls[criteria_key]['description']
            criteria.append(criteria_description)
            value.append(vnffgd['acl'][acl])
        sfc.acl = zip(criteria, value)

        if vnffgd['public_port']:
            sfc.public_port = vnffgd['public_port']

        sfcs.append(sfc)

    template = loader.get_template('sfc.html')
    return HttpResponse(template.render({"sfcs": sfcs}, request))


@shared_task()
def sfc_create(username, data, current_sfc_name):
    """Create a new SFC."""

    user = User.objects.get(username=username)

    if SFC.objects.filter(client=user, name=data['name']).exists():
        status_service(user, current_sfc_name, "Name alderady exists",error=True)
        return False

    # send high-level descriptor to SFC parser
    response = sfc_compose(user, data, current_sfc_name)

    if response['status'] != 'OK':
        error_reason = response['error_reason']
        status_service(user, current_sfc_name, "Error while creating SFC: " + error_reason,error=True)
        return False

    # To get public port (NodePort) when infra is Kubernetes
    if response['public_port']:
        data['public_port'] = response['public_port']

    sfc = SFC(
        sfc=Catalog_SFC.objects.get(id=response['service_id']),
        vnffgd_id=response['vnffgd_id'],
        vnffg_id=response['vnffg_id'],
        tosca_vnffgd=response['tosca_vnffgd'],
        name=response['sfc_name'],
        client=user,
        vnf_ids=response['vnf_ids'],
        vnfds=response['vnfds'],
        stop_type='',
        vnffgd=data,
        infrastructure=data['source']['infrastructure']
    )

    try:
        sfc.save()
        # messages.success(request, "SFC successfully created.")
        status_service(user, current_sfc_name, 'SFC successfully created.',step=8)
    except Exception as e:
        # messages.error(request, "%s (%s)" % (e.message, type(e)))
        status_service(user, current_sfc_name, "%s (%s)" % (e.message, type(e)),error=True)
        return False
    return True


def sfc_compose(client, data, current_sfc_name):
    # Loading: Step 1
    """
    current_sfc = SFCStatus.objects.get(id=current_sfc_id)
    current_sfc.status = "Colleting data"
    current_sfc.step = str(int(current_sfc.step) + 1)
    current_sfc.save()
    """
    status_service(client, current_sfc_name, "Colleting data",step=1)

    """Receive a high-level descriptor and create a SFC."""

    sfc_response = {}

    # path of SFC
    path = []

    # classifiers that will be used to distinguish which traffic should enter this Forwarding Path.
    acl = data['acl']

    # VNFDs of constituent VNFs
    constituent_vnfs = []

    # List of connection points
    connection_point = []

    # List of dependent virtual links of connection points
    dependent_virtual_link = []

    # Map a VNFD with a specific instance of a VNF
    vnf_mapping = {}

    # Get all repositories ids acquired by the client.
    acquisitions = [vnf.repository for vnf in Acquisitions.objects.filter(client=client)]

    sfc_name = data['name']
    source = data['source']
    source_repo_id = ''
    source_input_cp = ''
    source_type = source['type']

    if not source['infrastructure']:
        infra = Infrastructure.objects.get(name=DEFAULT_INFRA)
    else:
        infra = Infrastructure.objects.get(name=source['infrastructure'])

    infra_info = define_infra(infra)

    if source_type == 'internal':
        source_repo_id = source['repository']
        source_input_cp = source['input']

    vnf_id = ''
    network_src_port_id = ''
    vnfd_ids = []
    vnf_names = ''

    """
    verify if traffic source is internal or external.
    if internal, create the VNF which will create traffic.
    if external, get public router id.
    """
    if source_type == 'internal':
        # verify if VNF is acquired by client
        if source_repo_id in acquisitions:
            obj = Catalog.objects.filter(repository_id=source_repo_id)[0]
            vnf_repo_name = obj.VNF_name

            # create source VNF
            response = create_vnf(source_repo_id, vnf_repo_name, unique_id(), unique_id(), client, sfc_name, infra.name,
                                  current_sfc_name)

            if response[0] == 'ERROR':
                sfc_response['status'] = 'ERROR'
                sfc_response['error_reason'] = "Error while creating VNF. " + response[1]
                return sfc_response

            vnf_id = response[1]

            vnf_origin_id = vnf_id
            vnf = Instance.objects.filter(vnf_id=vnf_id)[0]
            vnfd_ids.append(vnf.vnfd_id)
            vnf_names += vnf_repo_name + ','
        else:
            sfc_response['status'] = 'ERROR'
            sfc_response['error_reason'] = "Error while creating SFC. VNF %s not found." % source_repo_id
            return sfc_response

        # get network_src_port_id
        if infra_info['technology'] == 'openstack':
            response = manager.vnf_resources(vnf_id, infra=infra_info)
        elif infra_info['technology'] == 'cloudstack':
            response = cloudstack_manager.vnf_resources(vnf_id)
        elif infra_info['technology'] == 'kubernetes':
            response = kubernetes_manager.vnf_resources(vnf_id)
        else:
            response = {'status': 'ERROR'}

        if response['status'] != 'OK':
            sfc_response['status'] = 'ERROR'
            sfc_response['error_reason'] = "Could not get network_src_port_id: " + response['error_reason']
            return sfc_response

        resources = response['resources']

        for resource in resources:
            if resource['name'] == source_input_cp:
                network_src_port_id = resource['id']
                break

    elif source_type == 'external':
        if infra_info['technology'] == 'openstack':
            response = manager.get_network_src_port_id(infra=infra_info)
        elif infra_info['technology'] == 'cloudstack':
            response = cloudstack_manager.get_network_src_port_id(infra_info)
        elif infra_info['technology'] == 'kubernetes':
            response = kubernetes_manager.get_network_src_port_id(infra_info)
        else:
            response = {'status': 'ERROR'}

        if response['status'] != 'OK':
            sfc_response['status'] = 'ERROR'
            sfc_response['error_reason'] = "Could not get network_src_port_id: Internal Server Error"
            return sfc_response

        network_src_port_id = response['network_src_port_id']

    acl['network_src_port_id'] = network_src_port_id

    for vnf in data['path']:
        repo_id = vnf['repository']
        CP_input = vnf['input']
        CP_output = vnf['output']

        obj = Catalog.objects.filter(repository_id=repo_id)[0]
        name_id = get_name_id(obj)

        # get VNFD
        url = "%s/vnfd/%s" % (server, name_id)
        vnfd = requests.get(url, auth=auth).json()
        vnfd_data = json.loads(vnfd['vnfd_data'])
        vnfd_name = unique_id()

        constituent_vnfs.append(vnfd_name)

        if CP_input == CP_output:
            capability = [CP_input]
        else:
            capability = [CP_input, CP_output]

        for CP in capability:
            # if CP not in connection_point:
            connection_point.append(CP)

            virtual_link = vnfd_data['vnfd'] \
                ['attributes'] \
                ['vnfd'] \
                ['topology_template'] \
                ['node_templates'] \
                [CP] \
                ['requirements'] \
                [0] \
                ['virtualLink'] \
                ['node']
            dependent_virtual_link.append(virtual_link)

        if len(capability) == 1:
            capability = capability[0]
        else:
            capability = ','.join(capability)

        path.append({
            "forwarder": vnfd_name,
            "capability": capability
        })

        obj = Catalog.objects.filter(repository_id=repo_id)[0]
        vnf_repo_name = obj.VNF_name

        # Test
        vnf_name = unique_id_lower()
        # response = create_vnf(repo_id, vnf_repo_name, unique_id(), vnfd_name, client, sfc_name, infra.name)
        response = create_vnf(repo_id, vnf_repo_name, vnf_name, vnfd_name, client, sfc_name, infra.name, data['expose_port'],
                              current_sfc_name)

        if response[0] == 'ERROR':
            sfc_response['status'] = 'ERROR'
            sfc_response['error_reason'] = "Error while creating SFC: " + response[1]
            return sfc_response

        vnf_id = response[1]

        vnf_mapping[vnfd_name] = vnf_id
        vnf_i = Instance.objects.filter(vnf_id=vnf_id)[0]
        vnfd_ids.append(vnf_i.vnfd_id)
        vnf_names += vnf_repo_name + ','

    vnf_ids = ''
    # if source is internal, add VNF source id to SFC path
    if source_type == 'internal':
        vnf_ids = vnf_origin_id + ','

    vnf_ids += ','.join(vnf_mapping.values())
    vnfds = ','.join(vnf_mapping.keys())

    vnffgd_data = {
        'vnffgd_name': unique_id(),
        'vnffg_name': unique_id(),
        'acl': acl,
        'path': path,
        'connection_point': connection_point,
        'constituent_vnfs': constituent_vnfs,
        'dependent_virtual_link': dependent_virtual_link,
        'vnfd_ids': vnfd_ids,
        'vnf_ids': vnf_ids
    }
    if infra_info['technology'] == 'openstack':
        response = manager.sfc_create(vnffgd_data, vnf_mapping, infra=infra_info,user=client, current_sfc_name=current_sfc_name)
    elif infra_info['technology'] == 'cloudstack':
        response = cloudstack_manager.sfc_create(vnffgd_data, vnf_mapping, infra=infra_info)
    elif infra_info['technology'] == 'kubernetes':
        vnffgd_data['expose_port']=data['expose_port']
        response = kubernetes_manager.sfc_create(vnf_name, vnffgd_data, vnf_mapping, infra=infra_info,
                                                 user=client, current_sfc_name=current_sfc_name)
    else:
        response = {'status': 'ERROR'}

    if response['status'] != 'OK':
        # Loading: Step 8 (if error)
        """
        current_sfc = SFCStatus.objects.get(id=current_sfc_id)
        current_sfc.status = "ERROR: %s" % response['error_reason']
        current_sfc.step = str(int(current_sfc.step) + 1)
        current_sfc.save()
        """
        status_service(client, current_sfc_name, "ERROR: %s" % response['error_reason'])
        sfc_response['status'] = 'ERROR'
        sfc_response['error_reason'] = response['error_reason']
        return sfc_response

    # Loading: Step 8 (if success)
    """
    current_sfc = SFCStatus.objects.get(id=current_sfc_id)
    current_sfc.status = "Service successfully created"
    current_sfc.step = str(int(current_sfc.step) + 1)
    current_sfc.save()
    """
    status_service(client, current_sfc_name, "Service successfully created")
    sfc_response = {
        'status': 'OK',
        'service_id': data['service_id'],
        'vnffgd_id': response['vnffgd_id'],
        'vnffg_id': response['vnffg_id'],
        'tosca_vnffgd': response['vnffgd'],
        'sfc_name': sfc_name,
        'client': client,
        'vnf_ids': vnf_ids,
        'vnfds': vnfds
    }

    if infra_info['technology'] == 'kubernetes':
        sfc_response['public_port'] = response['public_port']

    return sfc_response


def define_infra(infra):
    """Build infrastructure credentials."""
    if infra.technology == "openstack":
        return {
            'id': infra.infra_id,
            'infra_name': infra.name,
            'tenant_name': infra.tenant,
            'username': infra.username,
            'password': AESCipher(pwd).decrypt(str(infra.password)),
            'ip': infra.ip,
            'gateway_port': infra.gateway_port,
            'technology': infra.technology
        }
    elif infra.technology == "cloudstack":
        return {
            'id': infra.infra_id,
            'infra_name': infra.name,
            'zone_id': infra.zone_id,
            'host_id': infra.host_id,
            'api_key': infra.api_key,
            'secret_key': infra.secret_key,
            'ip': infra.ip,
            'gateway_port': infra.gateway_port,
            'technology': infra.technology
        }
    else:
        return {
            'id': infra.infra_id,
            'infra_name': infra.name,
            'token': infra.token,
            'ip': infra.ip,
            'gateway_port': infra.gateway_port,
            'technology': infra.technology
        }


def create_vnf(repository_id, vnf_repo_name, vnf_name, vnfd_name, user, sfc_member, infrastructure_name, expose_port,
               current_sfc_name):
    """Get descriptor and VNF function from local repository and instantiate the VNF."""

    # Search repository and generate the name_id.
    obj = Catalog.objects.filter(repository_id=repository_id)[0]
    name_id = get_name_id(obj)

    if infrastructure_name == 'Default':
        infrastructure_name = DEFAULT_INFRA

    infra = Infrastructure.objects.get(name=infrastructure_name)
    infra_info = define_infra(infra)

    # get VNFD
    url = "%s/vnfd/%s" % (server, name_id)
    vnfd = requests.get(url, auth=auth).json()
    vnfd_data = json.loads(vnfd['vnfd_data'])
    vnfd_data['vnfd']['name'] = vnfd_name
    vnfd_data['vnfd']['attributes']['vnfd']['topology_template']['node_templates']['VDU1']['properties'][
        'name'] = unique_id()
    os_type = vnfd_data['vnfd']['attributes']['vnfd']['topology_template']['node_templates']['VDU1']['properties'][
        'image']

    # verify if the user has a SSH key on the specified infrastructure
    # if it does, update VNFD with SSH key name
    if infra_info['technology'] == 'openstack':
        response = manager.get_ssh_key(user.username, infra=infra_info)
    elif infra_info['technology'] == 'cloudstack':
        response = cloudstack_manager.get_ssh_key(user.username, infra=infra_info)
    elif infra_info['technology'] == 'kubernetes':
        response = kubernetes_manager.get_ssh_key(user.username, infra=infra_info)
    else:
        response = {'status': 'ERROR'}

    if response['status'] == 'OK':
        vnfd_data['vnfd']['attributes']['vnfd']['topology_template']['node_templates']['VDU1']['properties'][
            'key_name'] = user.username

    function_data = ''

    # get VNF function
    # if VNF is click-on-osv based, send click function
    # otherwise, send the entire repository
    if os_type == 'click-on-osv':
        url = "%s/vnf/function/%s" % (server, name_id)
        function = requests.get(url, auth=auth).json()
        function_data = function['function_data']
    elif os_type == 'ubuntu-18.10':
        url = "%s/vnf/repository/%s" % (server, name_id)
        function = requests.get(url, auth=auth).json()
        # open repository zip in binary to send to VNFM
        function_data = function['repository_path']

        # force DHCP on second interface (ens4)
        vnfd_data['vnfd']['attributes']['vnfd']['topology_template']['node_templates']['VDU1']['properties'][
            'user_data_format'] = 'RAW'
        vnfd_data['vnfd']['attributes']['vnfd']['topology_template']['node_templates']['VDU1']['properties'][
            'user_data'] = """
        #!/bin/sh
        /sbin/dhclient ens4;
        """
    else:
        error_reason = 'Invalid VNF OS type.'
        return ("ERROR", error_reason)

    if not function_data:
        error_reason = "Could not get VNF function."
        return ("ERROR", error_reason)

    if infra_info['technology'] == 'openstack':
        response = manager.vnf_create(json.dumps(vnfd_data), os_type, vnf_name, function_data, infra=infra_info,
                                      user=user, current_sfc_name=current_sfc_name)
    elif infra_info['technology'] == 'cloudstack':
        response = cloudstack_manager.vnf_create(json.dumps(vnfd_data), os_type, vnf_name, function_data,
                                                 infra=infra_info, current_sfc_name=current_sfc_name)
    elif infra_info['technology'] == 'kubernetes':
        response = kubernetes_manager.vnf_create(json.dumps(vnfd_data), os_type, vnf_name, function_data,
                                                 infra=infra_info, expose_port=expose_port, user=user, current_sfc_name=current_sfc_name)
    else:
        response = {'status': 'ERROR'}

    if response['status'] != 'OK':
        error_reason = response['error_reason']
        return ("ERROR", error_reason)

    new_vnf = Instance(
        vnf_id=response['vnf_id'],
        repository=Catalog.objects.get(repository_id=repository_id),
        client=user,
        vnfd_id=response['vnfd_id'],
        vnf_ip=response['vnf_ip'],
        VNF_name=vnf_repo_name,
        sfc_member=sfc_member,
        infrastructure=infra.name
    )
    try:
        new_vnf.save()
        status = ("OK", response['vnf_id'])
    except:
        status = ("ERROR", "Error while saving VNF instance on database.")

    return status


def show_vnfd(request):
    if request.method == "POST":
        repository_id = request.POST.get('repository')

        obj = Catalog.objects.filter(repository_id=repository_id)[0]
        name_id = get_name_id(obj)

        # get vnfd
        url = "%s/vnfd/%s" % (server, name_id)
        vnfd = requests.get(url, auth=auth).json()
        vnfd_data = vnfd['vnfd_data' + repository_id]

        return HttpResponse(vnfd_data, request)


def select_infrastructure(param):
    """Based on a parameter, select the best infrastructure to deploy the VNF.
    param options: cpu, mem, bandwidth
    """

    # stores the infrastructure ID and its parameter value
    resource_usage = {}

    # get all public infrastructures
    infrastructures = Infrastructure.objects.filter(permission='public')

    # for every infrastructure available, collect and stores the resource_usage value
    for infra in infrastructures:
        infrastructure = define_infra(infra)
        if infrastructure['technology'] == 'openstack':
            resource_value = manager.get_resource_usage(infrastructure, param)
        elif infrastructure['technology'] == 'cloudstack':
            resource_value = cloudstack_manager.get_resource_usage(infrastructure, param)
        elif infrastructure['technology'] == 'kubernetes':
            resource_value = kubernetes_manager.get_resource_usage(infrastructure, param)
        else:
            response = {'status': 'ERROR'}

        if resource_value:
            resource_usage[infra.infra_id] = resource_value

    # returns an error if no infrastructure can be selected
    if not len(resource_usage):
        response = ("ERROR", "No infrastructure available.")
        return response

    best_infra_id = None

    # based on param, get the best value on the resource usage dictionary
    if param in ['CPU', 'BW']:
        best_infra_id = min(resource_usage, key=resource_usage.get)
    elif param == 'MEM':
        best_infra_id = max(resource_usage, key=resource_usage.get)
    elif param == 'LAT':
        pass

    placement = Infrastructure.objects.get(infra_id=best_infra_id)

    return ("OK", placement.name)


@login_required
def remove(request, id):
    """Create a VNF from a available repository.

    This function will create a VNF through VNF Manager module and
    will add its information to Instance table.
    """
    Acquisitions.objects.get(repository=id).delete()
    messages.success(request, "VNF successfully retorned to Catalog.")

    return redirect("Marketplace:vnfs")


@login_required
def get_log(request, vnf_id):
    """Get VNF logs."""

    vnf = Instance.objects.get(vnf_id=vnf_id)
    infra = Infrastructure.objects.filter(name=vnf.infrastructure)[0]
    infra_info = define_infra(infra)
    if infra_info['technology'] == 'openstack':
        response = manager.get_log(vnf.vnf_ip, infra=infra_info)
    elif infra_info['technology'] == 'cloudstack':
        response = cloudstack_manager.get_log(vnf.vnf_ip, infra=infra_info)
    elif infra_info['technology'] == 'kubernetes':
        response = kubernetes_manager.get_log(vnf.vnf_ip, infra=infra_info)
    else:
        response = {'status': 'ERROR'}

    if response['status'] != 'OK':
        error_reason = response['error_reason']
        messages.error(request, "Error while getting log: " + error_reason)
        return HttpResponse(request)

    log = str(response['log'])

    if log != 'None':
        log = log.replace('\\n', '<br>')
    else:
        log = "Start the VNF to open the logs"

    back = reverse('Marketplace:instances')
    return render(request, 'logs.html', {'response': log, 'vnf_id': vnf_id, 'BACK': back})


@login_required
def info(request):
    """Shows detailed info of a VNF."""

    url = request.path.split('/')
    vnf_id = url[-1]
    template = loader.get_template('info.html')
    instance = Instance.objects.filter(client=request.user, vnf_id=vnf_id)
    for obj in instance:
        catalog = Catalog.objects.filter(repository_id=obj.repository)
    return HttpResponse(template.render({'instance': instance, 'catalog': catalog}, request))


@login_required
def statistics(request):
    """Shows VNF statistics."""

    url = request.path.split('/')
    vnf_id = url[-1]
    template = loader.get_template('statistics.html')
    instance = Instance.objects.filter(client=request.user, vnf_id=vnf_id)

    for obj in instance:
        catalog = Catalog.objects.filter(repository_id=obj.repository)

    back = reverse('Marketplace:instances')
    return HttpResponse(template.render({"vnf_id": vnf_id, "catalog": catalog, 'BACK': back}, request))


@login_required
def sfc_path(request):
    import re
    descriptor = {'memory': 0, 'disk': 0, 'cpu': 0}
    """ Show Visualization with SFC path """
    url = request.path.split('/')
    fg = url[-1]
    service = SFC.objects.get(client=request.user, vnffg_id=fg)
    ids = service.vnf_ids
    repository_ids = ids.split(',')
    # repository_ids = ['7574dc0e-d9fe-4f3f-b53b-eb504274f8a1','dc966621-8615-4b84-899d-95df1873a0df']
    repositories = Instance.objects.filter(vnf_id__in=repository_ids)
    for instance in repositories:
        obj = instance.repository
        name_id = get_name_id(obj)
        url = "%s/vnfd/%s" % (server, name_id)
        vnfd = requests.get(url, auth=auth).json()['vnfd_data']
        vnfd = json.loads(vnfd)
        propriedades = \
            vnfd['vnfd']['attributes']['vnfd']['topology_template']['node_templates']['VDU1']['capabilities'][
                'nfv_compute']['properties']
        memory = int(re.findall(r'\d+', propriedades['mem_size'])[0])
        disk = int(re.findall(r'\d+', propriedades['disk_size'])[0])
        descriptor['memory'] += memory
        descriptor['disk'] += disk
        descriptor['cpu'] += propriedades['num_cpus']
    # calculo de mb to gb
    if descriptor['memory'] > 1023:
        descriptor['memory'] = str(round(descriptor['memory'] / 1024, 2)) + ' Gb'
    else:
        descriptor['memory'] = str(descriptor['memory']) + ' Mb'
    # adicionado metricas
    descriptor['disk'] = str(descriptor['disk']) + ' Gb'
    descriptor['cpu'] = str(descriptor['cpu']) + ' Core'
    template = loader.get_template('sfc_path.html')
    return HttpResponse(template.render(
        {"sfc": repositories, 'service': service, 'descriptor': descriptor, 'auth': {'server': server, 'auth': auth}},
        request))


@login_required
def tutorial(request, tutorial):
    return render(request, 'tutorial/%s.html' % tutorial)


@login_required
def infra_update(request, id):
    infra = Infrastructure.objects.get(infra_id=id)
    if request.method == 'POST':
        form = InfrastructureForm(request.POST, instance=infra)
        if form.is_valid():
            form.save()
            messages.success(request, 'Infrastructure has been saved!')
            return redirect('Marketplace:infrastructure_list')
    else:
        form = InfrastructureForm(instance=infra)
        print(form.fields['password'])
    return render(request, 'infras/update.html', {'form': form})


@login_required
def infra_list(request):
    infras = Infrastructure.objects.all()
    return render(request, 'infras/list.html', {'list': infras})


@login_required
def infrastructure_form(request):
    if request.method == "POST":
        form = InfrastructureForm(request.POST)
        if form.is_valid():
            submit = form.save(commit=False)

            # OPENSTACK
            if submit.technology == 'openstack':
                credentials = {
                    'tenant_name': submit.tenant,
                    'username': submit.username,
                    'password': submit.password,
                    'ip': submit.ip
                }
                # todo: nao esta usando credentials?
                cypher = AESCipher(pwd).encrypt(str(submit.password))
                submit.password = cypher

            # CLOUDSTACK
            elif submit.technology == 'cloudstack':
                credentials = {
                    'zone_id': submit.zone_id,
                    'host_id': submit.host_id,
                    'api_key': submit.api_key,
                    'secret_key': submit.secret_key,
                    'ip': submit.ip
                }

                response = cloudstack_manager._auth(credentials)
                if response['status'] == 'ERROR':
                    messages.error(request, "Error while registering infrastructure: " + response['error_reason'])
                    return render(request, 'infrastructure.html', {'form': form})

            # KUBERNETES
            elif submit.technology == 'kubernetes':
                credentials = {
                    'token': submit.token,
                    'ip': submit.ip,
                    'gateway_port': submit.gateway_port
                }

                response = kubernetes_manager._auth(credentials)
                if response['status'] == 'ERROR':
                    messages.error(request, "Error while registering infrastructure: " + response['error_reason'])
                    return render(request, 'infrastructure.html', {'form': form})

            submit.owner = request.user
            submit.save()
            messages.success(request, "Infrastructure successfully registered.")
            return redirect('Marketplace:infrastructure_list')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, field.label + ': ' + error)
    else:
        form = InfrastructureForm()
    return render(request, 'infrastructure.html', {'form': form})


def change_json(json_data, key, value):
    if key != 'num_cpus':
        value = '"' + value + '"'
    return (string.replace(json_data, '"' + key + '": "CHANGE"', '"' + key + '": ' + value))


def json_cp(key, node, network_name, index):
    # Le json template
    json_data = open(settings.PROJECT_ROOT + '/storage/temp_json/CP_.json', mode='r').read()
    json_data = string.replace(json_data, 'CP_CHANGE', key)
    json_data = string.replace(json_data, '"order": "CHANGE"', '"order": ' + index)
    json_data = string.replace(json_data, '"node": "CHANGE"', '"node": "' + node + '"')
    json_data = string.replace(json_data, '"network_name": "CHANGE"', '"network_name": "' + network_name + '"')
    json_data = string.replace(json_data, 'CHANGE', node)
    return str(json_data)


def form_json(request):
    req = request.POST

    # Dados padrões
    dados = {
        'image': "ubuntu-18.10",
        'CP_mgmt': {
            'node': 'VL' + str(random.getrandbits(64)),
            'network_name': "net_mgmt"
        }
    }

    num_cpus = [1, 2, 4, 8]
    disk_size = ['1 Gb', '5 Gb', '10 Gb', '50 Gb', '100 Gb']
    mem_size = ['512 Mb', '1024 Mb', '2048 Mb', '4096 Mb', '8192 Mb']
    for data in req:
        # Adiciona CP_traffic se checked
        if (data == 'CP_traffic'):
            dados['CP_traffic'] = {
                'node': 'VL' + str(random.getrandbits(64)),
                'network_name': "private"
            }
        else:
            dados[data.encode('utf8')] = req[data].encode('utf8')

    # Remove o token da lista
    del dados['csrfmiddlewaretoken']

    # Retorna valor real dos dados
    dados['num_cpus'] = str(num_cpus[int(dados['num_cpus'])])
    dados['disk_size'] = str(disk_size[int(dados['disk_size'])])
    dados['mem_size'] = str(mem_size[int(dados['mem_size'])])

    # Le json template
    json_data = open(settings.PROJECT_ROOT + '/storage/temp_json/vnfd.json', mode='r').read()

    # Altera dado do json
    for index, dado in enumerate(dados):
        if 'CP_' in dado:
            cp_traffic = json_cp(dado, dados[dado]['node'], dados[dado]['network_name'], str(index))
            cp_traffic += ', "CP_CHANGE"'
            json_data = string.replace(json_data, '"CP_CHANGE"', cp_traffic)
        else:
            json_data = change_json(json_data, dado, dados[dado])

    json_data = string.replace(json_data, ', "CP_CHANGE"', '')

    return JsonResponse(json.loads(json_data))


# Deployments
@login_required
def deployments(request):
    services = SFCStatus.objects.filter(client=request.user)
    return render(request, 'marketplace/deployments.html', {'deployments': services})
