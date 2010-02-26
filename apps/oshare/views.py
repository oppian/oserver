# Create your views here.

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.utils import simplejson

from oshare.models import UserFacebookSession

@login_required
def fblogin(request, group_slug=None, bridge=None):
    """
    Process facebook login success
    """
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
        
        
    # first remove any previous session
    try:
        fb_session = request.user.userfacebooksession; # reverse of OneToOneField
        fb_session.delete()
    except UserFacebookSession.DoesNotExist:
        pass
    
    next_view = request.GET.get('nextview', '/')
    # store new fb session info
    fb_session_info = simplejson.loads(request.GET['session'])
    fb_user_session = UserFacebookSession()
    fb_user_session.uid = fb_session_info.get('uid', None)
    fb_user_session.session_key = fb_session_info.get('session_key', None)
    fb_user_session.secret = fb_session_info.get('secret', None)
    fb_user_session.user = request.user
    fb_user_session.save()
    
    return HttpResponseRedirect(next_view)

