#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from views import *


urlpatterns = patterns('',
   

    url(r'create-trust-anchor/', create_trust_anchor_certificate,
                       name="create_trust_anchor_certificate"),

    url(r'create-intermediate-anchor/(?P<serial_number>\S+)',
                create_intermediate_anchor_certificate,
                name="create_intermediate_anchor_certificate"),

    url(r'create-endpoint/(?P<serial_number>\S+)', create_endpoint_certificate,
                       name="create_endpoint_certificate"),

    url(r'create-crl/(?P<serial_number>\S+)', create_anchor_crl,
                       name="create_anchor_crl"),

    
    url(r'revoke-endpoint/(?P<serial_number>\S+)', revoke_endpoint_certificate,
                        name="revoke_endpoint_certificate"),
    
   
    
    url(r'revoke-trust-anchor/(?P<serial_number>\S+)', revoke_trust_anchor_certificate,
                        name="revoke_trust_anchor_certificate"),    
    
    url(r'verify-anchor/(?P<serial_number>\S+)', verify_anchor_certificate,
                        name="verify_anchor_certificate"),    
    
    url(r'verify-endpoint/(?P<serial_number>\S+)', verify_endpoint_certificate,
                        name="verify_domain_certificate"), 
    
    
    url(r'view-anchor/(?P<serial_number>\S+)', view_anchor,
                        name="view_anchor_certificate"),
    
    url(r'view-anchor-details/(?P<serial_number>\S+)', view_anchor_details,
                        name="view_anchor_details"),
    url(r'view-endpoint-details/(?P<serial_number>\S+)', view_endpoint_details,
                        name="view_endpoint_details"),
    #url(r'$', certificate_dashboard,
    #                   name="certificate_dashboard"),
    
    )
