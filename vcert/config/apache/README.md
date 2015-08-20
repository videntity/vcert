Apache Configuration
===================

This directory contains example files to load the application in a production environment using apache2 and mod_wsgi.

The file 'django.wsgi' can stay put, but the file 'default' should be in the apache2 sites-available folder.  On Ubuntu this file is located here 

    /etc/apache2/sites-available/default


Make sure the paths are correct in 'django.wsgi' and 'default' files. The default path is:

    /home/ubuntu/

This is designed to work without any changes on AWS, so you may need to adjust slightly in a different hosting configutation.

Cheers,

Alan
