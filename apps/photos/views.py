from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect, get_host
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext
from oshare.decorators import fb_login_required
from oshare.fb_utils import add_or_remove_fb_albums
from photos.forms import PhotoUploadForm, PhotoEditForm, FacebookPhotosForm
from photos.models import Pool, Image


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

    return {
        "group": group,
        "photos": photos,
        'TEMPLATE': template_name,
    }


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
        member__username=username,
        is_public=True,
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
def fbphotos(request,
             template_name="photos/facebook.html", group_slug=None, bridge=None):
    """
    Fetch photos from facebook
    """

    if bridge:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None
        
    fb_user = request.fb.users.getInfo(request.fb.uid)[0]
    fb_albums = [album for album in request.fb.photos.getAlbums() if album['type'] != 'profile']
    # since facebook doesn't give us the album cover image urls directly we need to retrieve them in batch
    cover_pids_csv = ', '.join([album['cover_pid'] for album in fb_albums])
    cover_urls = [photo['src_small'] for photo in request.fb.photos.get(pids=cover_pids_csv)]
    for i, album in enumerate(fb_albums):
        album['thumb_url'] = cover_urls[i]
        
    if request.POST:
        # Form is being submitted
        albums_form = FacebookPhotosForm(objects=fb_albums, data=request.POST)
        if albums_form.is_valid():
            selected_ids = albums_form.cleaned_data['selected_ids']
            selected_albums = [album for album in fb_albums if album['aid'] in selected_ids]
            # create/associate/remove fb albums from the tribe as necessary
            add_or_remove_fb_albums(request.user, tribe=group, albums=selected_albums)
            
            if group:
                redirect_to = bridge.reverse("photos", group)
            else:
                redirect_to = reverse("photos")
            return HttpResponseRedirect(redirect_to)
 
    albums_form = FacebookPhotosForm(objects=fb_albums)

    return render_to_response(template_name, {
        "group": group,
        "fb_user": fb_user,
        "fb_albums": fb_albums,
        "fb_form" : albums_form,
        }, context_instance=RequestContext(request))

