#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import sys
from apps.certificates.models import (AnchorCertificateRevocationList,
                                      TrustAnchorCertificate,
                                      CertificateRevocationList,)

def buildcrls():
    
    
    #removed any old the crl for the CA.
    ca_crl = CertificateRevocationList.objects.all().delete()
    
    #create the crl for the CA.
    ca_crl = CertificateRevocationList.objects.create()
    if ca_crl == "Failed" or ca_crl in ("", None):
        print "A CRL was NOT created for the CA/RA. URL =  %s" % (ca_crl.url)
    else:
        print "A CRL was created for the CA/RA."
    tas = TrustAnchorCertificate.objects.filter(status="good")
    
    for t in tas:
        AnchorCertificateRevocationList.objects.filter(trust_anchor = t).delete()
        c = AnchorCertificateRevocationList.objects.create(trust_anchor = t)
        
        if c.url!="Failed":
            print "A CRL was created for the Trust Anchor %s" % (c.trust_anchor.dns)
        else:
            print  "[CRITICAL ERROR] A CRL was not created for the Trust Anchor %s" % (c.trust_anchor.dns)
def run():
    try:
        buildcrls()
    except:
        print "Error."
        print sys.exc_info()
