from settings import *

# Email Settings -----------------------------------------------------------




# Email Settings -----------------------------------------------------------

#Send out emails or not.
SEND_CA_EMAIL = False
# For AWS SES uncomment / set.
# EMAIL_BACKEND = 'django_ses.SESBackend'
# AWS credentials if using AWS SES
# AWS_ACCESS_KEY_ID = '[your AWS_ACCESS_KEY_ID here]'
# AWS_SECRET_ACCESS_KEY = '[your AWS_SECRET_ACCESS_KEY here]'

#Emails will come from this user
EMAIL_HOST_USER = 'vcert@example.com'

# he links in emails sent will use HOSTNAME_URL for referring to the server.
# Used in password resets and such.
#For development
HOSTNAME_URL = 'http://127.0.0.1:8000'
#For production
#HOSTNAME_URL = 'https://console.example.com'

#CA Settings ----------------------------------------------------
ORGANIZATION_NAME = "Example, Inc."
LOCATION_NAME = "Washington, DC"
REQUEST_ACCOUNT_URL = "http://example.com/request-account"
ORGANIZATION_NAME = "Sample-CA"
CA_COMMON_NAME = "ca.example.com"
LOCATION_NAME = "Anywhere, USA"
GLOBAL_TITLE = "caconsole.example.com"
CA_VERIFIER_EMAIL = "verifier@example.com"
CA_HOSTNAME = "localhost:8000/static"
CA_URL = 'http://%s/' % (CA_HOSTNAME)


# Recommend leaving these settings as-is
CA_CONF_DIR     = os.path.join( CA_BASE_DIR, 'conf/' )
CA_PRIVATE_DIR  = os.path.join( CA_BASE_DIR, 'private/' )
CA_PUBLIC_DIR   = os.path.join( CA_BASE_DIR, 'public/' )
CA_SIGNED_DIR   = os.path.join( CA_BASE_DIR, 'signed-keys/' )
CA_COMPLETED_DIR = os.path.join( CA_BASE_DIR, 'completed/' )
CA_INPROCESS_DIR = os.path.join( CA_BASE_DIR, 'inprocess/' )
CA_CRL_DIR = os.path.join( CA_BASE_DIR, 'crl/' )
# This file is the main settings 
CA_MAIN_CONF    = os.path.join( CA_CONF_DIR , "root.cnf")
#The password on the Root CA's private certificate.
PRIVATE_PASSWORD    = "changem3"
# change to point to the CA's public certificate
CA_PUBLIC_CERT   = os.path.join( CA_BASE_DIR, 'public/', "ca.example.com.pem" )

#The password on the Root CA's private certificate. This is set in install step 3.

# Make this unique, and don't share it with anybody.
# you should not use this one but create another 50 character random string.
# Assuming Django Extensions are installed you can accomplish this by
# python manage.py generate_secret_key
SECRET_KEY = 'd-smw%fitci+m72a48g0&1z9_%q+)gpjg2r%79e(=f26nbndww'