import json

from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, get_host
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils import simplejson

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from groups.templatetags.group_tags import groupurl

import facebook

from photologue.models import *

from photos.models import Image, Pool
from photos.forms import PhotoUploadForm, PhotoEditForm

from oshare.models import UserFacebookSession
from oshare.decorators import fb_login_required



@login_required
def upload(request, form_class=PhotoUploadForm,
        template_name="photos/upload.html", group_slug=None, bridge=None):
    """
    upload form for photos
    """
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    photo_form = form_class()
    if request.method == "POST":
        if request.POST.get("action") == "upload":
            photo_form = form_class(request.user, request.POST, request.FILES)
            if photo_form.is_valid():
                photo = photo_form.save(commit=False)
                photo.member = request.user
                photo.save()
                
                # in group context we create a Pool object for it
                if group:
                    pool = Pool()
                    pool.photo = photo
                    group.associate(pool)
                    pool.save()
                
                messages.add_message(request, messages.SUCCESS,
                    ugettext("Successfully uploaded photo '%s'") % photo.title
                )
                
                include_kwargs = {"id": photo.id}
                if group:
                    redirect_to = bridge.reverse("photo_details", group, kwargs=include_kwargs)
                else:
                    redirect_to = reverse("photo_details", kwargs=include_kwargs)
                
                return HttpResponseRedirect(redirect_to)
    
    return render_to_response(template_name, {
        "group": group,
        "photo_form": photo_form,
    }, context_instance=RequestContext(request))


@login_required
def yourphotos(request, template_name="photos/yourphotos.html", group_slug=None, bridge=None):
    """
    photos for the currently authenticated user
    """
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    photos = Image.objects.filter(member=request.user)
    
    if group:
        photos = group.content_objects(photos, join="pool")
    else:
        photos = photos.filter(pool__object_id=None)
    
    photos = photos.order_by("-date_added")
    
    return render_to_response(template_name, {
        "group": group,
        "photos": photos,
    }, context_instance=RequestContext(request))


@login_required
def photos(request, template_name="photos/latest.html", group_slug=None, bridge=None):
    """
    latest photos
    """
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    photos = Image.objects.filter(
        Q(is_public=True) |
        Q(is_public=False, member=request.user)
    )
    
    if group:
        photos = group.content_objects(photos, join="pool")
    else:
        photos = photos.filter(pool__object_id=None)
    
    photos = photos.order_by("-date_added")
    
    # check if ajax query
    if request.is_ajax():
        import json
        return json.JsonResponse(photos)
    
    return render_to_response(template_name, {
        "group": group,
        "photos": photos,
    }, context_instance=RequestContext(request))


@login_required
def details(request, id, template_name="photos/details.html", group_slug=None, bridge=None):
    """
    show the photo details
    """
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    photos = Image.objects.all()
    
    if group:
        photos = group.content_objects(photos, join="pool")
    else:
        photos = photos.filter(pool__object_id=None)
    
    photo = get_object_or_404(photos, id=id)
    
    # @@@: test
    if not photo.is_public and request.user != photo.member:
        raise Http404
    
    photo_url = photo.get_display_url()
    
    title = photo.title
    host = "http://%s" % get_host(request)
    
    if photo.member == request.user:
        is_me = True
    else:
        is_me = False
    
    return render_to_response(template_name, {
        "group": group,
        "host": host,
        "photo": photo,
        "photo_url": photo_url,
        "is_me": is_me,
    }, context_instance=RequestContext(request))


@login_required
def memberphotos(request, username, template_name="photos/memberphotos.html", group_slug=None, bridge=None):
    """
    Get the members photos and display them
    """
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    user = get_object_or_404(User, username=username)
    
    photos = Image.objects.filter(
        member__username = username,
        is_public = True,
    )
    
    if group:
        photos = group.content_objects(photos, join="pool")
    else:
        photos = photos.filter(pool__object_id=None)
    
    photos = photos.order_by("-date_added")
    
    return render_to_response(template_name, {
        "group": group,
        "photos": photos,
    }, context_instance=RequestContext(request))


@login_required
def edit(request, id, form_class=PhotoEditForm,
        template_name="photos/edit.html", group_slug=None, bridge=None):
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    photos = Image.objects.all()
    
    if group:
        photos = group.content_objects(photos, join="pool")
    else:
        photos = photos.filter(pool__object_id=None)
    
    photo = get_object_or_404(photos, id=id)
    photo_url = photo.get_display_url()
    
    if request.method == "POST":
        if photo.member != request.user:
            message.add_message(request, messages.ERROR,
                ugettext("You can't edit photos that aren't yours")
            )
            include_kwargs = {"id": photo.id}
            if group:
                redirect_to = bridge.reverse("photo_details", group, kwargs=include_kwargs)
            else:
                redirect_to = reverse("photo_details", kwargs=include_kwargs)
            
            return HttpResponseRedirect(reverse('photo_details', args=(photo.id,)))
        if request.POST["action"] == "update":
            photo_form = form_class(request.user, request.POST, instance=photo)
            if photo_form.is_valid():
                photoobj = photo_form.save(commit=False)
                photoobj.save()
                
                messages.add_message(request, messages.SUCCESS,
                    ugettext("Successfully updated photo '%s'") % photo.title
                )
                
                include_kwargs = {"id": photo.id}
                if group:
                    redirect_to = bridge.reverse("photo_details", group, kwargs=include_kwargs)
                else:
                    redirect_to = reverse("photo_details", kwargs=include_kwargs)
                
                return HttpResponseRedirect(redirect_to)
        else:
            photo_form = form_class(instance=photo)
    
    else:
        photo_form = form_class(instance=photo)
    
    return render_to_response(template_name, {
        "group": group,
        "photo_form": photo_form,
        "photo": photo,
        "photo_url": photo_url,
    }, context_instance=RequestContext(request))

@login_required
def destroy(request, id, group_slug=None, bridge=None):
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
    
    photos = Image.objects.all()
    
    if group:
        photos = group.content_objects(photos, join="pool")
    else:
        photos = photos.filter(pool__object_id=None)
    
    photo = get_object_or_404(photos, id=id)
    title = photo.title
    
    if group:
        redirect_to = bridge.reverse("photos_yours", group)
    else:
        redirect_to = reverse("photos_yours")
    
    if photo.member != request.user:
        message.add_message(request, messages.ERROR,
            ugettext("You can't edit photos that aren't yours")
        )
        return HttpResponseRedirect(redirect_to)
    
    if request.method == "POST" and request.POST["action"] == "delete":
        photo.delete()
        messages.add_message(request, messages.SUCCESS,
            ugettext("Successfully deleted photo '%s'") % title
        )
    
    return HttpResponseRedirect(redirect_to)

@fb_login_required
def fbphotos(request, 
             template_name="photos/facebook.html", group_slug=None, bridge=None, fb_login_view='photo_fblogin'):
    """
    Fetch photos from facebook
    """
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
            fb_login_url = bridge.reverse(fb_login_view, group)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
        fb_login_url = reverse(fb_login_view)
        
    fb_user = None;
    albums = None;
    next_url = 'http://%s%s' % (request.get_host(), fb_login_url)
    cancel_url = 'http://www.facebook.com/connect/login_failure.html'
    fb_login_url = 'http://www.facebook.com/login.php?api_key=%s&connect_display=page&v=1.0&next=%s&cancel_url=%s&fbconnect=true&return_session=true&session_key_only=false&req_perms=offline_access' % (settings.FACEBOOK_API_KEY, next_url, cancel_url)
    
    if request.fb:
        try:
            fb_user = request.fb.users.getInfo(request.fb.uid)[0]
            fb_albums = request.fb.photos.getAlbums()
            # since facebook doesn't give us the album cover image urls directly we need to retrieve them in batch
            cover_pids_csv = ', '.join([album['cover_pid'] for album in fb_albums])
            cover_urls = [photo['src_small'] for photo in request.fb.photos.get(pids=cover_pids_csv)]
            albums = []
            for album in fb_albums:
                new_album = {'aid': album['aid'], 'name':album['name'], 'cover_url':cover_urls[len(albums)]}
                albums.append(new_album)
        except:
            request.fb_session.delete()

    return render_to_response(template_name, {
        "fb_user": fb_user,
        "fb_albums": albums,
        "fb_login_url": fb_login_url,
        }, context_instance=RequestContext(request))
    
@login_required
def fblogin(request, group_slug=None, bridge=None, next_view='photo_fbphotos'):
    """
    Process facebook login success
    """
    
    if bridge:
        try:
            group = bridge.get_group(group_slug)
            url = bridge.reverse(next_view, group)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
        url = reverse(next_view)
        
    # first remove any previous session
    try:
        fb_session = request.user.userfacebooksession; # reverse of OneToOneField
        fb_session.delete()
    except UserFacebookSession.DoesNotExist:
        pass
    
    # store new fb session info
    fb_session_info = simplejson.loads(request.GET['session'])
    fb_user_session = UserFacebookSession()
    fb_user_session.uid = fb_session_info.get('uid', None)
    fb_user_session.session_key = fb_session_info.get('session_key', None)
    fb_user_session.secret = fb_session_info.get('secret', None)
    fb_user_session.user = request.user
    fb_user_session.save()
    
    return HttpResponseRedirect(url)

