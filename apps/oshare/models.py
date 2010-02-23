from django.db import models
from django.db.models.fields.related import ForeignKey, OneToOneField
from django.contrib.auth.models import User
from django.db.models.fields import CharField
from account.forms import UNIQUE_EMAIL

# Create your models here.


class UserFacebookSession(models.Model):
    """
    Ties a user's facebook session to their auth account
    """
    user = OneToOneField(User)
    uid = CharField(max_length=20, editable=False, unique=True)
    session_key = CharField(max_length=64, editable=False, unique=True)    
    secret = CharField(max_length=64, editable=False, unique=True)