Experimenting with OpenSSL for the Direct Project
=================================================

DRAFT (in progress)



Web Resources
-------------

http://www.madboa.com/geek/openssl/
http://www.sslshopper.com/article-most-common-openssl-commands.html
http://blog.didierstevens.com/2008/12/30/howto-make-your-own-cert-with-openssl/
http://unitstep.net/blog/2009/03/16/using-the-basic-constraints-extension-in-x509-v3-certificates-for-intermediate-cas/




CA Functions
------------



Create the CA (public and private key)


    cd /opt/ca
    openssl req -nodes -config conf/ca.directca.org.cnf -days 7330 -x509 -newkey rsa:4096 -out public/ca.directca.org.pem -outform PEM
    openssl rsa -des3 -in ./private/ca.directca.orgKey.pem -out ./private/ca.directca.orgKey.pem

Create the CSR and private key for the subordinate CA


    openssl req -subj "/emailAddress=directca@videntity.com/C=US/ST=West Virginia/L=Williamsburg/CN=ca.directca.org/O=DirectCA.org Videntity Systems Inc. - For testing only"  -out ca.directca.org.csr -new -newkey rsa:4096 -keyout  ./private/ca.directca.orgKey.pem


Sign the subordinate CA's CSR and generate a new public cert using the root CA's key


    openssl ca -batch -config conf/ca.videntity.com.cnf -in ca.directca.org.csr -out ./public/ca.directca.org.pem





Add a new CA or interm. cert to base Java.

keytool -import -trustcacerts -alias ca.videntity.com -file ca.videntity.com.der -keystore /usr/lib/jvm/java-1.7.0-openjdk-amd64/jre/lib/security/cacerts


Other Useful Commands
---------------------

Fetch the serial number from a certificate
    
    openssl x509 -in CERTIFICATE_FILE.pem -serial -noout
    openssl x509 -in CERTIFICATE_FILE.der -inform DER -serial -noout


Fetch the sha1_fingerprint from a certificate

     openssl x509 -in CERTIFICATE_FILE.pem -fingerprint -noout
     openssl x509 -in CERTIFICATE_FILE.der -inform DER -fingerprint -noout

Create a Key:

    openssl genrsa -out ca-root.key 1024

Create a Certificate

    openssl req -x509 -nodes -days 365  -subj '/emailAddress=root@direct.transparenthealth.org/C=US/ST=Maryland/L=Baltimore/CN=direct.transparenthealth.org/O=TransparentHealth/' -key ca-root.key -keyout ca-root.der -out ca-root.crt
    openssl req -x509 -nodes -days 365  -key ca-root.key -subj '/emailAddress=root@direct.transparenthealth.org/C=US/ST=Maryland/L=Baltimore/CN=direct.transparenthealth.org/O=TransparentHealth/'  -keyout ca-root.pem -out ca-root.pem


Convert a der-based key generated with certGen to a PEM (also removes the password)

    openssl pkcs8 -inform der -in transparenthealth.orgKey.der -out out.pem -outform pem


PKCS#8 format, DER encoding, no encryption

    openssl pkcs8 -topk8 -in openssl_key.pem -inform pem -out openssl_key_pk8.der -outform der -nocrypt

Convert a DER file (.crt .cer .der) to PEM

    openssl x509 -inform der -in certificate.cer -out certificate.pem

Convert a PEM file to DER

    openssl x509 -outform der -in certificate.pem -out certificate.der

Convert a PKCS#12 file (.pfx .p12) containing a private key and certificates to PEM

    openssl pkcs12 -in keyStore.pfx -out keyStore.pem -nodes

You can add -nocerts to only output the private key or add -nokeys to only output the certificates.
    

Convert a PEM certificate file and a private key to PKCS#12 (.pfx .p12)

    openssl pkcs12 -export -out certificate.pfx -inkey privateKey.key -in certificate.crt -certfile CACert.crt

How do I extract information from a pkcs12 certificate?

    openssl pkcs12 -info -in filename.pfx


How do I extract information from a certificate?

    openssl x509 -text -in cert.pem

Who issued the cert?
 
   openssl x509 -noout -in cert.pem -subject

To whom was it issued?

    openssl x509 -noout -in cert.pem -subject
    
for what dates is it valid?

    openssl x509 -noout -in cert.pem -dates

the above, all at once

    openssl x509 -noout -in cert.pem -issuer -subject -dates


Read the infromation out of a CRL

    openssl crl -in direct-ca-crl.pem -noout -text

