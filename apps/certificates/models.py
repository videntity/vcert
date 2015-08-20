#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf import settings
from django.db import models
import datetime, os, json
import pdb
from django.contrib.auth.models import User
from localflavor.us.models import PhoneNumberField
from localflavor.us.us_states import US_STATES
from cautils import (create_endpoint_certificate, create_trust_anchor_certificate,
                     revoke, build_crl, write_verification_message,
                     chain_keys_in_list, create_crl_conf, write_x5c_message,
                     revoke_from_anchor, build_anchor_crl)
import uuid
import sha
from fileutils import SimpleS3
from django.core.mail import send_mail, EmailMessage
from shutil import copyfile
#Note 4096 is incompatiable with Java Direct RI.
RSA_KEYSIZE_CHOICES = ((1024,1024), (2048,2048),(4096,4096),)
STATUS_CHOICES = (  ('incomplete','incomplete'),
                    ('unverified', 'unverified'),
                    ('failed','failed'),
                    ('good','good'),
                    ('revoked','revoked'))


EXPIRE_CHOICES = ((1,"1 Day"),(365,"1 Year"),(730,"2 Years"))

class TrustAnchorCertificate(models.Model):

    owner               = models.ForeignKey(User)
    status              = models.CharField(max_length=10, default="incomplete",
                                         choices=STATUS_CHOICES,
                                         editable=False)
    sha256_digest       = models.CharField(max_length=64, default="", blank=True,)
    sha1_fingerprint    = models.CharField(max_length=64, default="", blank=True,)
                                         #editable=False)
    serial_number       = models.CharField(max_length=64, default=-01, blank=True,)
                                           #editable=False)
                                                                               
    domain              = models.CharField(max_length=512, default="",
                              help_text= "We recommend using a top-level domain here (e.g. example.com)")
    common_name         = models.CharField(max_length=512, default="",
                            help_text= "Always set this to the same value as domain")
    dns                 = models.CharField(verbose_name="DNS", max_length=512, default="",
                            help_text= """We recommend using a top-level domain here (e.g. example.com).
                             This field should match the email field exactly.
                            """)
    email               = models.CharField(max_length=512, default="",             
                            help_text= """We recommend using a top-level domain here (e.g. example.com).
                                This field should match the DNS field exactly.""")
    rsa_keysize         = models.IntegerField(default=2048,
                                            choices= RSA_KEYSIZE_CHOICES)
    country             = models.CharField(max_length=2, default = "US")
    state               = models.CharField(blank=True, max_length=2,
                                        choices=US_STATES,)
    city                = models.CharField(max_length=64,
                            help_text="No slashes. Letters, numbers, and dashes are okay. ")
    organization        = models.CharField(max_length=64,
                            help_text="No slashes. Letters, numbers, and dashes are okay. ")
    private_key_path    = models.CharField(max_length=1024, default="",
                                        blank=True)
    public_key_path     = models.CharField(max_length=1024, default="",
                                        blank=True)
    completed_dir_path  = models.CharField(max_length=1024, default="",
                                        blank=True)
    
    private_expire_days  = models.IntegerField(default="1",
                                        blank=True)
    private_zip_name         = models.CharField(max_length=1024, default="",
                                               blank=True)
    presigned_zip_url       = models.CharField(max_length=1024, default="",
                                               blank=True)
    
    presigned_zip_s3        = models.CharField(max_length=1024, default="",
                                               blank=True)
    
    public_cert_pem_url         = models.CharField(max_length=1024, default="",
                                               blank=True)
    public_cert_pem_s3          = models.CharField(max_length=1024, default="",
                                               blank=True)
    public_cert_der_url         = models.CharField(max_length=1024, default="",
                                               blank=True)
    public_cert_der_s3         = models.CharField(max_length=1024, default="",
                                               blank=True)
    public_cert_status_url      = models.CharField(max_length=1024, default="",
                                               blank=True)
    public_cert_status_sha1_url = models.CharField(max_length=1024, default="",
                                               blank=True)
    public_cert_x5c_url         = models.CharField(max_length=1024, default="",
                                               blank=True)
    
    private_p12_url            = models.CharField(max_length=1024, default="",
                                               blank=True)
    
    private_der_url            = models.CharField(max_length=1024, default="",
                                               blank=True)
    
    private_pem_url            = models.CharField(max_length=1024, default="",
                                               blank=True)
    revoke                  = models.BooleanField(default=False)
    expired                 = models.BooleanField(default=False, editable=False)
    verified                = models.BooleanField(default=False,)
    verified_message_sent   = models.BooleanField(default=False,)
    rcsp_response           = models.TextField(max_length=512,
                                         blank=True, default="")
    notes                   = models.TextField(max_length=1024,
                                         blank=True, default="")
    npi                     = models.CharField(max_length=20,
                                         default="", blank=True)
    contact_first_name      = models.CharField(max_length=100,
                                                  default="")
    contact_last_name       = models.CharField(max_length=100,
                                                  default="")
    contact_email           = models.EmailField()
    contact_mobile_phone    = PhoneNumberField(max_length = 15, blank = True)
    contact_land_phone      = PhoneNumberField(max_length = 15, blank = True)
    contact_fax             = PhoneNumberField(max_length = 15, blank = True)
    expiration_date         = models.DateField(blank=True, editable=False)
    expire_days             = models.IntegerField(default=730,
                                                  choices = EXPIRE_CHOICES)
    creation_date           = models.DateField(auto_now_add=True)
    
    def __unicode__(self):
        return '%s (%s) Status=%s, Created %s.' % (self.domain,
                            self.serial_number, self.status, self.creation_date)
    
    class Meta:
        get_latest_by = "creation_date"
        ordering = ('-creation_date',)
        
    def save(self, **kwargs):
             
        if not self.sha256_digest and self.revoke==False:
            """I'm a new certificate"""

            today = datetime.date.today ()
            self.expiration_date = today + datetime.timedelta(
                                                    days=self.expire_days)
            result = create_trust_anchor_certificate(
                                        common_name     = self.common_name,
                                        email           = self.email,
                                        dns             = self.dns,
                                        expires         = self.expire_days,
                                        organization    = self.organization,
                                        city            = self.city,
                                        state           = self.state,
                                        country         = self.country,
                                        rsakey          = self.rsa_keysize,
                                        user            = self.owner.username)
            
            self.sha256_digest      = result['sha256_digest']
            self.serial_number      = result['serial_number']
            self.sha1_fingerprint   = result['sha1_fingerprint']
            self.notes              = result['notes']
            self.private_zip_name   = result['anchor_zip_download_file_name']
            self.status             = result['status']
            self.private_key_path   = result['private_key_path']
            self.public_key_path    = result['public_key_path']
            self.completed_dir_path = result['completed_dir_path']
            
            #send the verifier an email notification
            msg = """
            <html>
            <head>
            </head>
            <body>
            A new Direct Trust Anchor was created by %s and requires your review.
            Here is a link for the domain %s:
            <ul>
            <li><a href="/admin/certificates/trustanchorcertificate/%s">%s</a></li>
            </ul>
            </body>
            </html>
            """ % (self.organization, self.domain, self.id, self.domain)
            if settings.SEND_CA_EMAIL:
                subject = "[%s]A new Trust Anchor certificate requires verification" % (settings.ORGANIZATION_NAME)
                msg = EmailMessage(subject,
                               msg,
                               settings.EMAIL_HOST_USER,
                               [settings.CA_VERIFIER_EMAIL,])            
                msg.content_subtype = "html"  # Main content is now text/html
                msg.send()
                        
            
            
            # Create the CRL config file
            crl_result = create_crl_conf(
                      common_name           = self.common_name,
                        email               = self.email,
                        dns                 = self.dns,
                        anchor_dns          = self.dns,
                        expires             = self.expire_days,
                        organization        = self.organization,
                        city                = self.city,
                        state               = self.state,
                        country             = self.country,
                        rsakey              = self.rsa_keysize,
                        user                = self.owner.username,
                        public_key_path     = result['public_key_path'],
                        private_key_path    = result['private_key_path'],
                        completed_anchor_dir= result['completed_dir_path'])


            return super(TrustAnchorCertificate, self).save(**kwargs)
           

            
        if self.verified and not self.verified_message_sent and \
           self.status in  ('unverified', 'good'):
            """This is the verify routine"""
            
            self.status = "good"
            # Get the response
            rcsp_result = write_verification_message(self.serial_number,
                                                     self.common_name,
                                                    "good",
                                                    self.sha1_fingerprint,
                                                    )
            #Write it to db
            self.rcsp_response = rcsp_result
            fn = "%s.json" % (self.serial_number)
            #Write it to file
            fp = os.path.join(self.completed_dir_path, fn)
            
            f = open(fp, "w")
            f.write(str(rcsp_result))
            f.close()
            
            #Upload the RCSP file to S3
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                s=SimpleS3()
                self.public_cert_status_url  = s.store_in_s3(fn, fp,
                                    bucket=settings.RCSP_BUCKET, public=True)
                self.public_cert_status_url = s.build_pretty_url(
                                                     self.public_cert_status_url,
                                                    settings.RCSP_BUCKET)
            #Upload the RCSP locally
            if "LOCAL" in  settings.CA_PUBLICATION_OPTIONS:   
                dest = os.path.join(settings.LOCAL_RCSP_PATH, self.owner.username, self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                
                dest_file = os.path.join(dest, fn)
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_status_url = "%s%s/%s/%s" % (settings.RCSP_URL_PREFIX, self.owner.username, self.dns, fn)
            
            #Calculate the SHA1 fingerprint & write it to a file
            digestsha1 = json.dumps(sha.sha1_from_filepath(fp), indent =4)
            fn = "%s-sha1.json" % (self.serial_number)
            fp = os.path.join(self.completed_dir_path, fn)
            f = open(fp, "w")
            f.write(str(digestsha1)) 
            f.close()
                
            #Upload the RCSP SHA1 Digest to S3
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                self.public_cert_status_sha1_url = s.store_in_s3(fn, fp,
                                            bucket=settings.RCSPSHA1_BUCKET,
                                            public=True)
                self.public_cert_status_sha1_url= s.build_pretty_url(
                                            self.public_cert_status_sha1_url,
                                            settings.RCSPSHA1_BUCKET)
            
            if "LOCAL" in  settings.CA_PUBLICATION_OPTIONS:   
                dest = os.path.join(settings.LOCAL_RCSPSHA1_PATH, self.owner.username, self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                
                dest_file = os.path.join(dest, fn)
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_status_sha1_url = "%s%s/%s/%s" % (settings.RCSPSHA1_URL_PREFIX, self.owner.username, self.dns, fn)
                 
            
            # JOSE X5C-------------------------------------------------------------
            #get all the files
            certfilelist = [settings.CA_PUBLIC_CERT, self.public_key_path]
            
            fn = "%s-chain.pem" % (self.dns)
            chained_cert_path = os.path.join(self.completed_dir_path, fn )
            certlist = chain_keys_in_list(chained_cert_path, certfilelist)
            #write the json
            
            x5c_json = write_x5c_message(self.email, certlist)
        
            # set the filename ------------------------------------------------
            fn = "%s-x5c.json" % (self.serial_number)
            
            # Write it to file ------------------------------------------------
            fp = os.path.join(self.completed_dir_path, fn)
            
            f = open(fp, "w")
            f.write(str(x5c_json))
            f.close()
            
            #Upload the x5c file to S3
            s=SimpleS3()
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                key = "x5c/" + fn
                self.public_cert_x5c_url = s.store_in_s3(key, fp,
                                        bucket=settings.X5C_BUCKET,
                                        public=True)
                self.public_cert_x5c_url = s.build_pretty_url(
                                                     self.public_cert_x5c_url,
                                                    settings.X5C_BUCKET)
             
            if "LOCAL" in  settings.CA_PUBLICATION_OPTIONS:   
                dest = os.path.join(settings.LOCAL_PUBLIC_PATH, self.owner.username, self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)

                dest_file = os.path.join(dest, fn)
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_x5c_url = "%s%s/%s/%s" % (settings.PUBLIC_CERTS_URL_PREFIX, self.owner.username, self.dns, fn)
                 

              
            #Upload the PEM and DER public certificates  -----------------------
            
            #PEM ------------------------
            fn = "%s.pem" % (self.dns)
            key = "%s/%s/%s" % ( self.owner.username ,self.dns, fn )
            fp = os.path.join(self.completed_dir_path, fn)
            
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                self.public_cert_pem_url = s.store_in_s3(key, fp,
                                                bucket=settings.PUBCERT_BUCKET,
                                                public=True)
                self.public_cert_pem_url= s.build_pretty_url(
                                                    self.public_cert_pem_url,
                                                    settings.PUBCERT_BUCKET)
                
                self.public_cert_pem_s3 = json.dumps({"bucket": settings.PUBCERT_BUCKET,
                                                       "key": key})
            if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:

                dest = os.path.join(settings.LOCAL_AIA_PATH, self.owner.username, self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                

                dest_file = os.path.join(dest, fn)
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_pem_url = "%s%s/%s/%s" % (settings.AIA_URL_PREFIX, self.owner.username, self.dns, fn)
            
            
            #DER -------------------------
            fn = "%s.der" % (self.dns)
            key = "%s/%s/%s" % (self.owner.username, self.dns, fn ) 
            fp = os.path.join(self.completed_dir_path, fn)
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                self.public_cert_der_url = s.store_in_s3(key, fp,
                                                bucket=settings.PUBCERT_BUCKET,
                                                public=True)
                self.public_cert_der_url = s.build_pretty_url(
                                                    self.public_cert_der_url,
                                                    settings.PUBCERT_BUCKET)
                self.public_cert_der_s3 = json.dumps({"bucket": settings.PUBCERT_BUCKET,
                                                       "key": key})
            
            if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:
                #
                dest = os.path.join(settings.LOCAL_AIA_PATH, self.owner.username,
                                    self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                
                dest_file = os.path.join(dest, fn)
                
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_der_url = "%s%s/%s/%s" % (settings.AIA_URL_PREFIX, self.owner.username, self.dns, fn)
            
            
            #Send the zip file and expire in one week
            fn = self.private_zip_name
            fp = os.path.join(self.completed_dir_path, self.private_zip_name)
            key = "%s/%s/%s" % (self.owner.username, self.dns, fn ) 
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                self.presigned_zip_url  = s.store_in_s3(key, fp,
                                        bucket = settings.PUBCERT_BUCKET,
                                        public = True)
                
                self.presigned_zip_url = s.build_pretty_url(
                                                    self.presigned_zip_url,
                                                    settings.PUBCERT_BUCKET)
                
                #We dont need this for trust anchos since there is no private key give.
                #self.presigned_zip_url = s.get_presignedurl(key, bucket = settings.PRIVCERT_BUCKET) 
                
                self.presigned_zip_s3 = json.dumps({"bucket": settings.PUBCERT_BUCKET,
                                                       "key": key})
            
            
            
            
            
            """ Mark the certificate as verified """
            self.verified = True
            
            #send the verification email.
            msg = """
            <html>
            <head>
            </head>
            <body>
            Congratulations. Your trust anchor has for %s been verified.
            Here are some links to your public certificates and related status
            information.
            
            <ul>
            <li><a href="%s">PEM File                             - %s</a></li>
            <li><a href="%s">DER File                             - %s</a></li>
            <li><a href="%s">Status                               - %s</a></li>
            </ul>
            </body>
            </html>
            """ % (self.domain,
                   self.public_cert_pem_url,self.public_cert_pem_url,
                   self.public_cert_der_url,self.public_cert_der_url,
                   self.public_cert_status_url,self.public_cert_status_url,
                      )
            if settings.SEND_CA_EMAIL:
                subject = "[%s]Your Trust Anchor Certificate has been verified" %(settings.ORGANIZATION_NAME)
                msg = EmailMessage(subject,
                               msg,
                               settings.EMAIL_HOST_USER,
                               [self.owner.email, self.contact_email])            
                msg.content_subtype = "html"  # Main content is now text/html
                msg.send()
            
            
            self.verified_message_sent = True
        
            
        if self.revoke and self.status != "revoked":
                self.status = "revoked"
                
                # Build the  RCSP response
                # Get the status
                self.rcsp_response =  write_verification_message(self.serial_number,
                                                     self.common_name,
                                                    "revoked",
                                                    self.sha1_fingerprint,
                                                    )
                fn = "%s.json" % (self.serial_number)
                
                #Write it to file
                fp = os.path.join(self.completed_dir_path, fn)
                
                f = open(fp, "w")
                f.write(str(self.rcsp_response))
                f.close()
                
                #Upload the RCSP file to S3
                if "S3" in settings.CA_PUBLICATION_OPTIONS:
                    s=SimpleS3()
                    url = s.store_in_s3(fn, fp, bucket=settings.RCSP_BUCKET,
                                    public=True)
                if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:
                
                    dest = os.path.join(settings.LOCAL_RCSP_PATH, self.owner.username, self.dns)
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                    
                    dest_file = os.path.join(dest, fn)
                    
                    os.umask(0000)
                    copyfile(fp, dest_file)
                    os.chdir(settings.BASE_DIR)
                    self.public_cert_status_sha1_url = "%s%s/%s/%s" % (settings.RCSP_URL_PREFIX, self.owner.username, self.dns, fn)
                    
                    
                    
                #Calculate the SHA1 fingerprint & write it to a file
                digestsha1 = json.dumps(sha.sha1_from_filepath(fp), indent =4)
                fn = "%s-sha1.json" % (self.serial_number)
                fp = os.path.join(self.completed_dir_path, fn)
                f = open(fp, "w")
                f.write(str(digestsha1)) 
                f.close()
                if "S3" in settings.CA_PUBLICATION_OPTIONS:          
                    #Upload the RCSP SHA! Digest to S3
                    url = s.store_in_s3(fn, fp, bucket=settings.RCSPSHA1_BUCKET,
                                    public=True)
                
                if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:
                
                    dest = os.path.join(settings.LOCAL_RCSPSHA1_PATH, self.owner.username, self.dns)
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                    
                    dest_file = os.path.join(dest, fn)
                    
                    os.umask(0000)
                    copyfile(fp, dest_file)
                    os.chdir(settings.BASE_DIR)
                    self.public_cert_status_sha1_url = "%s%s/%s/%s" % (settings.RCSPSHA1_URL_PREFIX, self.owner.username, self.dns, fn)
                    
                    
                
                    
                
                    #Delete all the old files:
                    #PEM, DIR, ZIP
                    if self.presigned_zip_s3:
                        s3info = json.loads(self.presigned_zip_s3) 
                        self.presigned_zip_url = s.delete_in_s3(    s3info['bucket'],
                                                                s3info['key'],
                                                            )
                
                    if self.public_cert_der_s3:
                        s3info = json.loads(self.public_cert_der_s3) 
                        self.public_cert_der_url = s.delete_in_s3(  s3info['bucket'],
                                                                s3info['key'],
                                                            )
                
                    if self.public_cert_pem_s3:
                        s3info = json.loads(self.public_cert_pem_s3) 
                        self.public_cert_pem_url = s.delete_in_s3(  s3info['bucket'],
                                                                s3info['key'],
                                                            )
                
                #revoke the cert
                revoke(self)
                
            
        super(TrustAnchorCertificate, self).save(**kwargs)
        
    def delete(self, **kwargs):
        self.revoked = True
        self.status = "revoked"
    
        # Build the RCSP response
        rcsp_result = write_verification_message(self.serial_number,
                                             self.common_name,
                                            "revoked",
                                            self.sha1_fingerprint,
                                            )
        #Write it to db
        self.rcsp_response = rcsp_result
        fn = "%s.json" % (self.serial_number)
        #Write it to file
        fp = os.path.join(self.completed_dir_path, fn)
        
        f = open(fp, "w")
        f.write(str(rcsp_result))
        f.close()
        
        #Upload the RCSP file to S3
        s=SimpleS3()
        if "S3" in settings.CA_PUBLICATION_OPTIONS:
            url = s.store_in_s3(fn, fp, bucket=settings.RCSP_BUCKET,
                            public=True)

            
        #Calculate the SHA1 fingerprint & write it to a file
        digestsha1 = json.dumps(sha.sha1_from_filepath(fp), indent =4)
        fn = "%s-sha1.json" % (self.serial_number)
        fp = os.path.join(self.completed_dir_path, fn)
        f = open(fp, "w")
        f.write(str(digestsha1)) 
        f.close()
            
        #Upload the RCSP SHA! Digest to S3
        if "S3" in settings.CA_PUBLICATION_OPTIONS:
            url = s.store_in_s3(fn, fp, bucket=settings.RCSPSHA1_BUCKET,
                            public=True)
        
        #Revoke the cert.
        revoke(self)
        super(TrustAnchorCertificate, self).save(**kwargs)
        

class DomainBoundCertificate(models.Model):
    trust_anchor      = models.ForeignKey(TrustAnchorCertificate)
    status            = models.CharField(max_length=10, default="incomplete",
                                         choices=STATUS_CHOICES)
    sha256_digest     = models.CharField(max_length=64, default="", blank=True,)
    sha1_fingerprint  = models.CharField(max_length=64, default="", blank=True,)
                                         #editable=False)
    serial_number     = models.CharField(max_length=64, default=-01, blank=True,)
                                         #editable=False)
    domain            = models.CharField(max_length=512, default="",
                                         help_text="This value should match the email.")
    common_name       = models.CharField(max_length=512, default="")
    dns               = models.CharField(max_length=512, default="",
                                         verbose_name = "DNS",
                            help_text="""This should always match the email field,
                                         unless you are creating a "bad"
                                         certificate for testing.
                                      """)
    email           = models.CharField(max_length=512, default="", verbose_name ="Email or Domain",
                            help_text="""For email-bound certificate use an
                            email address (e.g. john@direct.example.com)
                            For a domain-bound certificate use a domain (e.g.
                            "direct.example.com).""")                                                                                               
    rsa_keysize                 = models.IntegerField(choices= RSA_KEYSIZE_CHOICES, default=2048)
    country                     = models.CharField(max_length=2, default = "US")
    state                       = models.CharField(blank=True, max_length=2,
                                        choices=US_STATES)
    city                        = models.CharField(max_length=64,
                                                   help_text="Letters, numbers, and dashes okay. No slashes")
    organization                = models.CharField(max_length=64,
                                                   help_text="Letters, numbers, and dashes okay. No slashes")
    completed_dir_path          = models.CharField(max_length=1024, default="",
                                        blank=True)
    public_key_path             = models.CharField(max_length=1024, default="",
                                        blank=True)

    private_expire_days         = models.IntegerField(default="1",
                                        blank=True)
    
    private_zip_name            = models.CharField(max_length=512, default="",
                                               blank=True)
    
    presigned_zip_url           = models.CharField(max_length=512, default="",
                                               blank=True)
    presigned_zip_s3            = models.CharField(max_length=512, default="",
                                               blank=True)
    
    public_cert_der_url         = models.CharField(max_length=1024, default="",
                                               blank=True)
    public_cert_der_s3         = models.CharField(max_length=1024, default="",
                                               blank=True)
    
        
    public_cert_pem_url         = models.CharField(max_length=1024, default="",
                                               blank=True)
    public_cert_pem_s3         = models.CharField(max_length=1024, default="",
                                               blank=True)
    

    private_p12_url            = models.CharField(max_length=1024, default="",
                                               blank=True)
    
    private_der_url            = models.CharField(max_length=1024, default="",
                                               blank=True)
    
    private_pem_url            = models.CharField(max_length=1024, default="",
                                               blank=True)
    
    public_cert_status_url      = models.CharField(max_length=1024, default="",
                                               blank=True)
    
    public_cert_status_sha1_url = models.CharField(max_length=1024, default="",
                                               blank=True)
    
    public_cert_x5c_url         = models.CharField(max_length=1024, default="",
                                               blank=True)
    
    revoke                      = models.BooleanField(default=False)
    revoked_note                = models.TextField(max_length=512,
                                         blank=True, default="")
    verified                    = models.BooleanField(default=False)
    verified_message_sent       = models.BooleanField(default=False)
    rcsp_response               = models.TextField(max_length=512,
                                         blank=True, default="")
    notes                       = models.TextField(max_length=1024,
                                         blank=True, default="")
    npi                         = models.CharField(max_length=20,
                                         default="", blank=True)
    contact_first_name          = models.CharField(max_length=100,
                                                  default="", blank=True)
    contact_last_name           = models.CharField(max_length=100,
                                                  default="", blank=True)
    contact_email               = models.EmailField()
    contact_mobile_phone        = PhoneNumberField(max_length = 15, blank = True)
    contact_land_phone          = PhoneNumberField(max_length = 15, blank = True)
    contact_fax                 = PhoneNumberField(max_length = 15, blank = True)
    expiration_date             = models.DateField(blank=True, editable=False)
    expire_days                 = models.IntegerField(default=365,
                                                  choices=EXPIRE_CHOICES )
    creation_date               = models.DateField(auto_now_add=True)
    

    
    def __unicode__(self):
        return '%s (%s) Status=%s, Created %s, Issued by %s' % (self.domain,
                            self.serial_number, self.status,  self.creation_date,
                            self.trust_anchor.organization)
    class Meta:
        get_latest_by = "creation_date"
        ordering = ('-creation_date',)
        verbose_name = "endpoint certificate"
        
    def save(self, **kwargs):
        if not self.sha256_digest and self.status=="incomplete":
            print "We've only just begun...I'm new."
            
            today = datetime.date.today ()
            self.expiration_date = today + datetime.timedelta(
                                                    days=self.expire_days)
            
            
            result = create_endpoint_certificate(
                        common_name         = self.common_name,
                        email               = self.email,
                        dns                 = self.dns,
                        anchor_dns          = self.trust_anchor.dns,
                        expires             = self.expire_days,
                        organization        = self.organization,
                        city                = self.city,
                        state               = self.state,
                        country             = self.country,
                        rsakey              = self.rsa_keysize,
                        aia_der             = self.trust_anchor.public_cert_der_url,
                        user                = self.trust_anchor.owner.username,
                        public_key_path     = self.trust_anchor.public_key_path,
                        private_key_path    = self.trust_anchor.private_key_path,
                        completed_anchor_dir = self.trust_anchor.completed_dir_path
                        )
            
            
            sha256_digest           = result['sha256_digest']
            self.serial_number      = result['serial_number']
            self.sha1_fingerprint   = result['sha1_fingerprint']
            self.notes              = result['notes']
            self.private_zip_name   = result['anchor_zip_download_file_name']
            self.status             = result['status']
            self.completed_dir_path = result['completed_dir_path']
            self.public_key_path     = result['public_key_path']
            
            #send the verifier an email notification
            msg = """
            <html>
            <head>
            </head>
            <body>
            A new Direct Domain Bound certificate was created by %s and requires your review.
            Here is a link:
            <ul>
            <li><a href="http://caconsole.nist.gov/admin/certificates/domainboundcertificate/%s">%s</a></li>
            </ul>
            </body>
            </html>
            """ % (self.organization, self.id, self.domain,
                   )
            if settings.SEND_CA_EMAIL :
                subject = "[%s]A new Domain-Bound Certificate requires verification" % (settings.ORGANIZATION_NAME)
                msg = EmailMessage(subject,  msg,
                               settings.EMAIL_HOST_USER,
                               [settings.CA_VERIFIER_EMAIL,])            
                msg.content_subtype = "html"  # Main content is now text/html
                msg.send()
            
            
            super(DomainBoundCertificate, self).save(**kwargs)
            return
        
        if self.verified and not self.verified_message_sent and \
           self.status in  ('unverified', 'good'):
            
            
            """ Mark the certificate as verified"""
            self.verified = True
            
            self.status = "good"
            # RCSP ------------------------------------------------------------
            rcsp_result = write_verification_message(self.serial_number,
                                                     self.common_name,
                                                    "good",
                                                    self.sha1_fingerprint,
                                                    )
            #Write it to db
            self.rcsp_response = rcsp_result
        
            #set the filename
            fn = "%s.json" % (self.serial_number)
            #Write it to file
            fp = os.path.join(self.completed_dir_path, fn)
            
            f = open(fp, "w")
            f.write(str(rcsp_result))
            f.close()
            
            #Upload the RCSP file to S3
            s=SimpleS3()
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                self.public_cert_status_url = s.store_in_s3(fn, fp,
                                                bucket=settings.RCSP_BUCKET,
                                                public=True)

                self.public_cert_status_url= s.build_pretty_url(
                                                    self.public_cert_status_url,
                                                    settings.RCSP_BUCKET)
            
            
            if "LOCAL" in  settings.CA_PUBLICATION_OPTIONS:   
                dest = os.path.join(settings.LOCAL_RCSP_PATH, self.trust_anchor.owner.username, self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                
                dest_file = os.path.join(dest, fn)
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_status_url = "%s%s/%s/%s" % (settings.RCSP_URL_PREFIX, self.trust_anchor.owner.username, self.dns, fn)
                

            #Calculate the RCSP SHA1 fingerprint & write it to a file
            digestsha1 = json.dumps(sha.sha1_from_filepath(fp), indent =4)
            fn = "%s-sha1.json" % (self.serial_number)
            fp = os.path.join(self.completed_dir_path, fn)
            f = open(fp, "w")
            f.write(str(digestsha1)) 
            f.close()
                
            #Upload the RCSP SHA1 Digest to S3
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                self.public_cert_status_sha1_url = s.store_in_s3(fn, fp,
                        bucket=settings.RCSPSHA1_BUCKET,public=True)
            
            if "LOCAL" in  settings.CA_PUBLICATION_OPTIONS:   
                dest = os.path.join(settings.LOCAL_RCSPSHA1_PATH, self.trust_anchor.owner.username, self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                
                dest_file = os.path.join(dest, fn)
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_status_sha1_url = "%s%s/%s/%s" % (settings.RCSPSHA1_URL_PREFIX, self.trust_anchor.owner.username, self.dns, fn)
                                          
            
            #JOSE x5c ---------------------------------------------------------    
            #get all the files
            certfilelist = [ settings.CA_PUBLIC_CERT,
                                self.trust_anchor.public_key_path,
                                self.public_key_path ]
            
            fn = "%s-chain.pem" % (self.dns)
            chained_cert_path = os.path.join(self.completed_dir_path, fn )
            certlist = chain_keys_in_list(chained_cert_path, certfilelist)
            #write the json
            
            x5c_json = write_x5c_message(self.email, certlist)
        
            # set the filename ------------------------------------------------
            fn = "%s-x5c.json" % (self.serial_number)
            
            # Write it to file ------------------------------------------------
            fp = os.path.join(self.completed_dir_path, fn)
            
            f = open(fp, "w")
            f.write(str(x5c_json))
            f.close()
            
            #Upload the x5c file to S3
            s=SimpleS3()
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                key = "x5c/" + fn
                self.public_cert_x5c_url = s.store_in_s3(key, fp,
                                        bucket=settings.X5C_BUCKET,
                                        public=True)
                self.public_cert_x5c_url= s.build_pretty_url(self.public_cert_x5c_url,
                                                              settings.X5C_BUCKET)
                
            if "LOCAL" in  settings.CA_PUBLICATION_OPTIONS:   
                dest = os.path.join(settings.LOCAL_PUBLIC_PATH, self.trust_anchor.owner.username, self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)

                dest_file = os.path.join(dest, fn)
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_x5c_url = "%s%s/%s/%s" % (settings.PUBLIC_CERTS_URL_PREFIX,
                                                           self.trust_anchor.owner.username, self.dns, fn)
                
            
            
            
            #Upload the PEM and DER public certificates  
            
            # PEM ----------------------------------------------------
            fn = "%s.pem" % (self.dns)
            key = "%s/%s/endpoints/%s" % (self.trust_anchor.owner.username,
                                          self.trust_anchor.dns, fn )
            
            fp = os.path.join(self.completed_dir_path, fn)
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                self.public_cert_pem_url = s.store_in_s3(key, fp,
                                                    bucket=settings.PUBCERT_BUCKET,
                                                    public=True)
                
                self.public_cert_pem_url = s.build_pretty_url(self.public_cert_pem_url,
                                                              settings.PUBCERT_BUCKET)
                self.public_cert_pem_s3  =  json.dumps({"bucket": settings.PUBCERT_BUCKET,
                                                          "key": key })
                
            
            if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:

                dest = os.path.join(settings.LOCAL_PUBLIC_PATH, self.trust_anchor.owner.username, self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                

                dest_file = os.path.join(dest, fn)
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_pem_url = "%s%s/%s/%s" % (settings.PUBLIC_CERTS_URL_PREFIX,
                                                           self.trust_anchor.owner.username, self.dns, fn)
            
                
            # DER ---------------------------------------------------
            fn = "%s.der" % (self.dns)
            key = "%s/%s/%s" % (self.trust_anchor.owner.username, self.dns,
                                   fn )
            fp = os.path.join(self.completed_dir_path, fn)
            #print "S3 --------------------", key, fp
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                self.public_cert_der_url = s.store_in_s3(key, fp, bucket=settings.PUBCERT_BUCKET,
                               public=True)
                self.public_cert_der_url= s.build_pretty_url(self.public_cert_der_url,
                                                              settings.PUBCERT_BUCKET)
                self.public_cert_der_s3 =  json.dumps({"bucket": settings.PUBCERT_BUCKET,
                                                          "key": key })
            
            if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:

                dest = os.path.join(settings.LOCAL_PUBLIC_PATH, self.trust_anchor.owner.username, self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                dest_file = os.path.join(dest, fn)
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_der_url = "%s%s/%s/%s" % (settings.PUBLIC_CERTS_URL_PREFIX,
                                                           self.trust_anchor.owner.username, self.dns, fn)
            
            #PRIVATE CERTS -----------------------------------------------------------------------
            random_string = str(uuid.uuid4())
            
            #P12 --------------------------------------------------------------
            fn = "%s.p12" % (self.dns)
            key = "%s/%s/%s/%s" % (random_string, self.trust_anchor.owner.username, self.dns,
                                   fn )
            fp = os.path.join(self.completed_dir_path, fn)
            #print "S3 --------------------", key, fp
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                self.private_p12_url = s.store_in_s3(key, fp, bucket=settings.PRIVCERT_BUCKET,
                               public=True)
                self.private_p12_url= s.build_pretty_url(self.private_p12_url,
                                                              settings.PRIVCERT_BUCKET)
                self.private_p12_s3 =  json.dumps({"bucket": settings.PRIVCERT_BUCKET,
                                                          "key": key })
            
            if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:

                dest = os.path.join(settings.LOCAL_PRIVATE_PATH, random_string, self.trust_anchor.owner.username,
                                    self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                dest_file = os.path.join(dest, fn)
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.private_p12_url = "%s%s/%s/%s/%s" % (settings.PRIVATE_URL_PREFIX, random_string,
                                                            self.trust_anchor.owner.username, self.dns, fn)
            
            #DER --------------------------------------------------------------
            fn = "%s.der" % (self.dns)
            key = "%s/%s/%s/%s" % (random_string, self.trust_anchor.owner.username, self.dns,
                                   fn )
            fp = os.path.join(self.completed_dir_path, fn)
            #print "S3 --------------------", key, fp
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                self.private_der_url = s.store_in_s3(key, fp, bucket=settings.PRIVCERT_BUCKET,
                               public=True)
                self.private_der_url= s.build_pretty_url(self.private_der_url,
                                                              settings.PRIVCERT_BUCKET)
                self.private_der_s3 =  json.dumps({"bucket": settings.PRIVCERT_BUCKET,
                                                          "key": key })
            
            if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:

                dest = os.path.join(settings.LOCAL_PRIVATE_PATH, random_string, self.trust_anchor.owner.username,
                                    self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                dest_file = os.path.join(dest, fn)
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.private_der_url = "%s%s/%s/%s/%s" % (settings.PRIVATE_URL_PREFIX, random_string,
                                                            self.trust_anchor.owner.username, self.dns, fn)
            
            
             # PEM --------------------------------------------------------------
            fn = "%s.pem" % (self.dns)
            key = "%s/%s/%s/%s" % (random_string, self.trust_anchor.owner.username, self.dns,
                                   fn )
            fp = os.path.join(self.completed_dir_path, fn)
            #print "S3 --------------------", key, fp
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                self.private_pem_url = s.store_in_s3(key, fp, bucket=settings.PRIVCERT_BUCKET,
                               public=True)
                self.private_pem_url= s.build_pretty_url(self.private_pem_url,
                                                              settings.PRIVCERT_BUCKET)
                self.private_pem_s3 =  json.dumps({"bucket": settings.PRIVCERT_BUCKET,
                                                          "key": key })
            
            if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:

                dest = os.path.join(settings.LOCAL_PRIVATE_PATH, random_string, self.trust_anchor.owner.username,
                                    self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                dest_file = os.path.join(dest, fn)
                
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.private_pem_url = "%s%s/%s/%s/%s" % (settings.PRIVATE_URL_PREFIX, random_string,
                                                            self.trust_anchor.owner.username, self.dns, fn)
            
            
            ##Send the zip file and expire in one week
            #fp = os.path.join(self.completed_dir_path, self.private_zip_name)
            #key = str(self.private_zip_name)
            #if "S3" in settings.CA_PUBLICATION_OPTIONS:
            #    url = s.store_in_s3(key, fp, bucket = settings.PRIVCERT_BUCKET)
            #
            #    self.presigned_zip_url = s.get_presignedurl(key, bucket = settings.PRIVCERT_BUCKET) 
            #    self.presigned_zip_s3  =  json.dumps({"bucket": settings.PRIVCERT_BUCKET,
            #                                              "key": key })
            #
            #
            #send the verification email.
            msg = """
            <html>
            <head>
            </head>
            <body>
            Congratulations. Your domain bound certificate has been verified.
            Below are links to your public certificates and related status information.
            Please login into <a href="http://caconsole.nist.gov">caconsole.nist.gov</a>
            to retrieve your private certificates for this domain.
            <ul>
                <li><a href="%s">PEM File -  %s  </a></li>
                <li><a href="%s">DER File -  %s </a></li>
                <li><a href="%s">Status   -  %s  </a></li>

            </ul>
            
            <p>For security purposes you must
            <a href="https://console.directca.org">login</a> and download the
            private certificates within 72 hours of this email.  
            </p>
            
            </body>
            </html>
            """ % (self.public_cert_pem_url,            self.public_cert_pem_url,
                   self.public_cert_der_url,            self.public_cert_der_url,
                   self.public_cert_status_url,         self.public_cert_status_url,
                   )
            if settings.SEND_CA_EMAIL:
                subject = "[%s]Your Domain-Bound Certificate has been verified"  % (settings.ORGANIZATION_NAME)
                msg = EmailMessage(subject,msg,
                               settings.EMAIL_HOST_USER,
                               [self.trust_anchor.owner.email, self.contact_email])            
                msg.content_subtype = "html"  # Main content is now text/html
                msg.send()
            
            
            #send the verification email.
            self.verified_message_sent = True
            super(DomainBoundCertificate, self).save(**kwargs)
            return
        
        if self.revoke and self.status != "revoked":
            self.revoke = True
            self.status = "revoked"
            
             # Get the response
            rcsp_result = write_verification_message(self.serial_number,
                                                 self.common_name,
                                                "revoked",
                                                self.sha1_fingerprint,
                                                )
            #Write it to db
            self.rcsp_response = rcsp_result
            fn = "%s.json" % (self.serial_number)
            #Write it to file
            fp = os.path.join(settings.CA_INPROCESS_DIR, fn)
            
            f = open(fp, "w")
            f.write(str(rcsp_result))
            f.close()
            
            #Upload the RCSP file to S3
            s=SimpleS3()
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                url = s.store_in_s3(fn, fp, bucket=settings.RCSP_BUCKET,
                                public=True)
            if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:
                dest = os.path.join(settings.LOCAL_X5C_PATH, self.trust_anchor.owner.username, self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                
                dest_file = os.path.join(dest, fn)
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_status_url = "%s%s/%s/%s" % (settings.X5C_URL_PREFIX, self.trust_anchor.owner.username, self.dns, fn)
                
                
                 
            #Calculate the SHA1 fingerprint & write it to a file
            digestsha1 = json.dumps(sha.sha1_from_filepath(fp), indent = 4)
            fn = "%s-sha1.json" % (self.serial_number)
            fp = os.path.join(settings.CA_INPROCESS_DIR, fn)
            f = open(fp, "w")
            f.write(str(digestsha1)) 
            f.close()
                
            #Upload the RCSP SHA! Digest to S3
            if "S3" in settings.CA_PUBLICATION_OPTIONS:
                url = s.store_in_s3(fn, fp, bucket=settings.RCSPSHA1_BUCKET,
                                public=True)
                
            if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:
                dest = os.path.join(settings.LOCAL_RCSPSHA1_PATH, self.trust_anchor.owner.username, self.dns)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                
                dest_file = os.path.join(dest, fn)
                os.umask(0000)
                copyfile(fp, dest_file)
                os.chdir(settings.BASE_DIR)
                self.public_cert_status_sha1_url = "%s%s/%s/%s" % (settings.RCSPSHA1_URL_PREFIX, self.trust_anchor.owner.username, self.dns, fn)
            
                
                #Delete all the old files:
                #PEM, DIR, ZIP
                if "S3" in settings.CA_PUBLICATION_OPTIONS:
                    if self.presigned_zip_s3:
                        s3info = json.loads(self.presigned_zip_s3) 
                        self.presigned_zip_url = s.delete_in_s3(s3info['bucket'],
                                                            s3info['key'],)
                    if self.public_cert_der_s3:
                        s3info = json.loads(self.public_cert_der_s3) 
                        self.public_cert_der_url = s.delete_in_s3(s3info['bucket'],
                                                              s3info['key'],)
                    
                    
                    if self.public_cert_pem_s3:
                        s3info = json.loads(self.public_cert_pem_s3) 
                        self.public_cert_pem_url = s.delete_in_s3(s3info['bucket'],
                                                              s3info['key'],)
                
                if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:
                    print "TODO - Delete local files after revocation"
            # Now perform the revocation on our index and delete old files.
            revoke_from_anchor(self)
            revoke(self)
        
         
        super(DomainBoundCertificate, self).save(**kwargs)

    def delete(self, **kwargs):
        self.revoke = True
        self.status = "revoked"
         # Get the response
        rcsp_result = write_verification_message(self.serial_number,
                                                 self.common_name,
                                                "revoked",
                                                self.sha1_fingerprint,
                                                )
        #Write it to db
        self.rcsp_response = rcsp_result
        fn = "%s.json" % (self.serial_number)
        #Write it to file
        fp = os.path.join(settings.CA_INPROCESS_DIR, fn)
        
        f = open(fp, "w")
        f.write(str(rcsp_result))
        f.close()
        
        #Upload the RCSP file to S3
        s=SimpleS3()
        if "S3" in settings.CA_PUBLICATION_OPTIONS:
            url = s.store_in_s3(fn, fp, bucket=settings.RCSP_BUCKET,
                            public=True)

            
        #Calculate the SHA1 fingerprint & write it to a file
        digestsha1 = json.dumps(sha.sha1_from_filepath(fp), indent =4)
        fn = "%s-sha1.json" % (self.serial_number)
        fp = os.path.join(settings.CA_INPROCESS_DIR, fn)
        f = open(fp, "w")
        f.write(str(digestsha1)) 
        f.close()
            
        #Upload the RCSP SHA! Digest to S3
        if "S3" in settings.CA_PUBLICATION_OPTIONS:
            url = s.store_in_s3(fn, fp, bucket=settings.RCSPSHA1_BUCKET,
                            public=True)
        revoke_from_anchor(self)
        revoke(self)
        
        super(DomainBoundCertificate, self).save(**kwargs)


class CertificateRevocationList(models.Model):
    
    url                 = models.CharField(max_length=512, default="", blank=True)
    creation_datetime   = models.DateTimeField(auto_now_add=True)
    creation_date       = models.DateField(auto_now_add=True)
    
    
    def __unicode__(self):
        return '%s Created @ %s.' % (self.id,
                                                    self.creation_datetime)
    
    class Meta:
        get_latest_by = "creation_date"
        ordering = ('-creation_date',)
        
    def save(self, **kwargs):
        self.url = build_crl()
    
        super(CertificateRevocationList, self).save(**kwargs)
        
class AnchorCertificateRevocationList(models.Model):
    trust_anchor        = models.ForeignKey(TrustAnchorCertificate)
    url                 = models.CharField(max_length=512, default="", blank=True)
    creation_datetime   = models.DateTimeField(auto_now_add=True)
    creation_date       = models.DateField(auto_now_add=True)
    
    
    def __unicode__(self):
        return 'CRL %s created @ %s.' % (self.id, self.creation_datetime)
    
    class Meta:
        get_latest_by = "creation_date"
        ordering = ('-creation_date',)
        
    def save(self, **kwargs):
        
        self.url = build_anchor_crl(self.trust_anchor)
    
        super(AnchorCertificateRevocationList, self).save(**kwargs)
    