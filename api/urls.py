from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^service/$', views.service, name='service'),
    url(r'^function/$', views.function, name='function'),
    url(r'^service/(?P<id>\d+)/$', views.service_status, name='service_status'),
    url(r'^service/logs/(?P<id>\d+)/$', views.service_logs, name='service_logs'),
]
