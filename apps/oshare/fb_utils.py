'''
Created on Mar 8, 2010

@author: neild
'''

from datetime import datetime
import urllib2 #@UnresolvedImport - Shuts PyDev up
from urlparse import urlparse #@UnresolvedImport - Shuts PyDev up

import facebook

from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from oshare.models import UserFacebookSession, FacebookPhotoAlbum, FacebookPhotoImage
from photos.models import Image

def get_user_fb_session(user):
    """
    Lookup facebook user session. May throw UserFacebookSession.DoesNotExist
    """
    # look up user's facebook session (if they have one)
    fb_session = user.userfacebooksession; # reverse of OneToOneField
    # prev session found, setup Facebook object for REST api calls
    fb = facebook.Facebook(settings.FACEBOOK_API_KEY, settings.FACEBOOK_SECRET_KEY)
    fb.session_key = fb_session.session_key
    fb.secret = fb_session.secret
    fb.uid = fb_session.uid
    return (fb_session, fb)

def add_or_remove_fb_albums(user, tribe=None, albums=[]):
    """
    Add or remove FacebookPhotoAlbum model objects from tribe as necessary 
    depending if the album id is in list of albums
    """
    # remove albums belonging to this user that are NOT in aids from the tribe
    user_fb_albums = FacebookPhotoAlbum.objects.filter(owner=user)
    if tribe:
        user_fb_albums = tribe.content_objects(user_fb_albums)
    albums_to_remove = user_fb_albums.exclude(aid__in=[album['aid'] for album in albums])
    for album in albums_to_remove:
        album.delete()
        
    # associate new albums with the tribe
    for album in albums:
        fb_photo_album, created = user_fb_albums.get_or_create(aid=album['aid'], defaults=
                                            {'owner':user, 
                                             'name':album.get('name', '')
                                            })
        if tribe:
            tribe.associate(fb_photo_album)
        fb_photo_album.save()
        get_new_fb_album_photos(fb_photo_album)
            
def get_new_fb_album_photos(album):
    """
    Import new photos from FacebookPhotoAlbum (album) and associate them with the tribe
    """
    num_added = 0
    num_deleted = 0
    num_modified = 0
    try:
        fb_session, fb = get_user_fb_session(album.owner)
        
        # First see if the album on facebook has changed since we last checked
        fb_album = fb.photos.getAlbums(aids=album.aid)[0]
        fb_album_modified = datetime.utcfromtimestamp(fb_album['modified'])
        if not fb_album_modified > album.modified:
            return (0,0,0) # no need to go any further
        
        # get list of current photos in the album from facebook
        photos = fb.photos.get(aid=album.aid)
        
        # First remove any photos that we already have but are no longer in the facebook album (user removed them)
        fbis_to_remove = album.fb_photo_images.exclude(pid__in=[photo['pid'] for photo in photos])
        num_deleted = fbis_to_remove.count()
        for fbi in fbis_to_remove.all():
            fbi.delete() 
        
        # get list of facebook images we already know about for this album
        existing_fbis = album.fb_photo_images.all().select_related()
        existing_pids = album.fb_photo_images.values_list('pid', flat=True)
        # Now add any new photos
        for photo in photos:
            fbi = None
            pid = photo['pid']
            fb_image_modified = datetime.utcfromtimestamp(photo['modified'])
            if pid in existing_pids: 
                # we already have this photo imported, look it up
                fbi = existing_fbis.get(pid=pid)
                # See if it has been modified since we imported it
                if not fb_image_modified > fbi.modified:
                    continue # this image hasn't changed since we imported it
            # import photo
            url = photo['src_big']
            if len(url) == 0:
                url = photo['src']
                if len(url) == 0:
                    url = photo['src_small']
            if len(url) > 0:
                img_temp = NamedTemporaryFile()
                img_temp.write(urllib2.urlopen(url).read())
                img_temp.flush()
                name = urlparse(url).path.split('/')[-1]
                if fbi:
                    # Updating existing image
                    fbi.modified = fb_image_modified
                    fbi.image.caption = photo['caption']
                    fbi.image.image.save(name, File(img_temp))
                    num_modified = num_modified + 1
                else:
                    # Importing new image
                    im = Image(title=pid, caption=photo['caption'], member=album.owner)
                    album.group.associate(im)
                    im.image.save(name, File(img_temp))
                    # create new FacebookPhotoImage model object to track this image
                    fbi = FacebookPhotoImage(pid=pid, modified=fb_image_modified, album=album, image=im)
                    num_added = num_added + 1
                fbi.save()
                
        # update modified field in album 
        album.modified = fb_album_modified
        album.save()
                
    except UserFacebookSession.DoesNotExist: #@UndefinedVariable - shuts PyDev up
        return
    except facebook.FacebookError:
        fb_session.delete()
    
    return (num_added, num_deleted, num_modified)
    
