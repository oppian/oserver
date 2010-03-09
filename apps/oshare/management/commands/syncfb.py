'''
Created on Mar 9, 2010

@author: neild
'''

from django.core.management.base import BaseCommand

from oshare.fb_utils import get_new_fb_album_photos
from oshare.models import FacebookPhotoAlbum

class Command(BaseCommand):
    """
    Iterate over all FacebookPhotoAlbum model objects in the db and update them from Facebook
    """
    def handle(self, *args, **options):
        for album in FacebookPhotoAlbum.objects.all():
            num_added, num_deleted = get_new_fb_album_photos(album)
            if num_added:
                print 'Imported %d photos from album: %s for user: %s' % (num_added, album, album.owner)
            if num_deleted:
                print 'Deleted %d photos from album: %s for user: %s' % (num_deleted, album, album.owner)
