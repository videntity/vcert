from settings import *



# Make this unique, and don't share it with anybody.
# you should not use this one but create another 50 character random string.
# Assuming Django Extensions are installed you can accomplish this by
# python manage.py generate_secret_key

SECRET_KEY = 'c-smw%fitci+m72a48g0&1z9_%q+)gpjg2r%79e(=f26nbndww'

# Email Settings -----------------------------------------------------------

#Use AWS SES
EMAIL_BACKEND = 'django_ses.SESBackend'

#AWS credentials
AWS_ACCESS_KEY_ID = '[your AWS_ACCESS_KEY_ID here]'
AWS_SECRET_ACCESS_KEY = '[your AWS_SECRET_ACCESS_KEY here]'

#emails will come from this user
EMAIL_HOST_USER = 'vcert@example.com'

#T he links in emails sent will use HOSTNAME_URL for referring to the server.
# Used in password resets and such.
#For development
HOSTNAME_URL = 'http://127.0.0.1:8000'

#For production
#HOSTNAME_URL = 'https://console.example.com'



# Twilio is not yet supported, but these are added for future multi-factor
# authentication support requiring a mobile phone for login.

# Twilio SMS Settings -----------------------------------------------
TWILIO_DEFAULT_FROM = "+15555555555"
TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"
TWILIO_SID = ""
TWILIO_AUTH_TOKEN = ""
TWILIO_API_VERSION = '2010-04-01'
SMS_LOGIN_TIMEOUT_MIN = 10


#Org details
ORGANIZATION_NAME = "Your Org"
LOCATION_NAME = "City, ST"

#CA Settings -----------------------------------------------------
# Reccomend leaving these settings as-is
ORGANIZATION_NAME = "Example, Inc."
LOCATION_NAME = "Washington, DC"

CA_CONF_DIR     = os.path.join( CA_BASE_DIR, 'conf/' )
CA_PRIVATE_DIR  = os.path.join( CA_BASE_DIR, 'private/' )
CA_PUBLIC_DIR   = os.path.join( CA_BASE_DIR, 'public/' )
CA_SIGNED_DIR   = os.path.join( CA_BASE_DIR, 'signed-keys/' )
CA_COMPLETED_DIR = os.path.join( CA_BASE_DIR, 'completed/' )
CA_INPROCESS_DIR = os.path.join( CA_BASE_DIR, 'inprocess/' )
CA_CRL_DIR = os.path.join( CA_BASE_DIR, 'crl/' )

# change to point to the CA's public certificate
CA_PUBLIC_CERT   = os.path.join( CA_BASE_DIR, 'public/', "ca.example.com.pem" )
# This file is the main settings 
CA_MAIN_CONF    = os.path.join( CA_CONF_DIR , "ca.directca.org.cnf")
#The password on the Root CA's private certificate. This is set in install step 3.
PRIVATE_PASSWORD    = "ChangeMe!"


CA_VERIFIER_EMAIL = "verifier@example.com"

#Depricated - Used to make a single CRL for all nodes.
CRL_FILENAME = "example-crl.pem"


#Publish items to S3.  If false the behavior is disabled. 
USE_S3              = True

# Send outbound emails such as #verification notification and more
SEND_CA_EMAIL       = True

# The S3 bucket for the certificate revocation lists.  This "webserver" is
# used by all trust anchors.
CRL_BUCKET          = "ca.example.com"            #Public

#A bucket for the X5C certificate chain
X5C_BUCKET          = "pubcerts.example.com"     #Public

#A bucket for public certs in pem, dir and x12 formats.
PUBCERT_BUCKET      = "pubcerts.example.com"     #Public



# A bucket to contain a JSON representation of the certificate revocation status
RCSP_BUCKET         = "rcsp.example.com"         #Public
# A bucket for a SHA-1 signature of RSCPRCSP_BUCKET 
RCSPSHA1_BUCKET     = "rcspsha1.example.com"     #Public

# A Note on RCSP - RCSP stands for REST Certificate Status Protocol.  Its
# a protocol I've invented as a modernsomething I've created as
# a modern replacement for Online Certificate Status Protocol (OCSP).
# vert serve as a reference implmentation implementation for RCSP.
# See this blog article for more info.


# A bucket for private certificates
PRIVCERT_BUCKET     = "privcerts.example.com"    #Private

#The password on the Root CA's private certificate.
PRIVATE_PASSWORD    = "99red6yrger2e2rjkgnduiotyutdmfgnR44867WEV#&(dfkgballoons"




