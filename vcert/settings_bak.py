# Django settings for vcert project.

# Django settings for millionhearts project.
import os
from django.utils.translation import ugettext_lazy as _

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Alan Viars', 'aviars@videntity.com'),
)

MANAGERS = ADMINS

BASE_DIR = os.path.join( os.path.dirname( __file__ ), '..' )
MANAGERS = ADMINS


DBPATH=os.path.join(BASE_DIR, 'db/db.db')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': DBPATH,                   # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False


#Authentication
AUTH_PROFILE_MODULE = 'accounts.userprofile'
AUTHENTICATION_BACKENDS = (#'django.contrib.auth.backends.ModelBackend',
                           'apps.accounts.auth.EmailBackend',
                            'apps.accounts.auth.MobilePhoneBackend',
                           'apps.accounts.auth.HTTPAuthBackend',
                           )


# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'collectedstatic')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'sitestatic'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ej)&g6=#-jwzbdngm_)c5wz)(j$6c5toled%0@0pljih3(3w=j'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'vcert.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'vcert.wsgi.application'


TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'apps/home/templates'),
    
    # This should always be the last in the list because it is our
    # fallback default.
    os.path.join(BASE_DIR, 'templates'), 
)


LOCALE_PATHS = (
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'locale'),
)



INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
     'bootstrapform',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    'apps.accounts',
    'apps.certificates',
    'apps.home',
    'django.contrib.markup',
    'django_extensions',
    
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


# Email Settings -----------------------------------------------------------

EMAIL_HOST_USER = 'vcert@example.com'
HOSTNAME_URL = 'http://127.0.0.1:8000'
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''

# Default S3 bucket for filwe upload utility.
AWS_BUCKET =''

# Twilio is not yet supported, but these are added for future multi-factor
# authentication support requiring a mobile phone for login.


# Twilio SMS Settings -----------------------------------------------
TWILIO_DEFAULT_FROM = "+15555555555"
TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"
TWILIO_SID = ""
TWILIO_AUTH_TOKEN = ""
TWILIO_API_VERSION = '2010-04-01'
SMS_LOGIN_TIMEOUT_MIN = 10



#Org details
ORGANIZATION_NAME = "Example, Inc."
LOCATION_NAME = "Washington, DC"

# CA Settings -----------------------------------------------------
# Not reccomended to adjust this part

CA_BASE_DIR = "/opt/ca/"
CA_CONF_DIR     = os.path.join( CA_BASE_DIR, 'conf/' )
CA_PRIVATE_DIR  = os.path.join( CA_BASE_DIR, 'private/' )
CA_PUBLIC_DIR   = os.path.join( CA_BASE_DIR, 'public/' )
CA_SIGNED_DIR   = os.path.join( CA_BASE_DIR, 'signed-keys/' )
CA_COMPLETED_DIR = os.path.join( CA_BASE_DIR, 'completed/' )
CA_INPROCESS_DIR = os.path.join( CA_BASE_DIR, 'inprocess/' )
CA_CRL_DIR = os.path.join( CA_BASE_DIR, 'crl/' )
CA_PUBLIC_CERT   = os.path.join( CA_BASE_DIR, 'public/', "ca.example.com.pem" )
CA_MAIN_CONF    = os.path.join( CA_CONF_DIR , "ca.example.com.cnf")



CA_VERIFIER_EMAIL = "verifier@example.com"


#depricated - iInore and liekly to  be removed in future versions.
CRL_FILENAME = "global-crl.pem"


#Publish items to S3.  If false the behavior is disabled.
USE_S3              = True
# Send outbound emails such as #verification notification and more
SEND_CA_EMAIL       = True

# The S3 bucket for the certificate revocation lists.  This "webserver" is
# used by all trust anchors.
CRL_BUCKET          = "ca.example.com"

#A bucket for the X5C certificate chain
X5C_BUCKET          = "pubcerts.example.com"

#A bucket for public certs in pem, dir and x12 formats.
PUBCERT_BUCKET      = "pubcerts.example.com"

# A bucket for private certificates
PRIVCERT_BUCKET     = "privcerts.example.com"

# A bucket to contain a JSON representation of the certificate revocation status
RCSP_BUCKET         = "rcsp.example.com"


RCSPSHA1_BUCKET     = "rcspsha1.example.com"



# To enable you local settings create or copy the example
# file found in ./config/settings_[EXAMPLE].py to the same
# directory as settings.py
try:
    from settings_local import *
except ImportError:
    pass
