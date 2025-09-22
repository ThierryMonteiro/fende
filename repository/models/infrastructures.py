#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone
from accounts.models import User

Permissions = (
    ('public', 'Public'),
    ('private', 'Private'),
)

Technologies = (
    ('openstack', 'OpenStack'),
    ('cloudstack', 'CloudStack'),
    ('kubernetes', 'Kubernetes'),
    ('libvirt', 'Libvirt'),
    ('others', 'Others'),
)


class Infrastructure(models.Model):
    infra_id = models.AutoField(primary_key=True)  # Chave
    name = models.CharField(max_length=32, unique=True)  # Nome da infraestrutura
    ip = models.CharField(max_length=32)  # IP da infraestrutura
    gateway_port = models.CharField(max_length=32, blank=True, default='9000')  # Porta do FENDE gateway da infraestrutura
    owner = models.ForeignKey(User)  # Dono da infraestrutura (User)
    technology = models.CharField(max_length=30,
                                  choices=Technologies)  # Tecnologia sendo utilizada pela infraestrutura (e.g., Openstack)
    permission = models.CharField(max_length=30, choices=Permissions)  # Permissões de uso da Infraestrutura
    tenant = models.CharField(max_length=32, blank=True, null=True)  # Credencial para logar no openstack
    username = models.CharField(max_length=32, blank=True, null=True)  # Credencial para logar no openstack
    password = models.CharField(max_length=999, blank=True, null=True)  # Credencial para logar no openstack
    zone_id = models.CharField(max_length=999, blank=True, null=True)  # Credencial para logar no Cloudstack
    host_id = models.CharField(max_length=999, blank=True, null=True)  # Credencial para logar no Cloudstack
    api_key = models.CharField(max_length=999, blank=True, null=True)  # Credencial para logar no Cloudstack
    secret_key = models.CharField(max_length=999, blank=True, null=True)  # Credencial para logar no Cloudstack
    token = models.CharField(max_length=999, blank=True, null=True)  # Credencial para logar no Kubernetes
    created_date = models.DateTimeField(auto_now_add=True)  # Data

    def __unicode__(self):
        return '%s-%s' % (self.name, self.owner)
