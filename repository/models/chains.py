#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone

from accounts.models import User


class SFC(models.Model):
    sfc = models.ForeignKey('marketplace.Catalog_SFC', on_delete=models.SET_NULL, default=1, null=True)
    vnffgd_id = models.CharField(max_length=32)  # Chave
    vnffg_id = models.CharField(max_length=32)  # Chave
    name = models.CharField(max_length=32)  # Nome do SFC
    client = models.CharField(max_length=64)  # Dono do SFC (User)
    stop_type = models.CharField(max_length=8)  #
    vnf_ids = models.CharField(max_length=1024)  # vnf_id (Instances) que compõem o SFC
    vnfds = models.CharField(max_length=1024)  # vnfd_id (Instances) que compõem o SFC
    vnffgd = models.TextField(default='')  # Conteúdo do VNFFGD gerado pelo formulário
    tosca_vnffgd = models.TextField(default='')  # Conteúdo do VNFFGD mapeado para os padrões do TOSCA
    created_date = models.DateTimeField(default=timezone.now)  # Data
    infrastructure = models.CharField(max_length=32,
                                      default='')  # Infraestruturas no qual está rodando as VNFs do SFC todo: mudar

    class Meta:
        unique_together = ['client', 'name']


class SFCStatus(models.Model):
    name = models.CharField(max_length=32)  # Nome da instancia SFC
    client = models.ForeignKey(User, on_delete=models.CASCADE)  # Usuario que criou a SFC
    created_date = models.DateTimeField(auto_now_add=timezone.now)  # Data/Horario da criacao
    step = models.CharField(max_length=2, default='0')  # Quantidade de passos ja realizados. 10 passos no total.

    class Meta:
        verbose_name = 'SFC_Status'

    def __str__(self):
        return self.name + ' ' + self.client.username


class Status(models.Model):
    sfcstatus = models.ForeignKey(SFCStatus, on_delete=models.CASCADE)
    message = models.CharField(max_length=300, default='Starting service creation')  # Status do processo de criacao
    error = models.BooleanField()
    created_date = models.DateTimeField(auto_now_add=timezone.now)

    class Meta:
        verbose_name = 'Status'


    class Meta:
        ordering = ['-created_date']
