from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from models import ( DomainBoundCertificate, TrustAnchorCertificate,
                    CertificateRevocationList, AnchorCertificateRevocationList)



class TreeViewAnchorCertificate(TrustAnchorCertificate):
    class Meta:
        proxy = True
        verbose_name = "Tree View of Anchor"


class DomainBoundCertificateAdmin(admin.ModelAdmin):
    
    list_display = ('common_name', 'verified','serial_number',
                    'organization', 'creation_date', 'expiration_date')
    
    search_fields = ('common_name','status', 'verified','serial_number',
                     'organization', 'creation_date', 'expiration_date')
    
admin.site.register(DomainBoundCertificate, DomainBoundCertificateAdmin)


class TrustAnchorCertificateAdmin(admin.ModelAdmin):
    
    #def queryset(self, request):
    #    return self.model.objects.filter(user = request.user)

    list_display = ('domain','parent', 'status', 'verified', 'serial_number',
                    'organization', 'creation_date', 'expiration_date')
    
    search_fields = ( 'common_name', 'domain', 'email',  'parent__common_name', 'status','verified', 'serial_number',
                     'organization', 'creation_date', 'expiration_date')

    
admin.site.register(TrustAnchorCertificate, TrustAnchorCertificateAdmin)





class TreeViewAdmin(MPTTModelAdmin):
                   
    search_fields = ('common_name','parent',)
    
    #def queryset(self, request):
    #    return self.model.objects.filter(user = request.user)
    
admin.site.register(TreeViewAnchorCertificate, TreeViewAdmin)



class CertificateRevocationListAdmin(admin.ModelAdmin):
    
    list_display = ('url', 'creation_date', 'creation_datetime')
    
    search_fields =('url', 'creation_date', 'creation_datetime')
    
admin.site.register(CertificateRevocationList, CertificateRevocationListAdmin)


class AnchorCertificateRevocationListAdmin(admin.ModelAdmin):
    
    list_display = ('url', 'creation_date', 'creation_datetime')
    
    search_fields =('url', 'creation_date', 'creation_datetime')
    
admin.site.register(AnchorCertificateRevocationList, AnchorCertificateRevocationListAdmin)
