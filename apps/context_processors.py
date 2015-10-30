#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4


from django.conf import settings

def global_title(request):
    return {'global_title': settings.GLOBAL_TITLE}

    
def ca_common_name(request):
    return {'ca_common_name': settings.CA_COMMON_NAME}

def ca_url(request):
    return {'ca_url': settings.CA_URL}



