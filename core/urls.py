from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import login, logout
from core import views
from marketplace.models import Catalog_SFC
from repository.models.catalog import Catalog
# import debug_toolbar
from django.conf.urls.static import static
from core import settings
from django.conf.urls.i18n import i18n_patterns
from accounts.forms import UserCreationForm, Autenticacao

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.index, name='index'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    url(r'^about$', views.about, name='about'),
    url(r'^team$', views.team, name='team'),
    url(r'^publications$', views.publications, name='publications'),
    url(r'^services/(?P<id>\d+)$', views.services, name='services'),
    url(r'^actor/(?P<type>\w+)$', views.actor, name='actor'),
    url(r'^marketplace/', include('marketplace.urls', namespace="Marketplace")),
    url(r'^repository/', include('repository.urls', namespace="Repository")),
    url(r'^accounts/', include('accounts.urls', namespace="accounts")),
    url(r'^register/$', views.UserCreate.as_view(), name="register"),
    url(r'^logout/$', logout, {'next_page': 'index'}, name='logout'),
    url(r'^login/$', login,
        {'authentication_form': Autenticacao,'template_name': 'core/home.html', 'extra_context': {'services': Catalog_SFC.objects.all(),
                                                              'formup': UserCreationForm, 'active_view':'home'}}, name="login"),

    # url(r'^__debug__/', include(debug_toolbar.urls)),
    url(r'^api/', include('api.urls', namespace="api")),

) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
