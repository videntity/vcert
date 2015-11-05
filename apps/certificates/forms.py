#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import datetime

from django.forms import ModelForm
from django import forms
from django.forms.extras.widgets import SelectDateWidget
from models import EndpointCertificate, TrustAnchorCertificate
import datetime

from django.utils.translation import ugettext_lazy as _



class TrustAnchorCertificateForm(ModelForm):
    class Meta:
        model = TrustAnchorCertificate
        fields = ('dns', 'rsa_keysize', 'organization','city', 'state',
                   'expire_days', 'include_aia', 'include_crl','contact_first_name',
                  'contact_last_name', 'contact_email',)
   
    required_css_class = 'required'
    
    def clean_email(self):
        email = self.cleaned_data.get('email', "")
        anchors = TrustAnchorCertificate.objects.filter(email=email, status="good").count()
        endpoints = EndpointCertificate.objects.filter(email=email, status="good").count()
        
        if anchors or endpoints:
            raise forms.ValidationError(_('A certificate was already created with this email. It must be revoked before continuing.'))
        return email
    
    def clean_dns(self):
        dns = self.cleaned_data.get('dns', "")
        anchors = TrustAnchorCertificate.objects.filter(dns=dns, status="good").count()
        endpoints = EndpointCertificate.objects.filter(dns=dns, status="good").count()
        
        if anchors or endpoints:
            raise forms.ValidationError(_('A certificate was already created with this DNS. It must be revoked before continuing.'))
        return dns
        
        

class RevokeTrustAnchorCertificateForm(ModelForm):
    class Meta:
        model = TrustAnchorCertificate
        fields = ('revoke',)
    required_css_class = 'required'


class VerifyTrustAnchorCertificateForm(ModelForm):
    class Meta:
        model = TrustAnchorCertificate
        fields = ('verified',)
    required_css_class = 'required'



class EndpointCertificateForm(ModelForm):
    class Meta:
        model = EndpointCertificate
        fields = ('email', 'dns', 'rsa_keysize', 'organization','city', 'state', 
                  'expire_days', 'include_aia', 'include_crl','contact_first_name', 'contact_last_name',
                  'contact_email')
   
    required_css_class = 'required'
    
    def clean_email(self):
        email = self.cleaned_data.get('email', "")
        anchors = TrustAnchorCertificate.objects.filter(email=email, status="good").count()
        endpoints = EndpointCertificate.objects.filter(email=email, status="good").count()
        
        if anchors or endpoints:
            raise forms.ValidationError(_('A certifcate was already created with this email. It must be revoked before continuing.'))
        return email
    
    def clean_dns(self):
        dns = self.cleaned_data.get('dns', "")
        anchors = TrustAnchorCertificate.objects.filter(dns=dns, status="good").count()
        endpoints = EndpointCertificate.objects.filter(dns=dns, status="good").count()
        
        if anchors or endpoints:
            raise forms.ValidationError(_('A certifcate was already created with this DNS. It must be revoked before continuing.'))
        return dns
    
class RevokeEndpointCertificateForm(ModelForm):
    class Meta:
        model = EndpointCertificate
        fields = ('revoke',)
    required_css_class = 'required'
    
    
class VerifyEndpointCertificateForm(ModelForm):
    class Meta:
        model = EndpointCertificate
        fields = ('verified',)
    required_css_class = 'required'