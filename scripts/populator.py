# -*- coding: utf-8 -*-
# !/usr/bin/env python

from repository.models import *
from django.contrib.auth.models import Group
from accounts.models import Institution
from marketplace.models import *
import requests
import os

from marketplace.views import AESCipher

#############  GENERAL CONFIG #############
# AES Settings
BLOCK_SIZE = 16  # Bytes
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]
pwd = "43!91$%82947mff320148rs1048210#@"

# INSTUTIONS
UFSM = Institution.objects.create(name='UFSM')
UFRGS = Institution.objects.create(name='UFRGS')
UFPR = Institution.objects.create(name='UFPR')
UNICAMP = Institution.objects.create(name='UNICAMP')
UZH = Institution.objects.create(name='UZH')
OTHER = Institution.objects.create(name='Other')

users = [
    {
        'username': 'gt-fende',
        'password': 'rnp#12345',
        'email': 'gt-fende@gt-fende.com',
        'is_superuser': True,
        'institution': UFRGS
    },
    {
        'username': 'developer',
        'password': '123',
        'email': 'developer@gt-fende.com',
        'is_superuser': False,
        'institution': UFRGS
    },
    {
        'username': 'reviewer',
        'password': '123',
        'email': 'reviewer@gt-fende.com',
        'is_superuser': False,
        'institution': UFRGS
    },
    {
        'username': 'tenant',
        'password': '123',
        'email': 'tenant@gt-fende.com',
        'is_superuser': False,
        'institution': UFRGS
    },
    {
        'username': 'consultant',
        'password': '123',
        'email': 'consultant@gt-fende.com',
        'is_superuser': False,
        'institution': UFRGS
    }
]

groups = ['Developer', 'Reviewer', 'Tenant', 'Consultant']

repository_test_pub = 'https://github.com/giovannivenancio/firewall_test'
repository_test_pr = ''

# API Rest CONFIG (Necessario para forcar o clone dos repositorios)
server = "http://localhost:5000"
auth = ("f&=gAt&ejuTHuqUKafaKe=2*", "bUpAnebeC$ac@4asaph#DrEb")

##########################################

# Cria super usuario, developer, reviewer e tenant.
for user in users:
    # verifica se usuario ja existe
    if User.objects.filter(username=user['username']).exists():
        print
        '\nUsername "%s" is already in use.' % user['username']
    else:
        new_user = User.objects.create_user(user['username'], password=user['password'], email=user['email'],
                                            institution=user['institution'])
        new_user.is_superuser = user['is_superuser']
        new_user.is_staff = user['is_superuser']
        new_user.save()

# Seleciona os usuarios
admin = User.objects.get(username='gt-fende')
developer = User.objects.get(username='developer')
reviewer = User.objects.get(username='reviewer')
tenant = User.objects.get(username='tenant')
consultant = User.objects.get(username='consultant')

# Cria os grupos e adiciona os respectivos usuarios aos grupos.
for group in groups:
    new_group, created = Group.objects.get_or_create(name=group)

developer_group = Group.objects.get(name='Developer')
developer_group.user_set.add(admin)
developer_group.user_set.add(developer)

reviewer_group = Group.objects.get(name='Reviewer')
reviewer_group.user_set.add(admin)
reviewer_group.user_set.add(reviewer)

tenant_group = Group.objects.get(name='Tenant')
tenant_group.user_set.add(admin)
tenant_group.user_set.add(tenant)

consultant_group = Group.objects.get(name='Consultant')
consultant_group.user_set.add(admin)
consultant_group.user_set.add(consultant)


# Funcoes auxiliares para chamada da API.
def create_repository(name_id, url):
    url = "%s/repository/create/%s/%s" % (server, name_id, url)
    requests.get(url, auth=auth)


def vnfd_update(name_id):
    os.system(
        'cp /var/lib/fende/%s/Descriptors/vnfd.json /var/lib/fende/%s/Descriptors/new_vnfd.json' % (name_id, name_id))


# Inicio do Populator

# Database eraser
Request.objects.all().delete()
RequestVNFD.objects.all().delete()
Catalog.objects.all().delete()
Permission.objects.all().delete()
Version.objects.all().delete()

# Categories
protection = Category.objects.create(name='Protection')
control = Category.objects.create(name='Control')
interoperability = Category.objects.create(name='Interoperability')
application = Category.objects.create(name='Application')
optimization = Category.objects.create(name='Optimization')

# Submissão de repostórios (Repositórios que ficarão na lista de revisões)
under_review = Request(tag='New', review_tag="To Review", developer=admin, institution=UFRGS, VNF_name='NAT',
                       version='1.0', category=application, abstract='Network Address Translator',
                       full_description='A principal função de um NAT é mapear endereços de rede internos',
                       link=repository_test_pub)
under_review.save()

under_review = Request(tag='Update', review_tag="To Review", developer=admin, institution=UFPR, VNF_name='Firewall',
                       version='1.4', category=protection,
                       abstract='Um Firewall de alta performance baseado em IP Tables',
                       full_description='Um Firewall baseado em IP Tables com suporte a diferentes políticas de segurança e interface com usuário. Nesta versão foi adicionado o suporte para múltiplos administradores',
                       link=repository_test_pub)
under_review.save()

under_review = Request(tag='New', review_tag="To Review", developer=admin, institution=UFRGS,
                       VNF_name='Video Transcoder', version='1.0', category=optimization,
                       abstract='Otimização para processamento de video',
                       full_description='Video transcoder otimiza o processamento de videos utilizando grande quantidade de processamento remoto',
                       link=repository_test_pub)
under_review.save()

under_review = Request(tag='New', review_tag="To Review", developer=admin, institution=UFSM, VNF_name='DHCP',
                       version='2.0', category=application, abstract='Basic Dynamic Host Configuration Protocol',
                       full_description='oferece configuração dinâmica de terminais, com concessão de endereços IP de host, máscara de sub-rede, default gateway (gateway padrão), número IP de um ou mais servidores DNS, sufixos de pesquisa do DNS e número IP de um ou mais servidores',
                       link=repository_test_pub)
under_review.save()

reviewed = Request(tag='New', review_tag="Accepted", developer=admin, institution=UFRGS, VNF_name='DPI',
                   version='1.0', category=protection, abstract='Deep Packet Inspection',
                   full_description='Ferramenta para segurança de redes com elevado poder para analisar pacotes que trafegam entre a rede e a internet',
                   link=repository_test_pub)
reviewed.save()

reviewed = Request(tag='New', review_tag="Accepted", developer=admin, institution=UFSM, VNF_name='Load Balancer',
                   version='3.0', category=interoperability, abstract='Balanceador de Carga',
                   full_description='Todo o tráfego é direcionado para um IP do provedor contratado e este é distribuido através da internet ou de rede local para os servidores de destino. Está versão utiliza técnicas de inteligência artificial para otimização do balanceamento de carga.',
                   link=repository_test_pub)
reviewed.save()

reviewed = Request(tag='New', review_tag="Accepted", developer=admin, institution=UFPR, VNF_name='Firewall',
                   version='1.3', category=protection, abstract='Um Firewall baseado em IP Tables',
                   full_description='Um Firewall baseado em IP Tables com suporte a diferentes políticas de segurança e interface com usuário',
                   link=repository_test_pub)
reviewed.save()

# Infraestruturas
infra = Infrastructure(name='UFPR (Default)', ip='200.17.202.200',
                       owner=admin,
                       technology='openstack', permission='public', tenant='admin', username='admin',
                       password=AESCipher(pwd).encrypt(str('gtfendernp')))
infra.save()

infra = Infrastructure(name='UFSM', ip='200.18.45.126',
                       owner=admin,
                       technology='openstack', permission='public', tenant='admin', username='admin',
                       password=AESCipher(pwd).encrypt(str('gtfendernp')))
infra.save()

infra = Infrastructure(name='POP-RS', ip='200.132.1.35',
                       owner=admin,
                       technology='openstack', permission='public', tenant='admin', username='admin',
                       password=AESCipher(pwd).encrypt(str('gtfendernp')))
infra.save()

# Catalog (Repositórios que ficarão disponíveis na marketplace)
catalog1 = Catalog(developer=admin, institution='UFRGS', VNF_name='DPI', version='1.0', category=protection,
                   abstract='Deep Packet Inspection',
                   full_description='Ferramenta para segurança de redes com elevado poder para analisar pacotes que trafegam entre a rede e a internet',
                   link=repository_test_pub)
catalog1.save()
name_id = 'DPI-1.0-gt-fende'
create_repository(name_id, repository_test_pub)

catalog2 = Catalog(developer=admin, institution='UFSM', VNF_name='Load Balancer', version='3.0', category=control,
                   abstract='Balanceador de Carga',
                   full_description='Todo o tráfego é direcionado para um IP do provedor contratado e este é distribuido através da internet ou de rede local para os servidores de destino. Está versão utiliza técnicas de inteligência artificial para otimização do balanceamento de carga.',
                   link=repository_test_pub)
catalog2.save()
name_id = 'LoadBalancer-3.0-gt-fende'
create_repository(name_id, repository_test_pub)

catalog3 = Catalog(developer=admin, institution='UFPR', VNF_name='Firewall', version='1.3', category=protection,
                   abstract='Um Firewall baseado em IP Tables',
                   full_description='Um Firewall baseado em IP Tables com suporte a diferentes políticas de segurança e interface com usuário',
                   link=repository_test_pub)
catalog3.save()
name_id = 'Firewall-1.3-gt-fende'
create_repository(name_id, repository_test_pub)

repository_test_sfc = 'https://github.com/giovannivenancio/vnfp1'
catalog4 = Catalog(developer=admin, institution='UFPR', VNF_name='SFC1', version='1.0', category=interoperability,
                   abstract='SFC 1', full_description='SFC 1', link=repository_test_sfc)
catalog4.save()
name_id = 'SFC1-1.0-gt-fende'
create_repository(name_id, repository_test_sfc)

repository_test_sfc = 'https://github.com/giovannivenancio/vnfp2'
catalog5 = Catalog(developer=admin, institution='UFPR', VNF_name='SFC2', version='1.0', category=interoperability,
                   abstract='SFC 2', full_description='SFC 2', link=repository_test_sfc)
catalog5.save()
name_id = 'SFC2-1.0-gt-fende'
create_repository(name_id, repository_test_sfc)

repository_test_sfc = 'https://github.com/giovannivenancio/vnfp3'
catalog6 = Catalog(developer=admin, institution='UFPR', VNF_name='SFC3', version='1.0', category=interoperability,
                   abstract='SFC 3', full_description='SFC 3', link=repository_test_sfc)
catalog6.save()
name_id = 'SFC3-1.0-gt-fende'
create_repository(name_id, repository_test_sfc)

repository_test = 'https://github.com/murielfranco/ad_repository'
catalog7 = Catalog(developer=admin, institution='UZH', VNF_name='AdBlocker', version='1.0', category=protection,
                   abstract='A blackhole for unwanted advertising',
                   full_description='A blackhole for unwanted advertising', link=repository_test)
catalog7.save()
name_id = 'AdBlocker-1.0-gt-fende'
create_repository(name_id, repository_test)

repository_test = 'https://github.com/murielfranco/firewall_repository'
catalog8 = Catalog(developer=admin, institution='UZH', VNF_name='Firewall Premium API', version='1.0',
                   category=protection,
                   abstract='A Firewall with an integrated API',
                   full_description='A Firewall with an integrated API to add and manage rules', link=repository_test)
catalog8.save()
name_id = 'FirewallPremiumAPI-1.0-gt-fende'
create_repository(name_id, repository_test)

repository_test = 'https://github.com/giovannivenancio/vnf-click'
catalog9 = Catalog(developer=admin, institution='UFPR', VNF_name='VNF-Click', version='1.0', category=interoperability,
                   abstract='A simple forwarder', full_description='A simple forwarder', link=repository_test)
catalog9.save()
name_id = 'VNF-Click-1.0-gt-fende'
create_repository(name_id, repository_test)

# Version (Versionamento de VNFs disponíveis)
version = Version(developer=admin, institution='UFSM', VNF_name='Load Balancer', version='1.0',
                  category='Interoperability',
                  abstract='Balanceador de Carga', full_description='Balanceador de Carga com funcionalidades básicas',
                  link=repository_test_pub)
version.save()
name_id = 'LoadBalancer-1.0-gt-fende'
create_repository(name_id, repository_test_pub)

version = Version(developer=admin, institution='UFSM', VNF_name='Load Balancer', version='2.0',
                  category='Interoperability',
                  abstract='Balanceador de Carga',
                  full_description='Todo o tráfego é direcionado para um IP do provedor contratado e este é distribuido através da internet ou de rede local para os servidores de destino',
                  link=repository_test_pub)
version.save()
name_id = 'LoadBalancer-2.0-gt-fende'
create_repository(name_id, repository_test_pub)

# VNFD update request
vnfd = RequestVNFD(review_tag='To Review', developer=admin, institution='UFPR', VNF_name='Firewall', version='1.3',
                   category='Protection', abstract='Um Firewall baseado em IP Tables', link=repository_test_pub,
                   details='Foi alterado a quantidade de memória necessária para rodar a VNF. Essa alteração se dá em função da análise de desempenho realizada por nossos especialistas')
vnfd.save()
name_id = 'Firewall-1.3-gt-fende'
vnfd_update(name_id)

vnfd = RequestVNFD(review_tag='Rejected', developer=admin, institution='UFSM', VNF_name='Load Balancer', version='2.0',
                   category='Interoperability', abstract='Balanceador de Carga', link=repository_test_pub,
                   details='Foi alterado a quantidade de memória necessária para rodar a VNF. Essa alteração se dá em função da análise de desempenho realizada por nossos especialistas',
                   comments="As alterações realizadas geram um comportamento inesperado e nocivo para nossos servidores. Recomendo que avalie novamente suas necessidades e se necessário entre em contato com nossa equipe técnica via email (fende@rnp.br)")
vnfd.save()

# Politicas
permission = Permission(VNF='DPI-1.0-gt-fende', code_source="none", contract_vnf="all")
permission.save()

permission = Permission(VNF='Firewall-1.3-gt-fende', code_source="all", contract_vnf="all")
permission.save()

permission = Permission(VNF='LoadBalancer-3.0-gt-fende', code_source="none", contract_vnf="all")
permission.save()

permission = Permission(VNF='LoadBalancer-2.0-gt-fende', code_source="none", contract_vnf="UFSM")
permission.save()

permission = Permission(VNF='AdBlocker-1.0-gt-fende', code_source="none", contract_vnf="all")
permission.save()

permission = Permission(VNF='FirewallPremiumAPI-1.0-gt-fende', code_source="none", contract_vnf="UFSM")
permission.save()

# tags
TAG.objects.create(name='UFSM')
TAG.objects.create(name='UFRGS')

############ CREATE SERVICE ##################

# # SERVICE
sfc = Catalog_SFC.objects.create(consultant=admin, institution='UFSM', sfc_name='Service 1', category=protection,
                                 version='1.0',
                                 price=100.00, full_description='Descricao Completa')

# TAG SERVICE
sfc.tag.add(TAG.objects.get(name='UFSM'))

# PATH SERVICE
vnfservice = VNFService.objects.create(catalog=catalog1, service=sfc)
sfc.vnfs.add(vnfservice)
vnfservice = VNFService.objects.create(catalog=catalog2, service=sfc)
sfc.vnfs.add(vnfservice)
vnfservice = VNFService.objects.create(catalog=catalog3, service=sfc)
sfc.vnfs.add(vnfservice)
sfc.save()

# CPs PATH
CP.objects.create(service=sfc, position=0, input='CP22',
                  output='CP22')
CP.objects.create(service=sfc, position=1, input='CP22',
                  output='CP22')
CP.objects.create(service=sfc, position=2, input='CP22',
                  output='CP22')

# PRINTS SERVICE
Print.objects.create(catalog=sfc, image='/static/img/logos/aveiro.png')
Print.objects.create(catalog=sfc, image='/static/img/logos/gent.png')
Print.objects.create(catalog=sfc, image='/static/img/logos/rnp.png')
Print.objects.create(catalog=sfc, image='/static/img/logos/ufpr.png')
Print.objects.create(catalog=sfc, image='/static/img/logos/ufrgs.png')
Print.objects.create(catalog=sfc, image='/static/img/logos/unicamp.png')

############ END CREATE SERVICE ##################
