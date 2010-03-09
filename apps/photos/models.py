from datetime import datetime

from django.core.urlresolvers import reverse
from django.db import models

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from photologue.models import *

from tagging.fields import TagField

from django.utils.translation import ugettext_lazy as _
from groups.base import GroupAware



PUBLISH_CHOICES = (
    (1, _("Public")),
    (2, _("Private")),
)



class PhotoSet(models.Model):
    """
    A set of photos
    """
    
    name = models.CharField(_("name"), max_length=200)
    description = models.TextField(_("description"))
    publish_type = models.IntegerField(_("publish_type"),
        choices = PUBLISH_CHOICES,
        default = 1
    )
    tags = TagField()
    
    class Meta:
        verbose_name = _("photo set")
        verbose_name_plural = _("photo sets")


class Image(ImageModel, GroupAware):
    """
    A photo with its details
    """
    
    SAFETY_LEVEL = (
        (1, _("Safe")),
        (2, _("Not Safe")),
    )
    title = models.CharField(_("title"), max_length=200)
    title_slug = models.SlugField(_("slug"))
    caption = models.TextField(_("caption"), blank=True)
    date_added = models.DateTimeField(_("date added"),
        default = datetime.now,
        editable = False
    )
    is_public = models.BooleanField(_("is public"),
        default = True,
        help_text = _("Public photographs will be displayed in the default views.")
    )
    member = models.ForeignKey(User,
        related_name = "added_photos",
        blank = True,
        null = True
    )
    safetylevel = models.IntegerField(_("safetylevel"),
        choices = SAFETY_LEVEL,
        default = 1
    )
    photoset = models.ManyToManyField(PhotoSet,
        blank = True,
        verbose_name = _("photo set")
    )
    tags = TagField()
    
    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self, group=None):
        kwargs = {"id": self.pk}
        view_name = "photo_details"
        # We check for attachment of a group. This way if the Image object
        # is not attached to the group the application continues to function.
        if group:
            return group.content_bridge.reverse(view_name, group, kwargs)
        return reverse(view_name, kwargs=kwargs)


