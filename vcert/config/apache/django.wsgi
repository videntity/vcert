import os
import sys

sys.path.append('/opt/django-apps/vcert/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'vcert.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

