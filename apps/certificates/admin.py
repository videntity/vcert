from django.contrib import admin
from models import ( DomainBoundCertificate, TrustAnchorCertificate,
                    CertificateRevocationList, AnchorCertificateRevocationList)


class DomainBoundCertificateAdmin(admin.ModelAdmin):
    
    list_display = ('domain', 'status', 'verified','serial_number',
                    'organization', 'creation_date', 'expiration_date')
    
    search_fields = ('domain','status', 'verified','serial_number',
                     'organization', 'creation_date', 'expiration_date')
    
admin.site.register(DomainBoundCertificate, DomainBoundCertificateAdmin)


class TrustAnchorCertificateAdmin(admin.ModelAdmin):
    
    list_display = ('domain','status', 'verified', 'serial_number',
                    'organization', 'creation_date', 'expiration_date')
    
    search_fields = ('domain', 'status','verified', 'serial_number',
                     'organization', 'creation_date', 'expiration_date')
    
admin.site.register(TrustAnchorCertificate, TrustAnchorCertificateAdmin)


class CertificateRevocationListAdmin(admin.ModelAdmin):
    
    list_display = ('url', 'creation_date', 'creation_datetime')
    
    search_fields =('url', 'creation_date', 'creation_datetime')
    
admin.site.register(CertificateRevocationList, CertificateRevocationListAdmin)


class AnchorCertificateRevocationListAdmin(admin.ModelAdmin):
    
    list_display = ('url', 'creation_date', 'creation_datetime')
    
    search_fields =('url', 'creation_date', 'creation_datetime')
    
admin.site.register(AnchorCertificateRevocationList, AnchorCertificateRevocationListAdmin)
