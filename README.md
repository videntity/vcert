README
======

`vcert`  A web-based certificate authority mangement system built atop OpenSSL.

Copyright Alan Viars 2013

Open Source License: MPL See LICENSE.txt

Last Updated: November 4, 2013

About
-----

`vcert` is a web-based (Django) Certificate Authority (or CA) that uses OpenSSL
under the hood.  The site DirectCA.org runs vcert. It was built specifically to
build x509 certificates compatible with the Direct Project.  It is written in
Python and Django and can run atop Apache2 or other webserver.

`vcert` can be used to manage a trust anchor (i.e. a registration authority or
HISP) or a root CA.

`vcert` supports revocation via certificate revocation lists (CRLs). A CRL is
created for each trust anchor and is published to a URL.

This software was designed to assist in testing for compliance with the Direct
Project's Applicability Statement. Perhaps you are not working in Health IT at
all and are just looking for a simple way to manage certificates.  You may well
be able to use this project for that purpose.

CODE CONTRIBUTIONS & PULL REQUEST WELCOME! 

    
Installation Part 1 - Download and Initial Setup
------------------------------------------------

`vcert` has a number of dependencies including OpenSSL, Python,
and Django. This software was tested with OpenSSL version 1.0.1, Python 2.7
and Django 1.5. SQLite is the default database and it was  tested
with SQLite version 3. The following instructions assume Ubuntu 13.04 is the
operating system, but it is possible to use others. (If anyone wants to
contribute Windows, Mac, or other operating system instructions please do so.)


Here is how to get started on Ubuntu 13.04. From the terminal, start by
installing OpenSSL. This is likely already installed, but installation
instructions are added here for clarity.

    sudo apt-get install openssl

Now install pip and make sure its up to date.

    sudo apt-get install python-pip
    sudo pip install --upgrade pip
    

Install git and then clone the master repository.

    sudo apt-get install git-core
    git clone https://github.com/videntity/vcert.git

    
Now change into the project's directory.

    cd vcert
    
Let's install the necessary python libraries including Django from the
project's requirements file.

    sudo pip install -r vcert/requirements.txt


Now that Django is installed lets setup our database.  Be sure and say yes when
asking to create an administrative account as this will be used in the CA's
administration.

   python manage.py syncdb

A directory for OpenSSL's CA must be created. We will do so by creating a
symbolic link between `/opt/ca` and `vcert/apps/certificates/ca` directories.

   sudo ln -s vcert/apps/certificates/ca /opt/
   
Now copy settings_local_example.py to settings_example.py.

    cp settings_local_example.py settings_example.py


You can at this point try out the server at this point with
`python manage.py runserver`, but your settings_local.py settings will need to
be customized before everything will work as expected. 


Installation Part 2 - Django Settings
-------------------------------------

The file `settings.py` contains default settings, where the file
`settings_local.py` add and overwrites what is in `settings.py` via Python
imports.


One of the main changes is replacing `examaple.com` with your own domain. You'll
also want to setup email settings for outgoing email notifications and setup web
locations for publishing certificates and CRLs.


Certificates and CRLs get published via Amazon Web Service's (AWS) Simple
Storage Service (S3) and email notifications are sent via Simple Email Service
(SES). The email setup is easily changed, but the certificate and CRL
publishing requires S3.  `vcert` assumes you create three S3 buckets with "vanity"
URLs. They are `ca` for CRLs and the CA's public certificate, `pubcerts` for public
certificates issued, and `privcerts` for private certificates. For illustration,
if you want to host your CA on the domain `example.com`, then you would create the
buckets `ca.example.com`, `privcerts.example.com` and `pubcerts.example.com`.
You need to map the DNS entries accordingly to create the "vanity" URL.  This is
accomplished within AWS management console for S3 and in your DNS provider's
website.


Please see the in-line comments inside `settings_local.py` for instructions
on what the various settings do.



Installlation Part 3 - OpenSSL CA Configuration
-----------------------------------------------

There are stil a few of items that need to be addressed:

Most notably you need to do the following:

Create and/or install the root CA's (or subordinate certificate's) private
certificate and change settings_local.py accordingly.  Here is how to generate a
new CA keypair with a password on the pricate key.  It assumes the domain
`ca.example.com` and uses the configuration file
`/opt/ca/conf/ca.example.com.cnf`. Before this next step,  you will likely want
to make adjustment there such the changing "example.com" to your domain, setting
organizational name, city, state, and so on.  Here are the step.



    cd /opt/ca
    openssl req -nodes -config conf/ca.example.com.cnf -days 7330 -x509 -newkey rsa:4096 -out public/ca.example.com.pem -outform PEM
    openssl rsa -des3 -in ./private/ca.example.comKey.pem -out ./private/ca.example.comKey.pem

You will end up with the CA's public key in '/opt/ca/public' and the private key
in '/opt/ca/private'.

You need to publish the CA's public certificate and CRL somehere.  `ca`
(e.g. `ca.example.com`) is a reasonable place. In the above example, we used
the configuration file `ca.example.com.cnf`.  You can use openssl command line
to create the CRL for your CA.



Installation Part 4  - Setting up Cron for CRL Updates
-------------------------------------------------------

In order to make the CRL updates automatic, we will use cron to execute a script
to perform the update. Edit your crontab like so.

    crontab -r
    
Now add the following line to your cron file.
    
    0 */2 * * * /home/ubuntu/django-apps/vcert/scripts/buildcrl.sh >> /home/ubuntu/crl.log

This assumes your `vcert` project is located at `/home/ubuntu/django-apps/vcert/`.
and the output of this operation is written to `/home/ubuntu/crl.log`. Adjust
these paths to fit your local environment.  With this setting we are updating
the CRLs every 30 minutes.  Note that each "Trust Anchor" has its own CRL.

    
    
Run the Application
-------------------

Now you can run the `vcert` in development mode:

    python manage.py runserver

    

Production Deployment
---------------------

The convention is to deploy `vcert` on server named `console` (e.g. `console.example.com`). 
Please refer to Django's documentation for more information on deploying Django
https://docs.djangoproject.com/en/dev/howto/deployment/
    
    
    
Security
--------

`vcert` makes no security claims and is provided AS-IS with NO WARRANTY. Django
has a number of security features that 'vcert' uses. It is recommended that you
use a unique `SECRET_KEY` and that you host the service on HTTPS using a valid
certificate.  User authentication is accomplished via django's standard `auth`
which uses salted and hashed passwords.

In order to enable a user to act as an administraor (i.e. verify/approve
certificates) you need to give access to the Django admin to said user. 
(`http://127.0.0.1:8000/admin` in a development
configuration). You can so this in two ways:

1. Make this user a superuser (with access to all models).
2. Set the is_staff flag and enable access on the `Certificate` models.

See https://docs.djangoproject.com/en/dev/topics/auth/ for more information on
authentication in Django.


Operation
---------

`vcert` operation is quite simple.  Any user with a CA account can create a new
"Trust anchor".  A trust anchor is the child certificate of the `vcerts`
certificate with signing authority. (Remember this is configured in
settings_local.py) After the Trust anchor request is made an email is sent to
the CA's verifier (`CA_VERIFIER_EMAIL` in`settings_local.py`).

What you do for "verification" is up to you.  After the
verifier verifies the information, then the verifier finds the certificate in
question within the Django admin, checks the "verify" box and then clicks save.  
(How you do verification is up to you).  When this happens, certificates are
published and an email notification is sent to the person requesting the
certificate.  Then the user may create leaf nodes off of the Trust Archor from
his or her account.  These, too, go through the same verification notification
and verification process before they may be accessed by the requestor. 


As written, `vcert` requires an invitation code to create an account.  This is
accomplished in the Django admin. Click the section that says "Invitations"
under "Accounts", then click "Add invitation", then provide an invitation code
and the email to which it should be sent.  Click "Save" and an email with the
code will be sent.  Anyone can use the invitation code.  In other words, it does
not require the new user to use the email in the invitation to register.


Happy CA-ing!

@aviars


    
