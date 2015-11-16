#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict


def get_cert_highlights(certificate_results):
    
    
    san = False
    h =  OrderedDict()
    h['Summary'] = "Unsure"
    h['Details'] = []
    h['Common Name']= certificate_results['subject']['CN']
    h['Serial Number']= certificate_results['serial_number']
    h['Issuer']= certificate_results['issuer']['CN']
    h['Expired']= certificate_results['is_expired']
    h['Revocation Status']= certificate_results['revocation_status']
    h['Chain Status'] = certificate_results['chain_status']
    
    
    
    
    if certificate_results.has_key('bound_to_expected_entity'):
        h['Bound to Expected Entity']=  certificate_results['bound_to_expected_entity']
    else:
        h['Bound to Expected Entity']= "Unknown / No Expected Entity  Provided"
     
    extensions =   certificate_results.get('extensions', {}) 
    
    for k in extensions.keys():
        if k == "subjectAltNameDNS":
            h['Subject Alt Name DNS'] = extensions[k]
            h['Endpoint Type'] = "Domain Bound"
            san = True
        
        if k == "subjectAltNameemail":
            h['Subject Alt Name Email'] = extensions[k]
            h['Endpoint Type'] = "Email Bound"
            san = True
        
        if k == "basicConstraints":
            h['Basic Constraints'] = extensions[k]

        if k == "authorityKeyIdentifierkeyid":
            h['Authority Key Identifier Key ID'] = extensions[k]


        if k == "subjectKeyIdentifier":
            h['Subject Key Identifier'] = extensions[k]

        if k == "basicConstraints":
            h['Basic Constraints'] = extensions[k]
        
        
        
    h['Signature Algorithm'] = certificate_results['signature_algorithm']
    
    
    
    if h['Signature Algorithm'].__contains__('sha2') and \
       san == True and \
       h['Expired'] == False and \
       h['Revocation Status'] == "ACTIVE" and \
       h['Chain Status'] == "IN-TACT" and \
       h['Bound to Expected Entity'] == True:
            h['Summary'] = "Good"
    
    if h['Chain Status'] == "BROKEN":
        h['Summary'] = "Unsure"    
        h['Details'].append("One or more AIAs missing.")
        
    if h['Revocation Status'] == "REVOKED":
        h['Summary'] = "Bad"
        h['Details'].append("The certificate is revoked.")
    elif h['Revocation Status'] == "UNDETERMINED":
        h['Summary'] = "Unsure"
        h['Details'].append("One or more CRLs missing.")
    
    if h['Expired']== True:
        h['Summary'] = "Bad"
        h['Details'].append("The certificate is expired.")

    if h['Bound to Expected Entity']== False:
        h['Summary'] = "Bad"
        h['Details'].append("The certificate appears to be bound to the wrong entity. ") 

    
    return h
    