from django.contrib import admin

from oshare.models import UserFacebookSession



class UserFacebookSessionAdmin(admin.ModelAdmin):
    readonly_fields = ('user', 'uid', 'session_key', 'secret')

 
admin.site.register(UserFacebookSession, UserFacebookSessionAdmin)

