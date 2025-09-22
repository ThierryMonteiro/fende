#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import *
from django.db import models
from accounts.models import User, Institution
from repository.models import Category


class Request(BaseModel):
    request_id = models.AutoField(primary_key=True)  # Chave
    tag = models.CharField(max_length=10,
                           default='New')  # Diferencia novas VNFs de novas versões de VNFs (new ou update)

    review_tag = models.CharField(max_length=10, default='To Review')  # Status da revisão
    developer = models.ForeignKey(User)  # Quem submeteu a VNF (User)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)  # Instituição de quem submeteu a VNF (User)
    VNF_name = models.CharField(max_length=50)  # Nome da VNF
    version = models.CharField(max_length=10)  # Versão da VNF
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  # Categoria
    abstract = models.CharField(max_length=120)  # Resumo
    full_description = models.CharField(max_length=1000)  # Descrição completa
    link = models.CharField(max_length=200)  # Link para o git
    comments = models.CharField(max_length=2000, default="Not available yet")  # Comentários feitos pelo revisor
    create_date = models.DateTimeField(auto_now_add=True)  # Data

    def __unicode__(self):
        return '%s' % (self.request_id)
