from django.conf.urls import include, url
from django.contrib import admin
from marketplace import views

admin.autodiscover()

urlpatterns = [
    url(r'^sfc/construct/$', views.sfc_construct.as_view(), name='sfc_construct'),
    url(r'^service/(?P<id>\d+)$', views.service, name='service'),
    url(r'^service/(?P<pk>\d+)/change/$', views.edit_service, name='edit_service'),
    url(r'^$', views.marketplace, name='index'),
    url(r'^(?P<category>[\w _-]+)$', views.marketplace, name='index'),
    url(r'^buy/$', views.buy, name='buy'),
    url(r'^catalog/vnfs$', views.catalog_vnfs, name='catalog_vnfs'),
    url(r'^purchased/$', views.vnfs, name='purchased'),
    url(r'^instances/$', views.instances, name='instances'),
    url(r'^instances/statistics/', views.statistics, name='statistics'),
    url(r'^instances/info/', views.info, name='info'),
    url(r'^deploy/(?P<id>\d+)/$', views.deploy, name='deploy'),
    url(r'^deployments/', views.deployments, name='deployments'),
    url(r'^sfc/$', views.sfc_list, name='sfc_list'),
    url(r'^sfc/create/$', views.sfc_create, name='sfc_create'),
    url(r'^sfc/sfc_path/', views.sfc_path, name='sfc_path'),
    url(r'^remove/(?P<id>\d+)/$', views.remove, name='remove'),
    url(r'^logs/(?P<vnf_id>[\w_-]+)/', views.get_log, name='logs'),
    url(r'^show_vnfd/', views.show_vnfd, name='show_vnfd'),
    url(r'^tutorial/(?P<tutorial>[\w _-]+)/', views.tutorial, name='tutorial'),
    url(r'^infrastructure/list/', views.infra_list, name='infrastructure_list'),
    url(r'^infrastructure/form/$', views.infrastructure_form, name='infrastructure_form'),
    url(r'^infrastructure/edit/(?P<id>\d+)/$', views.infra_update, name='infrastructure_edit'),
    url(r'^vnf/(?P<id>[\w_-]+)', views.vnf_api, name='vnf_api'),
    url(r'^resize/(?P<id>[\w_-]+)', views.resize, name='resize'),
]
