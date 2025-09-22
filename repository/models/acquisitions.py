#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone

class Acquisitions(models.Model):
    repository = models.CharField(max_length=16) # ID do repositório (Catalog) que foi adquirido
    client = models.CharField(max_length=64) # Usuário que adquiriu a VNF (User)
    created_date = models.DateTimeField(default=timezone.now) # Data
