#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4


from django.conf import settings

def global_title(request):
    from django.conf import settings
    return {'global_title': settings.GLOBAL_TITLE}

    

