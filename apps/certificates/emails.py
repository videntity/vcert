#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from django.conf import settings
from django.core.mail import EmailMessage,  EmailMultiAlternatives,send_mail



def send_verifier_email(cert_type, organization, serial_number,common_name):
    
    if settings.SEND_CA_EMAIL :
        msg = """
            <html>
            <head>
            </head>
            <body>
            A new Direct %s certificate was created by %s and requires your review.
            Here is a link:
            <ul>
            <li><a href="%s/certificates/verify-%s/%s">%s</a></li>
            </ul>
            </body>
            </html>
            """ % (cert_type, organization, settings.HOSTNAME_URL, cert_type,
                   serial_number,common_name)
        
        subject = "[%s]A New Direct %s Certificate %s requires verification" % \
               (settings.ORGANIZATION_NAME, cert_type, common_name)
        msg = EmailMessage(subject,  msg, settings.EMAIL_HOST_USER,
                       [settings.CA_VERIFIER_EMAIL,])            
        msg.content_subtype = "html"  # Main content is now text/html
        msg.send()
    return

def send_trust_anchor_confirmation_email(common_name, public_cert_pem_url,
                                         public_cert_der_url, owner_email,
                                         contact_email):
    if settings.SEND_CA_EMAIL:
        msg = """
            <html>
            <head>
            </head>
            <body>
            Congratulations. Your anchor certificate for %s has been verified.
            Below are links to your public certificates.
            
            <ul>
            <li><a href="%s">PEM File - %s</a></li>
            <li><a href="%s">DER File - %s</a></li>
            </ul>
            </body>
            </html>
            """ % (common_name,
                   public_cert_pem_url,public_cert_pem_url,
                   public_cert_der_url,public_cert_der_url)
            
        subject = "[%s]Your Trust Anchor Certificate for %s has been verified" % \
                            (settings.ORGANIZATION_NAME, common_name)
        msg = EmailMessage(subject,
                               msg,
                               settings.EMAIL_HOST_USER,
                               [owner_email, contact_email])            
        msg.content_subtype = "html"  # Main content is now text/html
        msg.send()
    return

def send_endpoint_confirmation_email(common_name, public_cert_pem_url,
                                         public_cert_der_url, owner_email,
                                         contact_email):
    if settings.SEND_CA_EMAIL:
        msg = """
                <html>
                <head>
                </head>
                <body>
                Congratulations. Your endpoint certificate for %s has been verified.
                Below are links to your public certificates and related status information.
               
                <ul>
                    <li><a href="%s">PEM File -  %s  </a></li>
                    <li><a href="%s">DER File -  %s </a></li>
    
                </ul>
                
                <p>For security purposes you must
                <a href="%s">login</a> to download the
                private certificates.  
                </p>
                
                </body>
                </html>
                """ % ( common_name,
                       public_cert_pem_url,            public_cert_pem_url,
                       public_cert_der_url,            public_cert_der_url,
                       settings.HOSTNAME_URL)
                
        subject = "[%s]Your Direct endpoint certificate for %s has been verified"  % \
                  (settings.ORGANIZATION_NAME, common_name)
        msg = EmailMessage(subject,msg,settings.EMAIL_HOST_USER,
                    [owner_email, contact_email])            
        msg.content_subtype = "html"  # Main content is now text/html
        msg.send()