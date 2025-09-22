#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone

from repository.models import Catalog


class Instance(models.Model):
    vnf_id = models.CharField(max_length=40)  # Chave
    repository = models.ForeignKey(Catalog, on_delete=models.CASCADE)  # ID do repositório (Catalog)
    client = models.CharField(max_length=64)  # Dono da instância (User)
    vnfd_id = models.CharField(max_length=64)  # ID do VNFD utilizado (Openstack)
    vnf_ip = models.CharField(max_length=16)  # IP da VNF (Openstack)
    created_date = models.DateTimeField(default=timezone.now)  # Data
    VNF_name = models.CharField(max_length=50)  # Nome da VNF (Catalog)
    sfc_member = models.CharField(max_length=32, blank=True, null=True,
                                  default='None')  # Nome do SFC do qual faz parte (SFC)
    infrastructure = models.CharField(max_length=32,
                                      default='')  # Nome da infraestrutura (Infrastructure) no qual está rodando

    def __unicode__(self):
        return '%s' % (self.VNF_name)
