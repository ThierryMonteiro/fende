#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import *
from django.db import models
from accounts.models import User

class Version(BaseModel):
    version_id = models.AutoField(primary_key=True) # Chave
    developer = models.ForeignKey(User) # Desenvolvedor da VNF
    institution = models.CharField(max_length=100) # Instituição do desenvolvedor da VNF
    VNF_name = models.CharField(max_length=50) # Nome da VNF (Mesmo do Catalog)v
    version = models.CharField(max_length=10) # Versão da VNF
    category = models.CharField(max_length=50) # Categoria
    abstract = models.CharField(max_length=120) # Resumo
    full_description = models.CharField(max_length=1000) # Descrição completo
    link = models.CharField(max_length=200) # Link do git
    create_date = models.DateTimeField(auto_now_add=True) # Data

    def __unicode__(self):
        return '%s-%s-%s' % (self.VNF_name, self.version, self.developer)
