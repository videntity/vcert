from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from ..accounts.models import UserProfile
from django.utils.translation import ugettext_lazy as _
from models import DomainBoundCertificate, TrustAnchorCertificate
from forms import (TrustAnchorCertificateForm, DomainBoundCertificateForm,
            RevokeDomainBoundCertificateForm, RevokeTrustAnchorCertificateForm,
            VerifyDomainBoundCertificateForm, VerifyTrustAnchorCertificateForm)

@login_required
def certificate_dashboard(request):
    
    #get all active trust anchors and associated domain-bound certs
    
    active_cert_list  = []
    
    active_tas = TrustAnchorCertificate.objects.filter(owner=request.user,
                                                       status="good") | \
                 TrustAnchorCertificate.objects.filter(owner=request.user,
                                                       status="unverified")
    
    for a in active_tas:
        domain = { 'trust_anchor': a,
                  'domain_bounds': None
                  }
        domain_bounds = DomainBoundCertificate.objects.filter(trust_anchor=a,
                                                        status="good") | \
                        DomainBoundCertificate.objects.filter(trust_anchor=a,
                                                    status="unverified")
        if domain_bounds:
            domain['domain_bounds'] = domain_bounds
        active_cert_list.append(domain)
    

    revoked_cert_list  = []
    
    revoked_tas = TrustAnchorCertificate.objects.filter(owner=request.user,
                                                        status = "revoked")    
        
    for r in revoked_tas:
        revoked_cert_list.append(r)
       
    domain_bounds = DomainBoundCertificate.objects.filter(
                                        trust_anchor__owner=request.user,
                                        status="revoked")
    for d in domain_bounds:
        revoked_cert_list.append(d)

        
    context={ 'active_cert_list': active_cert_list,
              'revoked_cert_list': revoked_cert_list, 
             }
    
    return render_to_response('home/index.html',
                              RequestContext(request, context,))

@login_required
def create_domain_certificate(request, serial_number):
    name = _("Create an Endpoint Certificate")
    if request.method == 'POST':
        ta = get_object_or_404(TrustAnchorCertificate, serial_number=serial_number,
                               owner = request.user)
        form = DomainBoundCertificateForm(request.POST)
        if form.is_valid():
            c = form.save(commit = False)
            c.common_name = c.dns
            c.domain = c.dns
            c.trust_anchor = ta
            c.save()
            if c.status == "unverified":
                messages.success(request, _("Your Direct certificate creation request completed successfully."))
            elif c.status == "failed":
                messages.error(request, _("Oops.  Something has gone wrong.  Your certifcate creation request failed."))
            
            return HttpResponseRedirect(reverse('home'))
        else:
            #The form is invalid
             messages.error(request,_("Please correct the errors in the form."))
             return render_to_response('generic/bootstrapform.html',
                                            {'form': form,
                                             'name':name,
                                             },
                                            RequestContext(request))
            
   #this is a GET
    ta = get_object_or_404(TrustAnchorCertificate, serial_number=serial_number,
                               owner = request.user)
    up = UserProfile.objects.get(user=request.user)
    #dnsguess ="direct.%s" % (ta.dns)
    data ={'contact_first_name': request.user.first_name,
           'contact_last_name': request.user.last_name,
           'city': up.city,
           'state': up.state,
           'organization': up.organization_name,
           'contact_email': request.user.email,
           'npi': up.npi,
           #'dns': dnsguess,
           }
    context= {'name':name,
              'form': DomainBoundCertificateForm(initial=data)}
    return render_to_response('generic/bootstrapform.html',
                              RequestContext(request, context,))


@login_required
def create_trust_anchor_certificate(request):
    name = _("Create a Trust Anchor Certificate")
    if request.method == 'POST':
        form = TrustAnchorCertificateForm(request.POST)
        if form.is_valid():
            ta = form.save(commit = False)
            ta.common_name = ta.dns
            ta.domain = ta.dns
            ta.owner=request.user
            ta.save()
            if ta.status == "unverified":
                messages.success(request, _("Your trust anchor creation request completed successfully. A human must verify this information before you can create endpoint certificates. An email will be sent when this process is complete."))
            elif ta.status == "failed":
                messages.error(request, _("Oops.  Something has gone wrong.  Your trust anchor certifcate creation request failed. Please contact customer support."))
        
            return HttpResponseRedirect(reverse('home'))
        else:
            #The form is invalid
             messages.error(request,_("Please correct the errors in the form."))
             return render_to_response('generic/bootstrapform.html',
                                            {'form': form,
                                             'name':name,
                                             },
                                            RequestContext(request))
            
   #this is a GET
   
    up = UserProfile.objects.get(user=request.user)
    data ={'contact_first_name': request.user.first_name,
           'contact_last_name': request.user.last_name,
           'city': up.city,
           'state': up.state,
           'organization': up.organization_name,
           'contact_email': request.user.email,
           'npi': up.npi,
           }
   
   
    context= {'name':name,
              'form': TrustAnchorCertificateForm(initial=data)
              }
    return render_to_response('generic/bootstrapform.html',
                              RequestContext(request, context,))



@login_required
def revoke_trust_anchor_certificate(request, serial_number):
    name = _("Revoke a Trust Anchor Certificate & its Children")
    ta = get_object_or_404(TrustAnchorCertificate, serial_number=serial_number,
                               owner = request.user)
        
    if request.method == 'POST':
        form = RevokeTrustAnchorCertificateForm(request.POST, instance = ta)
        if form.is_valid():
            m = form.save()
            children = DomainBoundCertificate.objects.filter(trust_anchor = ta)
            for c in children:
                c.revoke = True
                c.save()
            if m.status == "revoked":
                messages.success(request, _("The Direct Trust Anchor certificate and all its children were revoked."))
            else:
                messages.success(request, _("The Direct Trust Anchor certificate was NOT revoked."))
            
            return HttpResponseRedirect(reverse('home'))
        else:
            #The form is invalid
             messages.error(request,_("Please correct the errors in the form."))
             return render_to_response('generic/bootstrapform.html',
                                            {'form': form,
                                             'name':name,
                                             },
                                            RequestContext(request))
            
    #this is a GET
    context= {'name': name,
              'form': RevokeTrustAnchorCertificateForm(instance = ta)
              }
    return render_to_response('generic/bootstrapform.html',
                              RequestContext(request, context,))
        
@login_required
def revoke_domain_certificate(request, serial_number):
    
    name = _("Revoke a Domain Bound Certificate")
    dbc = get_object_or_404(DomainBoundCertificate, serial_number=serial_number,
                               trust_anchor__owner = request.user)
        
    if request.method == 'POST':
        form = RevokeDomainBoundCertificateForm(request.POST, instance = dbc)
        if form.is_valid():
            m = form.save()
            if m.status == "revoked":
                messages.success(request, _("The Direct endpoint certificate was revoked."))
            else:
                messages.success(request, _("The Direct endpoint certificate was NOT revoked."))
            
            return HttpResponseRedirect(reverse('home'))
        else:
            #The form is invalid
             messages.error(request,_("Please correct the errors in the form."))
             return render_to_response('generic/bootstrapform.html',
                                            {'form': form,
                                             'name':name,
                                             },
                                            RequestContext(request))
            
    #this is a GET
    context= {'name': name,
              'form': RevokeDomainBoundCertificateForm(instance = dbc)
              }
    return render_to_response('generic/bootstrapform.html',
                              RequestContext(request, context,))




@login_required
@staff_member_required
def verify_trust_anchor_certificate(request, serial_number):
    name = _("Verify a Trust Anchor Certificate")
    ta = get_object_or_404(TrustAnchorCertificate, serial_number=serial_number,
                               owner = request.user)
        
    if request.method == 'POST':
        form = VerifyTrustAnchorCertificateForm(request.POST, instance = ta)
        if form.is_valid():
            m = form.save()
            
            if m.verified:
                messages.success(request, _("The Direct trust anchor certificate was verified."))
            else:
                messages.error(request, _("The Direct trust anchor certificate was NOT verified. Something has gone wrong. Contact a systems administrator."))
            
            
           
            
            return HttpResponseRedirect(reverse('home'))
        else:
            #The form is invalid
             messages.error(request,_("Please correct the errors in the form."))
             return render_to_response('generic/bootstrapform.html',
                                            {'form': form,
                                             'name':name,
                                             },
                                            RequestContext(request))
            
    #this is a GET
    context= {'name': name,
              'form': VerifyTrustAnchorCertificateForm(instance = ta)
              }
    return render_to_response('generic/bootstrapform.html',
                              RequestContext(request, context,))



@login_required
@staff_member_required
def verify_domain_certificate(request, serial_number):
    
    name = _("Verify a Domain Bound Certificate")
    dbc = get_object_or_404(DomainBoundCertificate, serial_number=serial_number,
                               trust_anchor__owner = request.user)
        
    if request.method == 'POST':
        form = VerifyDomainBoundCertificateForm(request.POST, instance = dbc)
        if form.is_valid():
            m = form.save()
            if m.verified:
                messages.success(request, _("The Direct endpoint certificate was verified."))
            else:
                messages.error(request, _("The Direct endpoint certificate was NOT verified. Something has gone wrong. Contact a systems administrator."))
            
            return HttpResponseRedirect(reverse('home'))
        else:
            #The form is invalid
             messages.error(request,_("Please correct the errors in the form."))
             return render_to_response('generic/bootstrapform.html',
                                            {'form': form,
                                             'name':name,
                                             },
                                            RequestContext(request))
            
    #this is a GET
    context= {'name': name,
              'form': VerifyDomainBoundCertificateForm(instance = dbc)
              }
    return render_to_response('generic/bootstrapform.html',
                              RequestContext(request, context,))



def rcp(request, serial_number):
    
    tu = None
    c = None
    
    jsonstr = {
                "HashAlgorithm":    "sha1",
                "SHA1Fingerprint":  c.sha1_fingerprint,
                "SerialNumber":     c.serial_number,
                "CertStatus":       certstatus,
                "ThisUpdate":       tu,
            }

    jsonstr=json.dumps(jsonstr, indent = 4,)
    
    return HttpResponse(jsonstr, status=200, mimetype="application/json")
    
    
    