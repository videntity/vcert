#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from views import *


urlpatterns = patterns('',

    url(r'login/', simple_login,  name="login"),
    url(r'register', signup,  name="register"),
    url(r'logout/', mylogout, name='mylogout'),
    url(r'password-reset-request/', password_reset_request,
        name='password_reset_request'),
    
    url(r'account/', account_settings, name='account_settings'),
    url(r'reset-password/(?P<reset_password_key>[^/]+)/$', reset_password,
        name='password_reset_request'),
    
    url(r'signup-verify/(?P<signup_key>[^/]+)/$', signup_verify,
        name='signup_verify'),
    
    )