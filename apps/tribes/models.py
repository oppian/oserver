import datetime

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import  User

from groups.base import GroupBase, GroupAware

from autoslug.fields import AutoSlugField

class Tribe(GroupBase, GroupAware):
   
    slug = AutoSlugField(_("slug"), populate_from='name', unique=True)
    name = models.CharField(_("name"), max_length=80)
    creator = models.ForeignKey(User, verbose_name=_("creator"), related_name="%(class)s_created")
    created = models.DateTimeField(_("created"), default=datetime.datetime.now)
    description = models.TextField(_("description"))
    
    members = models.ManyToManyField(User,
        related_name = "tribes",
        verbose_name = _("members")
    )
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("tribe_detail", kwargs={"tribe_slug": self.slug})
