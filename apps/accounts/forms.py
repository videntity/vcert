#!/usr/bin/env python
from django import forms
from  models import *
#from django.contrib.admin import widgets
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from localflavor.us.models import PhoneNumberField
from localflavor.us.us_states import US_STATES
from django.conf import settings
from django.core.mail import mail_admins
from django.utils.translation import ugettext_lazy as _
from models import Invitation
class PasswordResetRequestForm(forms.Form):
    email= forms.CharField(max_length=75, label=_("Email"))
    required_css_class = 'required'
    
class PasswordResetForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput, max_length=30,
                                label=_("Password*"))
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=30,
                                label=_("Password (again)*"))

    required_css_class = 'required'
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two passwords didn't match."))
        if len(password1) < settings.MIN_PASSWORD_LEN:
            msg=_("Password must be at least %s characters long. Be tricky!") % (settings.MIN_PASSWORD_LEN)
            raise forms.ValidationError(msg)
        return password2


class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, label=_("User"))
    password = forms.CharField(widget=forms.PasswordInput, max_length=30,
                               label=_("Password"))
    required_css_class = 'required'




class SignupForm(forms.Form):
    
    invitation_code         = forms.CharField(max_length=30, label=_("Invitation Code"))
    username                = forms.CharField(max_length=30, label=_("User"))
    email                   = forms.EmailField(max_length=75, label=_("Email"))
    first_name              = forms.CharField(max_length=100, label=_("First Name"))
    last_name               = forms.CharField(max_length=100, label=_("Last Name"))
    organization_name       = forms.CharField(max_length=100, label=_("Organization Name"))
    state                   = forms.TypedChoiceField(choices=US_STATES, label=_("State"),)
    city                    = forms.CharField(max_length=100, label=_("City"))
    mobile_phone_number     = PhoneNumberField(max_length=15,)
    npi                     = forms.CharField(max_length=20, label=_("National Provider Identifier (NPI)"), required=False)



    password1 = forms.CharField(widget=forms.PasswordInput, max_length=30,
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=30,
                                label=_("Password (again)"))
    
    required_css_class = 'required'
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        if len(password1) < settings.MIN_PASSWORD_LEN:
            msg=_("Password must be at least %s characters long.  Be tricky!") % (settings.MIN_PASSWORD_LEN)
            raise forms.ValidationError(msg)
        return password2
    
    def clean_email(self):
        email = self.cleaned_data.get('email', "")
        if email:
            username = self.cleaned_data.get('username')
            if email and User.objects.filter(email=email).exclude(username=username).count():
                raise forms.ValidationError(_('This email address is already registered.'))
            return email
        else:
            return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).count()>0:
            raise forms.ValidationError(_('This username is already taken.'))
        return username
    
    def clean_invitation_code(self):
        invitation_code = self.cleaned_data['invitation_code']
        if Invitation.objects.filter(valid=True, code = invitation_code).count() != 1:
            raise forms.ValidationError(_('The invitation code is not valid.'))
        return invitation_code


    def save(self):
        
        invitation_code = self.cleaned_data['invitation_code']
        #make the invitation a invalid/spent.
        invite = Invitation.objects.get(code=str(invitation_code), valid=True)
        invite.valid=False
        invite.save()
            
        
        
        new_user = User.objects.create_user(
                        username=self.cleaned_data['username'],
                        first_name=self.cleaned_data['first_name'],
                        last_name=self.cleaned_data['last_name'],
                        password=self.cleaned_data['password1'],
                        email=self.cleaned_data['email'])
        
        new_user.is_active = False
        new_user.save()
        
        up=UserProfile.objects.create(
            user=new_user,
            invitation_code = self.cleaned_data['invitation_code'],
            mobile_phone_number=self.cleaned_data.get('mobile_phone_number', ""),
            city=self.cleaned_data.get('city', ""),
            state=self.cleaned_data.get('state', ""),
            organization_name=self.cleaned_data.get('organization_name', ""),
            npi=self.cleaned_data.get('npi', ""),
            )
        
        v=ValidSignupKey(user=new_user)
        v.save()
        
        return new_user
    
class AccountSettingsForm(forms.Form):

    
    username                = forms.CharField(max_length=30, label=_("User Name"))
    email                   = forms.CharField(max_length=30, label=_("Email"))
    first_name              = forms.CharField(max_length=100, label=_("First Name"))
    last_name               = forms.CharField(max_length=100, label=_("Last Name"))
    
    organization_name       = forms.CharField(max_length=100,
                                                    label=_("Organization Name"))
    state                   = forms.TypedChoiceField(choices=US_STATES,
                                                        label=_("State"))
    city                    = forms.CharField(max_length=100, label=_("City"))
    mobile_phone_number     = PhoneNumberField(max_length=12,)
    npi                     = forms.CharField(max_length=20, label=_("NPI"), required=False)
    
    required_css_class = 'required'
    

    
    def clean_email(self):
        email = self.cleaned_data.get('email', "")
        if email:
            username = self.cleaned_data.get('username')
            if email and User.objects.filter(email=email).exclude(email=email).count():
                raise forms.ValidationError(_('This email address is already registered.'))   
            return email
        else:
            return "foo@bar.com"

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exclude(username=username).count():
            raise forms.ValidationError(_('This username is already taken.'))
        return username
