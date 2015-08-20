#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4


"""
    Decorator to check for credentials before responding on json requests.
"""

from functools import update_wrapper, wraps

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

from utils import authorize, unauthorized_json_response


def json_login_required(func):
    """
        Put it before your view, will check if the user is logged in and return
        a JSON 401 error if he is not.
    """
    
    def wrapper(request, *args, **kwargs):
    
        if not authorize(request)\
            and getattr(settings,'API_AUTH_REQUIRED', True):
            
            return HttpResponse(unauthorized_json_response(), status=401)
    
        return func(request, *args, **kwargs)

    return update_wrapper(wrapper, func)






