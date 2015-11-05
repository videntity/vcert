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
from models import EndpointCertificate, TrustAnchorCertificate
from forms import (TrustAnchorCertificateForm, EndpointCertificateForm,
            RevokeEndpointCertificateForm, RevokeTrustAnchorCertificateForm,
            VerifyEndpointCertificateForm, VerifyTrustAnchorCertificateForm)
from mptt.utils import drilldown_tree_for_node, previous_current_next
from django.db.models import Q


@login_required
def view_endpoint_details(request, serial_number):
    
    e = get_object_or_404(DomainBoundCertificate, serial_number=serial_number,
                               trust_anchor__owner = request.user)
    
    response = HttpResponse(e.details, content_type='text/plain')
    return response


@login_required
def view_anchor_details(request, serial_number):
    
    a = get_object_or_404(TrustAnchorCertificate, serial_number=serial_number,
                               owner = request.user)
    
    response = HttpResponse(a.details, content_type='text/plain')
    return response  

@login_required
def create_intermediate_anchor_certificate(request, serial_number):
    
    a = get_object_or_404(TrustAnchorCertificate, serial_number=serial_number,
                               owner = request.user)
    
    name = "Create Intermediate Anchor from %s " % (a.common_name) 
    if request.method == 'POST':
        form = TrustAnchorCertificateForm(request.POST)
        if form.is_valid():
            ta = form.save(commit = False)
            ta.common_name = ta.dns
            ta.domain = ta.dns
            ta.owner=request.user
            ta.parent=a
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
                                             'name': name,
                                             'a': a,
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
              'form': TrustAnchorCertificateForm(initial=data),
              'anchor': a
              }
    return render_to_response('generic/bootstrapform.html',
                              RequestContext(request, context,))




@login_required
def certificate_dashboard(request):
    
    active_tas = TrustAnchorCertificate.objects.filter(owner=request.user,
                                                       status="good") | \
                 TrustAnchorCertificate.objects.filter(owner=request.user,
                                                       status="unverified")
    
    return render_to_response("index.html",
                          {'nodes':active_tas},
                          context_instance=RequestContext(request))


@login_required
def view_anchor(request, serial_number):
    #get all active trust anchors decendants and associated domain-bound certs
    anchor = get_object_or_404(TrustAnchorCertificate, serial_number=serial_number,
                               owner = request.user)

    active_children=[]
    revoked_children=[]
    revoked_anchors=[]
    revoked_descandants=[]
    descendant_anchors=[]
    descendant_revoked_anchors=[]
    active_endpoints =[]
    revoked_anchors=[]
    revoked_endpoints =[]
    
    
    for c in anchor.get_children():
        
        if str(c.owner)==str(request.user) and c.status in ("good", "verified"):
             active_children.append(c)
        elif str(c.owner)==str(request.user) and c.status=="revoked":
            revoked_children.append(c)

    for d in anchor.get_descendants():
        
        if str(d.owner)==str(request.user) and d.status in ("good", "verified"):
             descendant_anchors.append(d)
        elif str(d.owner)==str(request.user) and d.status=="revoked":
            descendant_revoked_anchors.append(d)
    
    active_anchors  = [anchor, ] + active_children
    
    revoked_anchors = descendant_revoked_anchors
    
    
    active_endpoints = EndpointCertificate.objects.filter(~Q(trust_anchor__parent = None),
                                                             status="good"
                                                             ) | \
                       EndpointCertificate.objects.filter(~Q(trust_anchor__parent = None),
                                                             status="unverified"
                                                             )| \
                       EndpointCertificate.objects.filter(trust_anchor = anchor,
                                                             status="good"
                                                             )| \
                       EndpointCertificate.objects.filter(trust_anchor = anchor,
                                                             status="unverified"
                                                             )
     
    
    revoked_endpoints = EndpointCertificate.objects.filter(~Q(trust_anchor__parent = None),
                                                             status="revoked")
    # EndpointCertificate.objects.filter(trust_anchor__parent=!None
    #                                                     status="good") | \
    #                     EndpointCertificate.objects.filter(trust_anchor=anchor,
    #                                                 status="unverified")
    #     
    # revoked_endpoints = EndpointCertificate.objects.filter(trust_anchor=anchor,
    #                                                     status="revoked")   
    revoked_certs = revoked_anchors + list(revoked_endpoints)
        
        
    context={ 'anchor': anchor,
              'active_cert_list': active_anchors,
              'active_endpoints': active_endpoints,
              'revoked_cert_list': revoked_certs, 
             }
    
    return render_to_response('anchor.html', RequestContext(request, context,))


@login_required
def create_endpoint_certificate(request, serial_number):
    ta = get_object_or_404(TrustAnchorCertificate, serial_number=serial_number,
                               owner = request.user)
    name = _("Create an Endpoint Certificate for ") + ta.common_name
    if request.method == 'POST':
        form = EndpointCertificateForm(request.POST)
        if form.is_valid():
            c = form.save(commit = False)
            c.common_name = c.dns
            c.domain = c.dns
            c.trust_anchor = ta
            c.save()
            if c.status == "unverified":
                messages.success(request, _("Your Direct endpoint certificate creation request completed successfully."))
            elif c.status == "failed":
                messages.error(request, _("Oops.  Something has gone wrong.  Your certificate creation request failed."))
            
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
           #'dns': dnsguess,
           }
    context= {'name':name,
              'form': EndpointCertificateForm(initial=data)}
    return render_to_response('generic/bootstrapform.html',
                              RequestContext(request, context,))


@login_required
def create_trust_anchor_certificate(request):
    name = _("Create a Top Level Trust Anchor Certificate")
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
            children = EndpointCertificate.objects.filter(trust_anchor = ta)
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
def revoke_endpoint_certificate(request, serial_number):
    
    name = _("Revoke a Domain Bound Certificate")
    dbc = get_object_or_404(EndpointCertificate, serial_number=serial_number,
                               trust_anchor__owner = request.user)
        
    if request.method == 'POST':
        form = RevokeEndpointCertificateForm(request.POST, instance = dbc)
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
              'form': RevokeEndpointCertificateForm(instance = dbc)
              }
    return render_to_response('generic/bootstrapform.html',
                              RequestContext(request, context,))




@login_required
@staff_member_required
def verify_anchor_certificate(request, serial_number):
    
    ta = get_object_or_404(TrustAnchorCertificate, serial_number=serial_number,
                               owner = request.user)
    name = _("Verify Anchor %s") % (ta.common_name)    
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
def verify_endpoint_certificate(request, serial_number):
    
    name = _("Verify a Domain Bound Certificate")
    e = get_object_or_404(EndpointCertificate, serial_number=serial_number,
                               trust_anchor__owner = request.user)
        
    if request.method == 'POST':
        form = VerifyEndpointCertificateForm(request.POST, instance = e)
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
              'form': VerifyEndpointCertificateForm(instance = e)
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
    
    
    