import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '1%yqqrr2t1g%qw&@v=9e9%29fe&n8@@9(1#ind!%_)*oko87cz'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

ADMINS = [('Muriel', 'mffranco@inf.ufrgs.br'), ('Giovanni', 'gvs11ufpr@gmail.com'),
          ('Cassiano', 'cschneider@inf.ufsm.br')]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shibboleth',
    'marketplace',
    'repository',
    'accounts',
    'core',
    'api',
    # libs
    'widget_tweaks',
    'easy_thumbnails',
    'django_cleanup',
    # 'debug_toolbar',
    'watson',
    'sortedm2m',
]


# DEBUG TOOLBAR
def custom_show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
    'INTERCEPT_REDIRECTS': False,
    'DISABLE_PANELS': {'debug_toolbar.panels.logging.LoggingPanel'}

}

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'shibboleth.middleware.ShibbolethRemoteUserMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    # libs
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'core/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# application = get_wsgi_application()
# WSGI_APPLICATION = 'FENDE.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# CELERY
from kombu import Exchange, Queue

task_default_queue = 'default'
default_exchange = Exchange('deploy', type='direct')
task_queues = (
    Queue(
        'deploy_queue',
        exchange=default_exchange,
        routing_key='service'
    )
)



#Celery Config
# broker_url='transport://user:password@hostname:port/virtual_host'
BROKER_URL = 'amqp://guest:guest@localhost:5672//'

#BROKER_URL = 'redis://'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


# auth
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'shibboleth.backends.ShibbolethRemoteUserBackend',
    'accounts.backends.ModelBackend',
]

SHIBBOLETH_ATTRIBUTE_MAP = {
    # "Shib-brEduPerson-brEduAffiliationType": (False, "affiliation_type"),
    # "Shib-eduPerson-eduPersonPrincipalName": (True, "email"),
    "Shib-inetOrgPerson-cn": (False, "name"),
    "Shib-inetOrgPerson-mail": (True, "email"),
}

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en'
TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True
LANGUAGES = (
    ('en', u'English'),
    ('pt-br', u'Portugues'),
)

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale')
]

# Messages
from django.contrib.messages import constants as messages_constants

MESSAGE_TAGS = {
    messages_constants.INFO: 'info',
    messages_constants.SUCCESS: 'success',
    messages_constants.WARNING: 'warning',
    messages_constants.ERROR: 'danger',
}

# EMAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'gtfende@gmail.com'
EMAIL_HOST_PASSWORD = 'rnp12345'
EMAIL_USE_SSL = True
EMAIL_PORT = 465

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Thumbnails
THUMBNAIL_ALIASES = {
    '': {
        'catalog': {'size': (178, 238), 'crop': True},
    },
}

# URL to redirect user to login
# LOGIN_URL = 'http://www.site.com/accounts/login/' Exemplo
LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/'

# LOGIN_ERROR_URL = '/accounts/login-error/'
LOGIN_ERROR_URL = ''

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/main.log'),
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'marketplace': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(module)s %(funcName)s at line %(lineno)d: %(message)s'
        },
        'simple': {
            'format': '%(levelname)s: %(message)s'
        },
    },
}

DEV_MODE = False

try:
    from .local_settings import *
except ImportError:
    pass
