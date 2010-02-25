'''
Created on Feb 25, 2010

@author: neild
'''

from django.conf import settings
from django.contrib.auth.decorators import login_required

import facebook

from oshare.models import UserFacebookSession

def fb_login_required(func):
    
    def wrapped_view_func(request, *args, **kwargs):
        try:
            # look up user's facebook session (if they have one)
            fb_session = request.user.userfacebooksession; # reverse of OneToOneField
            # prev session found, setup Facebook object for REST api calls
            fb = facebook.Facebook(settings.FACEBOOK_API_KEY, settings.FACEBOOK_SECRET_KEY)
            fb.session_key = fb_session.session_key
            fb.secret = fb_session.secret
            fb.uid = fb_session.uid
            # store session and api object on the request for use by decorated view funcs
            request.fb = fb
            request.fb_session = fb_session
        except UserFacebookSession.DoesNotExist:
            request.fb = None
            request.fb_session = None
        return func(request, *args, **kwargs)
    
    return login_required(wrapped_view_func)