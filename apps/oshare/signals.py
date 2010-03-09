'''
Created on Mar 9, 2010

@author: neild
'''

from django.db.models.signals import post_delete

from oshare.models import FacebookPhotoImage

def on_delete_fb_photo_image(sender, instance=None, **kwargs):
    """
    Cascade delete to the FacebookPhotoImage.image (OneToOneField)
    """
    if instance:
        instance.image.delete()
    

post_delete.connect(on_delete_fb_photo_image, sender=FacebookPhotoImage)
