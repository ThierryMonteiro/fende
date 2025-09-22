#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import *
from catalog import *
from django.db import models

class Permission(BaseModel):
    permission_id = models.AutoField(primary_key=True) # Chave
    VNF = models.CharField(max_length=100) # VNF_name-version-developer (Catalog) 
    code_source = models.CharField(max_length=500, default="all")
    contract_vnf = models.CharField(max_length=500, default="all")
    # Adicionar novas politicas abaixo

    def __unicode__(self):
        return '%s' % (self.VNF)
