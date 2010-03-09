
from datetime import datetime

from django.db import models
from django.db.models.fields.related import OneToOneField
from django.contrib.auth.models import User
from django.db.models.fields import CharField

from photos.models import Image
from tribes.models import Tribe
from groups.base import GroupAware

# Create your models here.


class UserFacebookSession(models.Model):
    """
    Ties a user's facebook session to their auth account
    """
    user = OneToOneField(User)
    uid = CharField(max_length=20, editable=False, unique=True)
    session_key = CharField(max_length=64, editable=False, unique=True)    
    secret = CharField(max_length=64, editable=False, unique=True)
    
    def __unicode__(self):
        return '%s : %s' % (self.user.username, self.uid)
    

class FacebookPhotoAlbum(GroupAware):
    """
    Class to represent a user's facebook album content
    """
    aid = models.CharField(max_length=32, db_index=True)
    name = models.TextField(blank=True)
    modified = models.DateTimeField(default=datetime.min) # actually maps to modified_major in FQL
    owner = models.ForeignKey(User) # django user, not fb FQL owner
    
    def __unicode__(self):
        return '%s : %s' % (self.name, self.aid)
    
class FacebookPhotoImage(models.Model):
    """
    Represents Image model instances that originate from Facebook album photos
    """
    pid = models.CharField(max_length=32, db_index=True)
    album = models.ForeignKey(FacebookPhotoAlbum, related_name='fb_photo_images')
    image = models.OneToOneField(Image)
    
 