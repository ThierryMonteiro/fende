# coding=utf-8

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^ssh-key/$', views.ssh_key, name='ssh_key'),
    url(r'^remove-key/(?P<id>\d+)$', views.remove_key, name='remove_key'),
    # url(r'^registro/$', views.register, name='register'),
]
