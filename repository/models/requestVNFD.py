#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import *
from django.db import models
from accounts.models import User
Categories =  (
             ('security', 'Security'),
             ('forwarding', 'Forwarding'),
             ('performance', 'Performance'),   
             ('others', 'Others'),   
             )

class RequestVNFD(BaseModel):
    request_id = models.AutoField(primary_key=True) # Chave
    review_tag = models.CharField(max_length=10, default='To Review') # Status da revisão
    developer = models.ForeignKey(User) # Quem submeteu o VNFD (User)
    institution = models.CharField(max_length=100) # Instituição de quem submeteu a VNF (User)
    VNF_name = models.CharField(max_length=50) # Nome da VNF no qual o VNFD está vinculado
    version = models.CharField(max_length=10) # Versão da VNF no qual o VNFD está vinculado
    category = models.CharField(max_length=30, choices=Categories) # Categoria
    abstract = models.CharField(max_length=120) # Resumo
    link = models.CharField(max_length=200) # Link para o git
    comments = models.CharField(max_length=2000, default="Not available yet") # Comentários feitos pelo revisor
    details = models.CharField(max_length=9999, default="Not provided") # Detalhes sobre o que foi alterado no VNFD
    create_date = models.DateTimeField(auto_now_add=True) # Data

    def __unicode__(self):
        return '%s' % (self.request_id)
