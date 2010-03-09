'''
Created on Mar 8, 2010

@author: neild
'''

from datetime import datetime
import urllib2
from urlparse import urlparse

import facebook

from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from oshare.models import UserFacebookSession, FacebookPhotoAlbum, FacebookPhotoImage
from photos.models import Pool, Image

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
    user_fb_albums = FacebookPhotoAlbum.objects.filter(owner=user, tribes=tribe)
    albums_to_remove = user_fb_albums.exclude(aid__in=[album['aid'] for album in albums])
    for album in albums_to_remove:
        album.tribes.remove(tribe)
        # TODO: cascade remove all FacebookPhotoImage.image associations with the tribe 
        if album.tribes.count() == 0:
            album.delete()
        else:
            album.save()
        
    # associate new albums with the tribe
    for album in albums:
        fb_photo_album, created = user_fb_albums.get_or_create(aid=album['aid'], defaults=
                                            {'owner':user, 
                                             'name':album.get('name', '')
                                            })
        if tribe:
            fb_photo_album.tribes.add(tribe)
        fb_photo_album.save()
        get_new_fb_album_photos(fb_photo_album)
            
def get_new_fb_album_photos(album):
    """
    Import new photos from FacebookPhotoAlbum (album) and associate them with the tribe
    """
    try:
        fb_session, fb = get_user_fb_session(album.owner)
        
        # First see if the album on facebook has changed since we last checked
        fb_album = fb.photos.getAlbums(aids=album.aid)[0]
        fb_album_modified = datetime.utcfromtimestamp(fb_album['modified_major'] )
        if not fb_album_modified > album.modified:
            return # no need to go any further
        
        # get list of current photos in the album from facebook
        photos = fb.photos.get(aid=album.aid)
        
        # First remove any photos that we already have but are no longer in the facebook album (user removed them)
        fbis_to_remove = album.fb_photo_images.exclude(pid__in=[photo['pid'] for photo in photos])
        for fbi in fbis_to_remove.all():
            fbi.delete() # TODO: do we have to call fbi.image.delete() or does this cascade?
        
        # get list of pids we already know about for this album
        existing_pids = album.fb_photo_images.values_list('pid', flat=True)
        # Now add any new photos
        for photo in photos:
            if photo['pid'] in existing_pids:
                continue # we already have this photo imported
            # import photo
            url = photo['src_big']
            title = photo['caption']
            if not title:
                title = photo['pid']
            if len(url) == 0:
                url = photo['src']
                if len(url) == 0:
                    url = photo['src_small']
            if len(url) > 0:
                img_temp = NamedTemporaryFile()
                img_temp.write(urllib2.urlopen(url).read())
                img_temp.flush()
                name = urlparse(url).path.split('/')[-1]
                im = Image(title=title, caption=photo['caption'])
                im.member = album.owner;
                im.image.save(name, File(img_temp))
                # in group context we create a Pool object for it
                for tribe in album.tribes.all():
                    pool = Pool()
                    pool.photo = im
                    tribe.associate(pool)
                    pool.save()
                # create new FacebookPhotoImage model object to track this image
                fbi = FacebookPhotoImage(pid=photo['pid'], album=album, image=im)
                fbi.save()
                
        # update modified field in album 
        album.modified = fb_album_modified
        album.save()
                
    except UserFacebookSession.DoesNotExist:
        return
    except facebook.FacebookError:
        fb_session.delete()
    
