#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
from string import join

from django.core.urlresolvers import reverse
from django.db import models
from accounts.models import User
from repository.models.catalog import Category, Catalog
from repository.models.acquisitions import Acquisitions
from repository.models.infrastructures import Infrastructure
from sortedm2m.fields import SortedManyToManyField


class TAG(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


def build_url(*args, **kwargs):
    get = kwargs.pop('get', {})
    url = reverse(*args, **kwargs)
    if get:
        url += '?' + urllib.urlencode(get)
    return url


class Catalog_SFC(models.Model):
    consultant = models.ForeignKey(User, on_delete=models.CASCADE)
    institution = models.CharField('Institution', max_length=30)
    # repositories_ids
    sfc_name = models.CharField('SFC Name', max_length=100)
    # prints
    vnfs = SortedManyToManyField('VNFService')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    version = models.CharField('Version', max_length=10)
    price = models.DecimalField('Price', max_digits=10, decimal_places=2)
    full_description = models.CharField(max_length=1000)
    create_date = models.DateTimeField(auto_now_add=True)  # Data
    tag = models.ManyToManyField(TAG, verbose_name='TAGS', blank=True)

    def __str__(self):
        return self.sfc_name.encode('utf8')

    def clients(self):
        return Acquisitions.objects.filter(repository=self.id)

    def update_url(self):
        vnfs = []
        for vnf in self.vnfs.all():
            vnfs.append(str(vnf.catalog.repository_id))
            vnfs.append(str(vnf.catalog.VNF_name))
        string = join(vnfs, ',')
        return build_url('Marketplace:edit_service', args=[self.pk], get={'vnfs': string})


class VNFService(models.Model):
    service = models.ForeignKey(Catalog_SFC, on_delete=models.CASCADE)
    catalog = models.ForeignKey(Catalog, on_delete=models.CASCADE)

    def __str__(self):
        return self.catalog.VNF_name


class CP(models.Model):
    service = models.ForeignKey(Catalog_SFC, on_delete=models.CASCADE)
    position = models.IntegerField('Position', default=0)
    input = models.CharField('Input', max_length=20)
    output = models.CharField('Output', max_length=20)

    class Meta:
        unique_together = ['service', 'position']

    def __str__(self):
        return 'input: ' + self.input + ' ' + 'output: ' + self.output


class Print(models.Model):
    catalog = models.ForeignKey(Catalog_SFC, on_delete=models.CASCADE)
    image = models.ImageField('Prints', upload_to='prints')
