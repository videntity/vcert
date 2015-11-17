#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import datetime
from  OpenSSL import crypto
from django.forms import ModelForm, Form
from django import forms
from django.forms.extras.widgets import SelectDateWidget
from models import EndpointCertificate, TrustAnchorCertificate
import datetime
from gdc.parse_certificate import build_chain
from gdc.get_direct_certificate import DCert
from django.utils.translation import ugettext_lazy as _

OUTPUT_CHOICES = (("json","JSON"),("html","HTML"))

class TrustAnchorCertificateForm(ModelForm):
    class Meta:
        model = TrustAnchorCertificate
        fields = ('dns', 'rsa_keysize', 'organization','city', 'state',
                   'expire_days', 'include_aia', 'include_crl','contact_first_name',
                  'contact_last_name', 'contact_email',)
   
    required_css_class = 'required'
    
    def clean_email(self):
        email = self.cleaned_data.get('email', "").strip()
        
        anchors = TrustAnchorCertificate.objects.filter(email=email, status="good").count()
        endpoints = EndpointCertificate.objects.filter(email=email, status="good").count()
        
        if anchors or endpoints:
            raise forms.ValidationError(_('A certificate was already created with this email. It must be revoked before continuing.'))
        return email
    
    def clean_dns(self):
        dns = self.cleaned_data.get('dns', "").strip()
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
        email = self.cleaned_data.get('email', "").strip()
        anchors = TrustAnchorCertificate.objects.filter(email=email, status="good").count()
        endpoints = EndpointCertificate.objects.filter(email=email, status="good").count()
        
        if anchors or endpoints:
            raise forms.ValidationError(_('A certifcate was already created with this email. It must be revoked before continuing.'))
        return email
    
    def clean_dns(self):
        dns = self.cleaned_data.get('dns', "").strip()
        anchors = TrustAnchorCertificate.objects.filter(dns=dns, status="good").count()
        endpoints = EndpointCertificate.objects.filter(dns=dns, status="good").count()
        
        if anchors or endpoints:
            raise forms.ValidationError(_('A certificate was already created with this DNS. It must be revoked before continuing.'))
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




class DiscoverPublicForm(Form):

    endpoint   = forms.CharField(label=_("Endpoint"),
                                    help_text="""
                                    Lookup in DNS and LDAP using this name. This is often the
                                    subject's common name ("CN") or the SubjectAltName's email
                                    address or DNS value.
                                    """)
    output_format    = forms.TypedChoiceField(choices=OUTPUT_CHOICES, initial="html")
    def clean_pem(self):
        endpoint = self.cleaned_data.get('endpoint', "")        
        return  endpoint.lstrip().rstrip() 
    
    required_css_class = 'required'
    
    def save(self, commit=True):
        
        endpoint = self.cleaned_data.get('endpoint', "")
        dc = DCert(endpoint=endpoint, expected_bound_entity=endpoint, save_to_disk=False)
        results = dc.validate_certificate()
        return results
        
 

class DiscoverPEMForm(Form):
    pem                     = forms.CharField(widget=forms.Textarea, label=_("PEM Certificate"),
                                    help_text="""
                                    This file's contents begins with -----BEGIN CERTIFICATE----- and ends with
                                    -----END CERTIFICATE-----.
                                    This file usually has the extension .pem or .crt and can be opened in any ASCII text editor. """)
    expected_bound_entity   = forms.CharField( required=False, label=_("Expected Bound Entity"),
                                    help_text="""
                                    This is often the subject's common name ("CN") the subject Alt Name's email address or DNS value.
                                    This  field is not required and present to facilitate checking that a certificate given is bound
                                    to the expected entity.
                                    """)
    output_format            = forms.TypedChoiceField(choices=OUTPUT_CHOICES, initial="html")
    
    
    
    
    def clean_pem(self):
        x509 = None
        pem = self.cleaned_data.get('pem', "")
        
        try:
            x509 = crypto.load_certificate(crypto.FILETYPE_PEM, pem)
        except:
            raise forms.ValidationError(_('Invalid PEM.'))

        if not x509:
            raise forms.ValidationError(_('Invalid PEM.'))
                
        return pem
    
    required_css_class = 'required'
    
    def save(self, commit=True):
        
        pem = self.cleaned_data.get('pem', "")
        expected_bound_entity = self.cleaned_data.get('expected_bound_entity', None)
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, pem)
        return build_chain(x509, expected_bound_entity)