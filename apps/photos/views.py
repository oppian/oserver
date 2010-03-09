from urlparse import urlparse
import urllib2

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect, get_host
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext

from oshare.decorators import fb_login_required

from photos.forms import PhotoUploadForm, PhotoEditForm, FacebookPhotosForm
from photos.models import Image

from tribes.utils import group_and_bridge

@login_required
def upload(request, form_class=PhotoUploadForm,
        template_name="photos/upload.html", **kwargs):
    """
    upload form for photos
    """

    group, bridge = group_and_bridge(kwargs)

    photo_form = form_class(request.user, group)
    if request.method == "POST":
        if request.POST.get("action") == "upload":
            photo_form = form_class(request.user, group, request.POST, request.FILES)
            if photo_form.is_valid():
                photo = photo_form.save(commit=False)
                photo.member = request.user
                if group:
                    group.associate(photo, commit=False)
                photo.save()

                messages.add_message(request, messages.SUCCESS,
                    ugettext("Successfully uploaded photo '%s'") % photo.title
                )

                include_kwargs = {"id": photo.id}
                if group:
                    redirect_to = bridge.reverse("photo_details", group, kwargs=include_kwargs)
                else:
                    redirect_to = reverse("photo_details", kwargs=include_kwargs)

                return HttpResponseRedirect(redirect_to)

    return {
        "TEMPLATE": template_name,
        "group": group,
        "photo_form": photo_form,
    }


@login_required
def yourphotos(request, template_name="photos/yourphotos.html", **kwargs):
    """
    photos for the currently authenticated user
    """

    group, bridge = group_and_bridge(kwargs)

    photos = Image.objects.filter(member=request.user)

    # filter by group
    if group:
        photos = group.content_objects(photos)

    photos = photos.order_by("-date_added")

    return {
        "TEMPLATE": template_name,
        "group": group,
        "photos": photos,
    }

# TODO: write is group member decorator
@login_required
def photos(request, template_name="photos/latest.html", **kwargs):
    """
    latest photos
    """

    group, bridge = group_and_bridge(kwargs)

    photos = Image.objects.filter(
        Q(is_public=True) |
        Q(is_public=False, member=request.user)
    )

    # filter by group, otherwise show only with no group set
    if group:
        photos = group.content_objects(photos)
    else:
        photos = photos.filter(object_id=None)

    photos = photos.order_by("-date_added")

    return {
        "group": group,
        "photos": photos,
        'TEMPLATE': template_name,
    }


@login_required
def details(request, id, template_name="photos/details.html", **kwargs):
    """
    show the photo details
    """

    group, bridge = group_and_bridge(kwargs)

    photos = Image.objects.all()

    if group:
        photos = group.content_objects(photos)
    else:
        photos = photos.filter(object_id=None)

    photo = get_object_or_404(photos, id=id)

    # @@@: test
    if not photo.is_public and request.user != photo.member:
        raise Http404

    photo_url = photo.get_display_url()
    host = "http://%s" % get_host(request)

    return {
        "TEMPLATE": template_name,
        "group": group,
        "host": host,
        "photo": photo,
        "photo_url": photo_url,
        "is_me": photo.member == request.user,
    }


@login_required
def memberphotos(request, username, template_name="photos/memberphotos.html", **kwargs):
    """
    Get the members photos and display them
    """

    group, bridge = group_and_bridge(kwargs)

    # test user exists
    user = get_object_or_404(User, username=username)

    photos = Image.objects.filter(
        member=user,
        is_public=True,
    )

    if group:
        photos = group.content_objects(photos)
    else:
        photos = photos.filter(object_id=None)

    photos = photos.order_by("-date_added")

    return {
        "TEMPLATE": template_name,
        "group": group,
        "photos": photos,
    }


@login_required
def edit(request, id, form_class=PhotoEditForm,
        template_name="photos/edit.html", **kwargs):

    group, bridge = group_and_bridge(kwargs)

    photos = Image.objects.all()

    if group:
        photos = group.content_objects(photos)
    else:
        photos = photos.filter(object_id=None)

    photo = get_object_or_404(photos, pk=id)
    photo_url = photo.get_display_url()

    if request.method == "POST":
        if photo.member != request.user:
            messages.add_message(request, messages.ERROR,
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

    return {
        "TEMPLATE": template_name,
        "group": group,
        "photo_form": photo_form,
        "photo": photo,
        "photo_url": photo_url,
    }

@login_required
def destroy(request, id, **kwargs):

    group, bridge = group_and_bridge(kwargs)

    photos = Image.objects.all()

    if group:
        photos = group.content_objects(photos)
    else:
        photos = photos.filter(object_id=None)

    photo = get_object_or_404(photos, pk=id)
    title = photo.title

    if group:
        redirect_to = bridge.reverse("photos_yours", group)
    else:
        redirect_to = reverse("photos_yours")

    if photo.member != request.user:
        messages.add_message(request, messages.ERROR,
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
def fbphotos(request, template_name="photos/facebook.html", **kwargs):
    """
    Fetch photos from facebook
    """

    group, bridge = group_and_bridge(kwargs)
        
    fb_user = request.fb.users.getInfo(request.fb.uid)[0]
    fb_albums = [album for album in request.fb.photos.getAlbums() if album['type'] != 'profile']
    # since facebook doesn't give us the album cover image urls directly we need to retrieve them in batch
    cover_pids_csv = ', '.join([album['cover_pid'] for album in fb_albums])
    cover_urls = [photo['src_small'] for photo in request.fb.photos.get(pids=cover_pids_csv)]
    albums = []
    for album in fb_albums:
        new_album = {'id': album['aid'], 'name':album['name'], 'thumb_url':cover_urls[len(albums)]}
        albums.append(new_album)
        
    if request.POST:
        # Form is being submitted
        albums_form = FacebookPhotosForm(objects=albums, data=request.POST)
        if albums_form.is_valid():
            for aid in albums_form.cleaned_data['selected_ids']:
                # for each album ...
                photos = request.fb.photos.get(aid=aid)
                for photo in photos:
                    url = photo['src_big']
                    title = photo['caption']
                    if not title:
                        title = photo['pid']
                    if len(url) == 0:
                        url = photo['src']
                        if len(url) == 0:
                            url = photo['src_small']
                    if len(url) > 0:
                        # fetch url and save it
                        img_temp = NamedTemporaryFile()
                        img_temp.write(urllib2.urlopen(url).read())
                        img_temp.flush()
                        name = urlparse(url).path.split('/')[-1]
                        
                        # create image
                        im = Image(
                            title = title, 
                            caption = photo['caption'],
                            member = request.user,
                        )
                        if group:
                            group.associate(im)
                        im.image.save(name, File(img_temp))
            if group:
                redirect_to = bridge.reverse("photos", group)
            else:
                redirect_to = reverse("photos")
            return HttpResponseRedirect(redirect_to)
 
    albums_form = FacebookPhotosForm(objects=albums)

    return {
        "TEMPLATE": template_name,
        "group": group,
        "fb_user": fb_user,
        "fb_albums": albums,
        "fb_form" : albums_form,
    }

