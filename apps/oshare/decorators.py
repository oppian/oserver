'''
Created on Feb 25, 2010

@author: neild
'''

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response

import facebook

from oshare.models import UserFacebookSession

def fb_login_required(func):
    
    def wrapped_view_func(request, *args, **kwargs):
        resp = None
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
            resp = func(request, *args, **kwargs)
        except facebook.FacebookError:
            fb_session.delete()
        except UserFacebookSession.DoesNotExist:
            pass   
        
        if not resp:
            fb_login_path = reverse('oshare_fblogin')
            next_url = '%s?nextview=%s' % (request.build_absolute_uri(fb_login_path), request.get_full_path())
            cancel_url = 'http://www.facebook.com/connect/login_failure.html'
            fb_login_url = 'http://www.facebook.com/login.php?api_key=%s&connect_display=page&v=1.0&next=%s&cancel_url=%s&fbconnect=true&return_session=true&session_key_only=false&req_perms=offline_access' % (settings.FACEBOOK_API_KEY, next_url, cancel_url)
            resp = render_to_response('oshare/fb_login.html', {"fb_login_url": fb_login_url} )
            
        return resp      
    
    return login_required(wrapped_view_func)