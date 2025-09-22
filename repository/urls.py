from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$',                                      views.dev_dashboard,            name='index'),
    url(r'^dev/status/',                            views.dev_submission_status,    name='dev_submission_status'),
    url(r'^dev/my_repositories/',                   views.dev_myrepositories,       name='dev_myrepositories'),
    url(r'^dev/update/submit/',                     views.dev_updateform,           name='dev_updateform'),
    url(r'^dev/policy_update/',                     views.dev_policy_update,        name='dev_policy_update'),
    url(r'^dev/VNFD_update/',                       views.dev_VNFD_update,          name='dev_VNFD_update'),
    url(r'^review/$',                               views.review_list,              name='review_list'),
    url(r'^review/vnfd/$',                          views.vnfd_list,                name='vnfd_list'),
    url(r'^review/vnfd/download/',                  views.vnfd_download,            name='vnfd_download'),
    url(r'^review/details/',                        views.review_details,           name='review_details'),
    url(r'^review/accept/',                         views.repository_accept,        name='repository_accept'),
    url(r'^review/reject/',                         views.repository_reject,        name='repository_reject'),
    url(r'^review/vnfd/accept/',                    views.vnfd_accept,              name='vnfd_accept'),
    url(r'^review/vnfd/reject/',                    views.vnfd_reject,              name='vnfd_reject'),
    url(r'download/(?P<id>\d+)/$',                  views.download,                 name='download'),
    url(r'^tutorial/(?P<tutorial>[\w _-]+)/',       views.tutorial,                 name='tutorial'),

    # Package Submission
    url(r'^dev/publish/',                           views.dev_publish,              name='dev_publish'),
    url(r'^dev/vnf/publish/',                       views.vnf_publish,              name='dev_vnf_publish'),
    url(r'^dev/package/upload',                     views.dev_package_upload,       name='dev_package_upload'),

]
