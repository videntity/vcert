Custom and Local Install Instructions for Direct Certificate Authority and Test Tool
====================================================================================

This document outlines installing the software in Amazon web Service (AWS) Elastic Cloud Computing (EC2), but the information contained here is also mostly applicable to local installs. You won't need this if following these instructions, but the source code for this application can be found here. https://github.com/videntity/vcert.

This Amazon Machine Image (AMI) is a pre-built image that will lanch the Direct CA Console and the CA in AWS EC2.

It was created to streamline the setup of a separate personal installation and provide a full working example for those seeking to setup a local deployment.

The AMI is `ami-226f2248`.

You can use this URL to kick things off.

https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#LaunchInstanceWizard:ami=ami-226f2248


A micro-instance is suitble for a low traffic installation.

Overview of Stack Components
-----------------------------

* Ubuntu Linux 14.04 64-bit Version
* Apache2 with mod_wsgi
* Python 2.7 / Django 1.8.3
* Bootstrap, JQuery, JavaScript
* sqlite3
* OpenSSL
* A number of Python and C libraries



After your instance is lanched,  EC2 will assign a hostname and IP.

After the instance is fully launched, point your browser to

http://youhost.amazonaws.com replacing yourhost with your actual running instance's host name. You won't be able to see the console until DNS is configured.  See the first step below.

Your To Do Items To Complete and Customize the Installation:
============================================================


You'll need to map your CA console application and your CA static resource separately. Always run the console application over HTTPS.


**NOTE**: This software is provided without any warranty under the terms of the GPL v2 license. Commercial licenses avaialable.

Setup DNS
---------

Setup in your DNS server as follows two pointers back to your running instance..

* Set Console app host name to `caconsle.*` or `console.*`.
* Set the CA static resource hostname as `ca.*` or `sampleca.* *`.



Navigate to http://caconsonle.example.com  http://caconsole.example.com  and http://ca.example.com replacing `example.com` with your actual domain.

The core Apache2 configuration file exists her on the server: `/etc/apache2/sites-available/000-default.conf ` 


SSH Login
---------

This is not absolutley necessary, but you will need this for most any configuration change, to enable SSL, and to setup outbound email.

Login Example:


    ssh -i yourkey.pem ubuntu@yourhost.com

Credentials


* Username: `ubuntu`
* Password: `None`  (You'll use youe own EC2 certificates for access.) Use `sudo` or `sudo su -` for rootly commands.



Log Into the Admin
==================

This is the back office and system administration access to the application. Please note you can corrupt your database here if you aren't careful.

* Username: `videntity`
* Password: `changem3`

Point your browser to http://caconsole.example.com/admin, where example.com is your actual hostname.

The main thing you may want to do here is send invites for people to join. You'll need to setup email before that will work,

There are other administrative views of the data here.  You can also change user information. Explore carefully. Please see https://docs.djangoproject.com/en/1.9/ref/contrib/admin/ for more information.


Setup Outbound Email
--------------------

At the path `/home/ubuntu/django-projects/vcert/vcert/settings_local.py` make the following adjustments/additions.

Set

`SEND_CA_EMAIL = True`


Configure other EMAIL settings for your needs.

You will need to redefine/define some settings that begin with `EMAIL_` depending on your own needs. See https://docs.djangoproject.com/en/1.9/ref/settings/#email-backend for more information.

After this is done, restart Apache2 for the changes to take effect:

    sudo apache2ctl restart



Change the Host away from Example.com to your own
-------------------------------------------------


there are two main taks.

* Create your own root CA certificate pair.
* Redefine some settings in your `settings_local.py` file. 

To create your own root CA pair's do the following:

    cd /opt/ca
    
    openssl genrsa -out private/ca.example.comKey.pem 2048
    
    openssl req -sha256 -new -x509 -days 1826 -key private/ca.example.comKey.pem -out public/ca.example.com.pem
    
    openssl rsa -des3 -in ./private/ca.example.comKey.pem -out ./private/ca.example.comKey.pem


You'll need to redefine default settings by createing/ editing your settings_local.py file. See the file `/home/ubuntu/django-projects/vcert/vcert/settings_local_example.py` for details.  Be sure and restart Apache after making changes here with the following command.


    sudo apachectl restart





Enable HTTPS/SSL
----------------

Only use the console application using HTTPS. Enabling SSL will require obtaining certificates install onto the Apache webserver. This is well documented elswhere online. Here are a couple hints to get you going in the right direction:

 * Keep in mind, these certificates are separate from certificates generated from this application.
 * Here is a reasonable tutorial: https://www.digitalocean.com/community/tutorials/how-to-create-a-ssl-certificate-on-apache-for-ubuntu-12-04
