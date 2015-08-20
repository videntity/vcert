#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from django.conf import settings
from django.core.mail import EmailMessage,  EmailMultiAlternatives


def send_password_reset_url_via_email(user, reset_key):
    subject = "[%s]Your password reset request" % (settings.ORGANIZATION_NAME)    
    from_email = settings.EMAIL_HOST_USER
    to = user.email
    headers = {'Reply-To': from_email}
    
    html_content = """"
    <P>
    Click on the following link to reset your password.<br>
    <a HREF="%s/accounts/reset-password/%s">%s/accounts/reset-password/%s</a>
    </P>
    """ % (settings.HOSTNAME_URL , reset_key, settings.HOSTNAME_URL, reset_key)
   
    text_content="""
    Click on the following link to reset your password.
    %s/accounts/reset-password/%
    """
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to,])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def send_signup_key_via_email(user, signup_key):
    
    print "send mail"
    subject = "[%s]Verify your email to get started." % (settings.ORGANIZATION_NAME)    
    from_email = settings.EMAIL_HOST_USER
    to = user.email
    headers = {'Reply-To': from_email}
    
    html_content = """
    <P>
    You're almost done.  Please click the link to activate your account.<br>
    <a HREF="%s/accounts/signup-verify/%s">%s/accounts/signup-verify/%s</a>
    </P>
    """ % (settings.HOSTNAME_URL, signup_key, settings.HOSTNAME_URL, signup_key)
   
    text_content="""
    You're almost done.  Please click the link to activate your account.
    %s/accounts/signup-verify/%
    """
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to,])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

