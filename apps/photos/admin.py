from django.contrib import admin

from photos.models import Image



class PhotoAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "title_slug",
        "caption",
        "date_added",
        "is_public",
        "member",
        "safetylevel",
        "tags",
    ]



admin.site.register(Image, PhotoAdmin)
