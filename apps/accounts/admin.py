from django.contrib import admin
from models import UserProfile, ValidPasswordResetKey, Invitation, ValidSignupKey


admin.site.register(UserProfile)
admin.site.register(ValidPasswordResetKey)
admin.site.register(ValidSignupKey)

class InvitationAdmin(admin.ModelAdmin):
    
    list_display =  ('code', 'valid', 'email')
    search_fields = ('code', 'valid', 'email')
    
admin.site.register(Invitation, InvitationAdmin)