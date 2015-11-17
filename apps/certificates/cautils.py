#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf import settings
from collections import OrderedDict
import os, sys, uuid, json, re
from shutil import copyfile, copytree, rmtree
from subprocess import call
import pdb
from sha import sha256_from_filepath
from cStringIO import StringIO
import subprocess
from datetime import datetime
from fileutils import SimpleS3



def sedswap(swap_this, for_that, config_file_path):
 
    sed_str = """s#%s#%s#g""" % (swap_this, for_that)
    error, output = subprocess.Popen(["sed", "-i", "-e", sed_str, config_file_path],
                                stdout=subprocess.PIPE,
                                stderr= subprocess.PIPE
                                ).communicate()
   
    #print swap_this, for_that #, config_file_path
    return error, output

def sedswap2(swap_this, for_that, config_file_path):
    #the has signs dont work with AIA or CRL so this is needed.
    sed_str = """s/%s/%s/g""" % (swap_this, for_that)
    error, output = subprocess.Popen(["sed", "-i", "-e", sed_str, config_file_path],
                                stdout=subprocess.PIPE,
                                stderr= subprocess.PIPE
                                ).communicate()
   
    #print swap_this, for_that #, config_file_path
    return error, output
 

def write_verification_message(serial_number, common_name, status,
                               cert_sha1_fingerprint,
                               note = ""):

    d = OrderedDict()
    d['SerialNumber']        = serial_number
    d['CommonName']          = common_name
    d['CertStatus']          = status
    d['CertSHA1Fingerprint'] = cert_sha1_fingerprint 
    d['ThisUpdate']          = str(datetime.now())
    
    if note:
        d['Note']            = note
    
    return json.dumps(d, indent =4)


def extract(raw_string, start_marker, end_marker):
    start = raw_string.index(start_marker) + len(start_marker)
    end = raw_string.index(end_marker, start)
    return raw_string[start:end]

def chain_keys_in_list(outpath, filenames):
    certslist_str = ""
    with open(outpath, 'w') as outfile:
        for fname in filenames:
            with open(fname) as infile:
                outfile.write(infile.read())

    f = open(outpath, 'r')
    certslist_str = f.read()
    f.close()

    list_of_certs = re.findall('-----BEGIN CERTIFICATE-----$\n(.*?)\n^-----END CERTIFICATE-----',
               certslist_str, re.DOTALL|re.MULTILINE)
    
    #print "LIST O CERTS", list_of_certs
    newcerts =[]
    for c in list_of_certs:
        nc = c.replace('\n','')
        newcerts.append(nc)
    return newcerts

def write_x5c_message(name, x5ckeys):
    jose_x509 = {"keys":[
                {"kty":"PKIX",
                "x5c": x5ckeys,
                    "use":"sig",
                    "kid":name }]
                }
    return json.dumps(jose_x509, indent =4)


def build_crl():
    url = ""
    password = "pass:" + settings.PRIVATE_PASSWORD
    crl_file = settings.LOCAL_ROOT_CRL_PATH
    print "CRL_FILE", crl_file
    
    
    call(["openssl", "ca", "-config",  settings.CA_MAIN_CONF ,
          "-crlexts", "crl_ext", "-gencrl", "-out",
          crl_file, "-passin", password])
    
    call(["openssl", "crl", "-in", crl_file, '-out',crl_file, '-outform', 'DER' ])
    
    
    if "S3" in settings.CA_PUBLICATION_OPTIONS:
        s=SimpleS3()
        key = "crl/" + settings.CRL_FILENAME
        url = s.store_in_s3(key, crl_file,
                        bucket=settings.CRL_BUCKET, public=True)


    if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:
        os.umask(0000)
        #print "copy", crl_file, settings.LOCAL_CRL_PATH
        #copyfile(crl_file, os.path.join(settings.LOCAL_CRL_PATH, settings.CRL_FILENAME))
        os.chdir(settings.BASE_DIR)
        url = settings.CA_ROOT_CRL_URL

    if url:
        print "Completed upload @ %s. Archive URL = %s" % (datetime.now(), url)
    else:
        print "Upload failed @ %s"
        url= "Failed"
        
    return url, crl_file


def build_anchor_crl(trust_anchor):
    
    url = ""
    config_file = "%s-crl-stub.cnf" % (trust_anchor.dns)
    crl_file = "%s.crl" % (trust_anchor.dns)
    crl_path = os.path.join(trust_anchor.completed_dir_path, crl_file)
    crl_conf = os.path.join(trust_anchor.completed_dir_path, config_file)
    
    print crl_conf
    
    call(["openssl", "ca", "-config",  crl_conf,  "-gencrl",
          "-crlexts", "crl_ext","-out", crl_path,])
    
    call(["openssl", "crl", "-in", crl_path, '-out',crl_path, '-outform', 'DER' ])
    
    
    if "S3" in settings.CA_PUBLICATION_OPTIONS:
        s=SimpleS3()
        key = "crl/" + crl_file
        url = s.store_in_s3(key, crl_path,
                        bucket=settings.CRL_BUCKET,
                        public=True)
    
    if "LOCAL" in settings.CA_PUBLICATION_OPTIONS:
        os.umask(0000)
        #print "copy", crl_path, settings.LOCAL_CRL_PATH
        copyfile(crl_path, os.path.join(settings.LOCAL_CRL_PATH, crl_file))
        os.chdir(settings.BASE_DIR)
        url = os.path.join(settings.CRL_URL_PREFIX, crl_file) 

    if url:
        print "Completed upload @ %s. Archive URL = %s" % (datetime.now(), url)
    else:
        print "Upload failed @ %s"
        url= "Failed"
        
    return url, crl_path


def revoke(cert):

    #TODO Find a more secure way to store password.
    password = "pass:" + settings.PRIVATE_PASSWORD 
    fn = cert.serial_number + ".pem"
    fn = os.path.join(settings.CA_SIGNED_DIR, fn)
    error, output = subprocess.Popen(["openssl", "ca",
                                      "-config", settings.CA_MAIN_CONF,
                                      "-revoke" , fn,
                                      "-passin", password ],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()
    if os.path.exists(cert.completed_dir_path):
        rmtree(cert.completed_dir_path)
        #print "DELETED the path", cert.completed_dir_path
    return output

def revoke_from_anchor(cert):
    print "revoke_from_anchor"
    fn = cert.serial_number + ".pem"
    fn = os.path.join(settings.CA_SIGNED_DIR, fn)
    if hasattr(cert, 'trust_anchor'):
        config_file = "%s/%s-crl-stub.cnf" % (cert.trust_anchor.completed_dir_path,
                                          cert.trust_anchor.dns)
    elif hasattr(cert,'parent'):
        if cert.parent:
            config_file = "%s/%s-crl-stub.cnf" % (cert.parent.completed_dir_path,
                                          cert.parent.dns)
        else:
            revoke(cert)

    error, output = subprocess.Popen(["openssl", "ca", "-config", config_file,
                                      "-revoke" , fn],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()
    
    print "revoke -------------------------------"
    print error, output
    if os.path.exists(cert.completed_dir_path):
        rmtree(cert.completed_dir_path)
        # print "DELETED the path", cert.completed_dir_path
    return output



def create_trust_anchor_certificate(common_name     = "example.com",
                                    email           = "example.com",
                                    dns             = "example.com",
                                    expires         = 730,
                                    organization    = "ACME",
                                    city            = "Gaithersburg",
                                    state           = "MD",
                                    country         = "US",
                                    rsakey          = 2048,
                                    user            = "alan",
                                    aia_url         = settings.CA_ROOT_AIA_URL,
                                    include_aia     = True,
                                    include_crl     = True,
                                    parent          = None ):
    
    #a  dict for all the things we want to return
    result = {  "sha256_digest":                      "",
                "anchor_zip_download_file_name":      "",
                "status":                             "failed",
                "serial_number":                      "-01",
                "sha1_fingerprint":                   "",
                "private_key_path":                   "",
                "public_key_path":                    "",
                "notes":                              "Certificate generation in process.",
                "completed_dir_path":                 "",
                "aia_url":                            "",
                "crl_url":                            "",
                "chain_url":                           "",
                "x5c_url":                            "",
                "details":                            "",
                }
    
    dirname = str(uuid.uuid4())[0:5]
    this_dir = os.path.join(settings.CA_INPROCESS_ANCHOR_DIR, dirname)
    
    tname =  dns
    os.chdir(settings.CA_INPROCESS_ANCHOR_DIR)
    os.umask(0000)
    os.mkdir(dirname)
    os.chdir(this_dir)
    
    
    if not parent:
        #"Root Trust Anchor"
        conf_stub_file_name             = tname  + "trust-anchor-stub.cnf"
        #conf_intermediate_stub_file_name  = tname  + "intermediate-anchor-stub.cnf"
        completed_user_dir              = os.path.join(settings.CA_COMPLETED_DIR, user )
        completed_user_anchor_dir       = os.path.join(completed_user_dir, "anchors")
        completed_this_anchor_dir       = os.path.join(completed_user_anchor_dir, dns)
        completed_user_dom_bound_dir    = os.path.join(completed_this_anchor_dir, "endoints")
        completed_user_intermediate_dir = os.path.join(completed_this_anchor_dir, "intermediates")
        crl_url                         = settings.CA_ROOT_CRL_URL
        aia_url                         = settings.CA_ROOT_AIA_URL

        # Copy a stub configs to our working directory----------------------------------
        copyfile(os.path.join(settings.CA_CONF_DIR, "trust-anchor-stub.cnf"),
                               conf_stub_file_name)
        this_conf = os.path.join(this_dir, conf_stub_file_name) 

    else:
        #print "Intermediate Anchor"
        conf_stub_file_name             = tname  + "intermediate-stub.cnf"
        completed_user_dir              = os.path.join(parent.completed_dir_path)
        completed_user_anchor_dir       = os.path.join(completed_user_dir, "anchors")
        completed_user_intermediate_dir = os.path.join(parent.completed_dir_path, "intermediates")
        
        completed_user_dom_bound_dir    = os.path.join(completed_user_dir, "endoints")
        completed_this_anchor_dir       = os.path.join(completed_user_anchor_dir, dns)
        # Copy a stub config file to our directory----------------------------------
        copyfile(os.path.join(settings.CA_CONF_DIR, "intermediate-anchor-stub.cnf"),
                 conf_stub_file_name)
        this_conf = os.path.join(this_dir, conf_stub_file_name)
        crl_url                         = settings.CRL_URL_PREFIX + parent.common_name + ".crl"
        aia_url                         = settings.AIA_URL_PREFIX +  parent.common_name + ".der"
    
    chain_url                       = settings.CHAIN_URL_PREFIX  + common_name + "-chain.pem"
    x5c_url                         = settings.X5C_URL_PREFIX +  common_name + "-x5c.json"
        
        
        
    #print "COMPLETED PATH IS: ",  completed_this_anchor_dir

    keysize = "rsa:" + str(rsakey)
    csrname = tname + ".csr"
    privkeyname = tname + "Key.key"         # Private key in pem format
    PCKS8privkeyname  = tname + "Key.der"   # PCKS8 DER formatted private key file
    p12name = tname + ".p12"                # p12 formatted private and public keys
    public_cert_name =  tname + ".pem"      #pubic certificate as a PEM
    public_cert_name_der =  tname + ".der"  # pubic certificate as a der
    anchor_zip_download_file_name = tname + "-ANCHOR.zip"
    crl_conf_stub_file_name = tname  + "crl.cnf"
    private_key_path_pem = os.path.join(completed_this_anchor_dir, privkeyname)
    public_key_path_pem = os.path.join(completed_this_anchor_dir, public_cert_name)

    subj = '/emailAddress=' + email + \
           '/C='            + country +  \
           '/ST='           + state + \
           '/L='            + city + \
           '/CN='           + common_name + \
           '/O='            + organization
    

    
    #Create the signing request. ----------------------------------------------
    error, output  = subprocess.Popen(["openssl", "req", "-subj", subj , "-out", csrname,
                             "-new", "-newkey", keysize, "-nodes", "-keyout",
                             privkeyname],
                            stdout = subprocess.PIPE,
                            stderr= subprocess.PIPE,
                            ).communicate()
    print "Signing request", output
    
    #Prepare for the signing ----------------------------------
    
    
    #get the next serial number --------------------------------
    fp = open(settings.CA_MAIN_SERIAL, "r")
    serial = str(fp.read())
    fp.close()
    
    
   
    # Prepare strings for sed, that will be used to fillout our stub into a usable config file.
    
    error, output = sedswap("|DNS|", dns, this_conf)
    error, output = sedswap("|DAYS|", expires, this_conf)
    error, output = sedswap("|SERIAL|", serial[:-1], this_conf)
    error, output = sedswap("|COUNTRY|", country, this_conf)
    error, output = sedswap("|STATE|", state ,this_conf)
    error, output = sedswap("|CITY|", city , this_conf)
    error, output = sedswap("|COMMON_NAME|", common_name, this_conf)
    error, output = sedswap("|ORGANIZATION|", organization ,this_conf)
    error, output = sedswap("|EMAIL_ADDRESS|", email, this_conf)
    error, output = sedswap("|CRL_URL|", crl_url, this_conf)

    if not parent:
        error, output = sedswap("|ANCHORDNS|", settings.CA_COMMON_NAME,  this_conf)
    else:
        error, output = sedswap("|CERTIFICATE|", parent.public_key_path, this_conf)
        error, output = sedswap("|COMPLETED_ANCHOR_DIR|", parent.completed_dir_path, this_conf)
        error, output = sedswap("|ANCHORDNS|", parent.common_name,  conf_stub_file_name)
        error, output = sedswap("|PRIVATE_KEY|", parent.private_key_path,  this_conf)
    
    
    if include_crl:
        error, output = sedswap("|CRL_URL|", crl_url, this_conf)
    else:
        error, output = sedswap2("crlDistributionPoints", "#crlDistributionPoints",  this_conf)
        
    if include_aia:
 
        if not parent: 
            #Points to a DER.
            aia_url = settings.CA_URL + "aia/" + settings.CA_COMMON_NAME + ".der"
        else:
            aia_url = aia_url
            
        
        error, output = sedswap("|AIA_URL|", aia_url,  this_conf)
        
    else:
        error, output = sedswap2("authorityInfoAccess", "#authorityInfoAccess",  this_conf)
  
    
    # Build the certificate from the signing request.
    if not parent:
        password = "pass:" + settings.PRIVATE_PASSWORD #TODO Find a more secure way to do this
        
        error, signoutput = subprocess.Popen(["openssl", "ca", "-batch", "-config",
                             this_conf, "-in", csrname, "-out",
                             public_cert_name, "-passin", password],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()
    else:
        #print "build cert"
        error, signoutput = subprocess.Popen(["openssl", "ca", "-batch", "-config",
                             this_conf, "-in", csrname, "-out",
                             public_cert_name],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()
    
    print "CERT SIGN OUT", signoutput
    

    
    #if the previous step fails, then 
    if str(signoutput.lower()).__contains__("failed to update database") or \
       str(signoutput.lower()).__contains__("error"):
        print "PUBLIC CERT NAME:", public_cert_name, "FAILED!!!!"
        result["status"]                            = "failed"
        result["notes"] = signoutput
        os.chdir(settings.BASE_DIR) 
        return result
    
    
    output = subprocess.Popen(["openssl", "x509", "-in", public_cert_name,
                                      "-text", "-noout"],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()
    result['details'] = output[0]
        
    #The certificate was created so let's start plucking info out.
    #get the serial number
    #print "get the serial from the cert"
    output,error = subprocess.Popen(["openssl", "x509", "-in",
                                      public_cert_name, "-serial","-noout",],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()
    
    try:
        serialsplit = output.split("=")
        serial_number = str(serialsplit[1])[:-1]
    except(IndexError):
        result["status"] = "failed"
        result["notes"] = output
        os.chdir(settings.BASE_DIR) 
        return result
        
    
    #print "SERIAL:",  serial_number
    #get the sha1 fingerprint
    output,error = subprocess.Popen(["openssl", "x509", "-in",
                                      public_cert_name, "-fingerprint","-noout",],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()
    
    fpsplit = output.split("=")
    sha1_fingerprint = str(fpsplit[1])[:-1]
    #print "SHA1 Fingerprint:",  sha1_fingerprint 
    # Convert the public pem into a der
    error, output = subprocess.Popen(["openssl", "x509", "-outform", "der", "-in",
                                      public_cert_name, "-out",
                                      public_cert_name_der],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()

    
    error, output = subprocess.Popen(["openssl", "x509", "-outform", "der",
                                      "-in", public_cert_name, "-out",
                                      public_cert_name_der],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()
    

    # Convert the private key in pem format to a PCKS8 DER formatted private key file
    error, output = subprocess.Popen(["openssl", "pkcs8", "-topk8", "-out",
                                      PCKS8privkeyname,  "-in", privkeyname,
                                      "-inform", "pem", "-outform", "der",
                                      "-nocrypt",],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()
    
    
    #create the sha1 digest of the DER.
    sha256_digest = sha256_from_filepath(public_cert_name_der)
  
    #Create an empty index file
    if not os.path.exists('index'):
        open('index', 'w').close()
       

    #Since the anchor creation process completed, then build out the perm dirs
    if not os.path.exists(completed_user_dir):
        os.makedirs(completed_user_dir)
    
    if not os.path.exists(completed_user_anchor_dir):
        os.makedirs(completed_user_anchor_dir)
     
    if not os.path.exists(completed_user_intermediate_dir):
        os.makedirs(completed_user_intermediate_dir) 
        
        
    completed_this_anchor_dir = os.path.join(completed_user_anchor_dir, dns)

    if os.path.exists(completed_this_anchor_dir):
        rmtree(completed_this_anchor_dir)
    copytree(".", completed_this_anchor_dir)
        
    os.chdir(completed_this_anchor_dir)
    error, output = subprocess.Popen(["zip", anchor_zip_download_file_name,
                                      public_cert_name, public_cert_name_der],
                                    stdout=subprocess.PIPE,
                                    stderr= subprocess.PIPE
                                    ).communicate()

    
    #build result dict
    result.update({"sha256_digest": sha256_digest,
                   "anchor_zip_download_file_name": anchor_zip_download_file_name,
                   "notes": "",
                   "serial_number" : serial_number,
                   "status": "unverified",
                   "sha1_fingerprint": sha1_fingerprint,
                   "private_key_path": private_key_path_pem,
                   "public_key_path": public_key_path_pem,
                   "completed_dir_path": completed_this_anchor_dir,
                   "aia_url":  aia_url,
                   "crl_url": crl_url,
                   "chain_url":  chain_url,
                   "x5c_url": x5c_url
                   })
    
    # Get back to the directory we started.
    os.chdir(settings.BASE_DIR) 

    return result
    

    


def create_endpoint_certificate(    anchor,
                                    common_name     = "foo.example.com",
                                    email           = "foo.example.com",
                                    dns             = "foo.example.com",
                                    anchor_dns      = "example.com",
                                    expires         = 730,
                                    organization    = "NIST",
                                    city            = "Gaithersburg",
                                    state           = "MD",
                                    country         = "US",
                                    rsakey          = 2048,
                                    aia_der         = "",
                                    user            = "",
                                    private_key_path = "",
                                    public_key_path  = "",
                                    completed_anchor_dir = "",
                                    include_aia = True,
                                    include_crl =True):
    
    result = {  "sha256_digest":                      "",
                "anchor_zip_download_file_name":      "",
                "status":                             "failed",
                "serial_number":                      "-01",
                "sha1_fingerprint":                   "",
                "private_key_path":                   "",
                "public_key_path":                    "",
                "notes":                              "Certificate generation in process.",
                "completed_dir_path":                 "",
                "details":                            "",
                "aia_url":                            "",
                "crl_url":                            "",
                "chain_url":                          "",
                "x5c_url":                            "",
                }
    
    dirname = str(uuid.uuid4())[0:5]
    tname =  dns
    keysize = "rsa:" + str(rsakey)
    csrname = tname + ".csr"
    privkeyname = tname + "Key.key"         # Private key in pem format
    PCKS8privkeyname  = tname + "Key.der"   # PCKS8 DER formatted private key file
    p12name = tname + ".p12"                # p12 formatted private and public keys
    public_cert_name =  tname + ".pem"      #pubic certificate as a PEM
    public_cert_name_der =  tname + ".der"  # pubic certificate as a der
    conf_stub_file_name = tname  + "endpoint-stub.cnf"
    anchor_zip_download_file_name = str(uuid.uuid4()) + "-" + tname + "-ENDPOINT.zip"
    
    completed_user_dir             = os.path.join(anchor.completed_dir_path )
    completed_endpoint_dir          = os.path.join(anchor.completed_dir_path, "endpoints/")
    completed_this_endpoint         = os.path.join(completed_endpoint_dir, dns)
    result['crl_url']               = settings.CRL_URL_PREFIX + anchor.common_name + ".crl"
    result['aia_url']               = settings.AIA_URL_PREFIX + anchor.common_name + ".der"
    result['x5c_url']               = settings.X5C_URL_PREFIX + common_name + ".json"
    result['chain_url']             = settings.CHAIN_URL_PREFIX + common_name + ".pem"
    

    subj = '/emailAddress=' + email + \
           '/C='            + country +  \
           '/ST='           + state + \
           '/L='            + city + \
           '/CN='           + common_name + \
           '/O='            + organization 
    
    dirpath = os.path.join(settings.CA_INPROCESS_DIR, "endpoints", dirname)
    os.umask(0000)
    os.mkdir(dirpath)
    os.chdir(dirpath)
     
    #print "Temp DIRECTORY is:",  dirpath
    #print "Temp DIRECTORY is:",  completed_this_domain_bound_dir
    
    #Determine if this is address or domain bound
    email_bound=False
    if email.__contains__("@"):
        email_bound=True
    
    # Create the signing request.
    call(["openssl", "req", "-subj", subj , "-out", csrname, "-new", "-newkey",
          keysize, "-nodes", "-keyout", privkeyname]) 
    
    # Copy a stub config file to our directory
    if email.__contains__("@"):
        copyfile(os.path.join(settings.CA_CONF_DIR,"email-bound-stub.cnf"),
                    conf_stub_file_name)
    else:
        copyfile(os.path.join(settings.CA_CONF_DIR,"domain-bound-stub.cnf"),
                    conf_stub_file_name)
    
    this_conf= os.path.join(conf_stub_file_name)
    
    #get the next serial number
    fp = open(settings.CA_MAIN_SERIAL, "r")
    serial = str(fp.read())
    fp.close()
    
    # Modify the stub file
    
    error, output = sedswap("|DNS|", dns, this_conf)
    error, output = sedswap("|ANCHORDNS|", anchor_dns, this_conf)
    error, output = sedswap("|COMPLETED_ANCHOR_DIR|", completed_anchor_dir, this_conf)
    error, output = sedswap("|DAYS|", expires, this_conf)
    error, output = sedswap("|CERTIFICATE|", public_key_path, this_conf)
    error, output = sedswap("|PRIVATE_KEY|", private_key_path , this_conf)
    error, output = sedswap("|SERIAL|", serial[:-1], this_conf)
    error, output = sedswap("|COUNTRY|", country, this_conf)
    error, output = sedswap("|STATE|", state , this_conf)
    error, output = sedswap("|CITY|", city, this_conf)
    error, output = sedswap("|COMMON_NAME|",common_name, this_conf)
    error, output = sedswap("|ORGANIZATION|", organization, this_conf)
    error, output = sedswap("|EMAIL_ADDRESS|", email , this_conf)
    
    if include_crl:    
        error, output = sedswap("|CRL_URL|", result['crl_url'], this_conf)
    else:
        error, output = sedswap2("crlDistributionPoints", "#crlDistributionPoints", this_conf)
    
    if include_aia:
        error, output = sedswap("|AIA_URL|", aia_der , this_conf)
    else:
        error, output = sedswap2("authorityInfoAccess", "#authorityInfoAccess" , this_conf)
    
    # Build the certificate from the signing request.
    
    error, signoutput = subprocess.Popen(["openssl", "ca", "-batch", "-config",
                             conf_stub_file_name, "-in", csrname, "-out",
                             public_cert_name],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()
  
    print "Signing ----------------",  signoutput
    
    output = subprocess.Popen(["openssl", "x509", "-in", public_cert_name,
                                      "-text", "-noout"],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()
    result['details'] = output[0]
    
    
    #if the previous step fails, then 
    if str(signoutput.lower()).__contains__("failed to update database") or \
       str(signoutput.lower()).__contains__("unable to load ca private key") or \
       str(signoutput.lower()).__contains__("error"):
        print "PUBLIC CERT NAME:", public_cert_name, "FAILED!!!!"

        result["status"] = "failed"
        result["notes"]  = signoutput
        os.chdir(settings.BASE_DIR) 
        return result
        
    
    #get the serial number
    output,error = subprocess.Popen(["openssl", "x509", "-in",
                                      public_cert_name, "-serial","-noout",],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()

    try:
        serialsplit = output.split("=")
        serial_number = str(serialsplit[1])[:-1]
    except (IndexError):
        result["status"] = "failed"
        result["notes"]  = signoutput
        os.chdir(settings.BASE_DIR) 
        return result
    

    #get the sha1 fingerprint
    output,error = subprocess.Popen(["openssl", "x509", "-in",
                                      public_cert_name, "-fingerprint","-noout",],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()
    

    fpsplit = output.split("=")
    sha1_fingerprint = str(fpsplit[1])[:-1]
    #print "SHA1 Fingerprint:",  sha1_fingerprint
    
    
    # Convert the public pem into a der
    output,error = subprocess.Popen(["openssl", "x509", "-outform", "der", "-in",
                                     public_cert_name, "-out",
                                     public_cert_name_der],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()
    

    #convert the private key in pem format to PCKS8 DER formatted private key file
    output,error = subprocess.Popen(["openssl", "pkcs8", "-topk8", "-out",
                                     PCKS8privkeyname,  "-in", privkeyname,
                                     "-inform", "pem", "-outform", "der",
                                     "-nocrypt",],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()

    # Create a p12 file from our der public key and out DER private key
    
    output,error = subprocess.Popen(["openssl", "pkcs12", "-export", "-inkey",
                                     privkeyname, "-in", public_cert_name,
                                     "-out", p12name, "-passout", "pass:"],
                             stdout=subprocess.PIPE,
                             stderr= subprocess.PIPE
                            ).communicate()
    #print output, error
    

    
    #create the sha1 digest of the DER.
    sha256_digest = sha256_from_filepath(public_cert_name_der)
  

    #Since the anchor creation process completed, then built out the perm dirs

    if not os.path.exists(completed_endpoint_dir):
        os.makedirs(completed_endpoint_dir)
    
    if os.path.exists(completed_this_endpoint):
        rmtree(completed_this_endpoint)
        
    copytree(".", completed_this_endpoint)
        
    os.chdir(completed_this_endpoint)
    
    crl_conf = os.path.join(completed_anchor_dir, "crl.cnf" )
    

    #if a crl.cnf does not exist, then create it.
    if not os.path.exists(crl_conf):
        copyfile(conf_stub_file_name, crl_conf)
        
    
    #create the zip file containing the private and public keys)
    error, output = subprocess.Popen(["zip", anchor_zip_download_file_name,
                                      public_cert_name, public_cert_name_der,
                                      privkeyname, PCKS8privkeyname, p12name
                                      ],
                                    stdout=subprocess.PIPE,
                                    stderr= subprocess.PIPE
                                    ).communicate()
    
    #Private Key Path for PEM
    private_key_path_pem = os.path.join(completed_this_endpoint, privkeyname)
    public_key_path_pem = os.path.join(completed_this_endpoint,  public_cert_name)

    
    #build result dict
    result.update({"sha256_digest":  sha256_digest,
                   "anchor_zip_download_file_name": anchor_zip_download_file_name,
                   "notes": "",
                   "serial_number" : serial_number,
                   "status": "unverified",
                   "sha1_fingerprint": sha1_fingerprint,
                   "private_key_path": private_key_path_pem,
                   "public_key_path": public_key_path_pem,
                   "completed_dir_path" :completed_this_endpoint
                   })
    
    # Get back to the directory we started.
    os.chdir(settings.BASE_DIR) 

    return result




def create_crl_conf(common_name     = "foo.example.com",
                    email           = "foo.bar.org",
                    dns             = "foo.bar.org",
                    anchor_dns      = "bar.org",
                    expires         = 1095,
                    organization    = "NIST",
                    city            = "Gaithersburg",
                    state           = "MD",
                    country         = "US",
                    rsakey          = 2048,
                    user            = "",
                    private_key_path = "",
                    public_key_path  = "",
                    completed_anchor_dir = ""):
    
    result = {"status": "failed"}
    
    dirname = str(uuid.uuid4())[0:5]
    tname =  dns
    keysize = "rsa:" + str(rsakey)
    completed_user_dir = os.path.join(settings.CA_COMPLETED_DIR, user )
    
    
    subj = '/emailAddress=' + email + \
           '/C='            + country +  \
           '/ST='           + state + \
           '/L='            + city + \
           '/CN='           + common_name + \
           '/O='            + organization 
    
    conf_stub_file_name = tname  + "-crl-stub.cnf"
    conf_stub_file_path = os.path.join(completed_anchor_dir, conf_stub_file_name)
    os.chdir(completed_anchor_dir)
     
    
    #copy over the stub
    copyfile(os.path.join(settings.CA_CONF_DIR,"crl-stub.cnf"),
             os.path.join(completed_anchor_dir, conf_stub_file_name))
    
    
    #get the next serial number
    ##p = open("/opt/ca/conf/serial", "r")
    #serial = str(fp.read())
    #fp.close()
    
    # Modify the stub file --------------------------------------------
    seddns = "s/|DNS|/%s/g" % (dns)
    sedanchordns = "s/|ANCHORDNS|/%s/g" % (anchor_dns)
    #prepare sed strings -----------------
    sedcompletedanchordir = "s#|COMPLETED_ANCHOR_DIR|#%s#g" % (completed_anchor_dir)
    seddays = "s/|DAYS|/%s/g" % (expires)
    sedpublickey = "s#|CERTIFICATE|#%s#g" % (public_key_path)
    sedprivatekey = "s#|PRIVATE_KEY|#%s#g" % (private_key_path)
    sedcountry = "s#|COUNTRY|#%s#g" % (country)
    sedstate= "s#|STATE|#%s#g" % (state)
    sedcity = "s#|CITY|#%s#g" % (city)
    sedcommon_name =  "s#|COMMON_NAME|#%s#g" % (common_name)
    sedorganization = "s#|ORGANIZATION|#%s#g" % (organization)
    sedemail = "s#|EMAIL_ADDRESS|#%s#g" % (email)


    #use sed to modify the file.
    error, output = subprocess.Popen(["sed", "-i", "-e", sedcompletedanchordir,
                                      conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()
    error, output = subprocess.Popen(["sed", "-i", "-e", seddns,
                                      conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()
    
    error, output = subprocess.Popen(["sed", "-i", "-e", sedanchordns,
                                      conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()

    
    error, output = subprocess.Popen(["sed", "-i", "-e",
                                      seddays, conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()
    
    error, output = subprocess.Popen(["sed", "-i", "-e",
                                      sedpublickey, conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()
    
    error, output = subprocess.Popen(["sed", "-i", "-e",
                                      sedprivatekey, conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()

     
    error, output = subprocess.Popen(["sed", "-i", "-e", sedcountry,
                                      conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()
    
    error, output = subprocess.Popen(["sed", "-i", "-e", sedstate,
                                      conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()

    error, output = subprocess.Popen(["sed", "-i", "-e", sedcity,
                                      conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()

    error, output = subprocess.Popen(["sed", "-i", "-e", sedcommon_name,
                                      conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()
    error, output = subprocess.Popen(["sed", "-i", "-e", sedorganization,
                                      conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()
    
    error, output = subprocess.Popen(["sed", "-i", "-e", sedemail,
                                      conf_stub_file_path],
                                        stdout=subprocess.PIPE,
                                        stderr= subprocess.PIPE
                                        ).communicate()

    
    
    # Get back to the directory we started.
    os.chdir(settings.BASE_DIR) 
    result = {"status": "success"}
    return result
