from datetime import datetime

from django import forms
from django.utils.translation import ugettext_lazy as _

from photos.models import Image
from photos.widgets import TableCheckboxSelectMultiple


class PhotoUploadForm(forms.ModelForm):
    
    class Meta:
        model = Image
        exclude = ["member", "photoset", "title_slug", "effect", "crop_from"]
        
    def clean_image(self):
        if "#" in self.cleaned_data["image"].name:
            raise forms.ValidationError(
                _("Image filename contains an invalid character: '#'. Please remove the character and try again."))
        return self.cleaned_data["image"]
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(PhotoUploadForm, self).__init__(*args, **kwargs)


class PhotoEditForm(forms.ModelForm):
    
    class Meta:
        model = Image
        exclude = [
            "member",
            "photoset",
            "title_slug",
            "effect",
            "crop_from",
            "image",
        ]
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(PhotoEditForm, self).__init__(*args, **kwargs)

class FacebookPhotosForm(forms.Form):
    """
    Maybe used for album ids (aids) or picture ids (pids)
    """
    
    selected_ids = forms.MultipleChoiceField(label='')
    
    def __init__(self, objects=(), *args, **kwargs):
        super(FacebookPhotosForm, self).__init__(*args, **kwargs)
        # set choice field's choices dynamically
        choices = [(obj['aid'], obj['name']) for obj in objects]
        thumbs = [obj['thumb_url'] for obj in objects]
        self.fields['selected_ids'].choices = choices        
        self.fields['selected_ids'].widget = TableCheckboxSelectMultiple(choices=choices, thumb_urls=thumbs, cols_count=3)