
from django import forms
from django.utils.translation import ugettext_lazy as _

from photos.models import Image
from photos.widgets import TableCheckboxSelectMultiple

from tribes.forms import GroupForm
from django.forms.models import ModelForm


class PhotoUploadForm(GroupForm):
    
    class Meta:
        model = Image
        exclude = ["member", "photoset", "title_slug", "effect", "crop_from", 'group_content_type', 'group_object_id']
        
    def clean_image(self):
        if "#" in self.cleaned_data["image"].name:
            raise forms.ValidationError(
                _("Image filename contains an invalid character: '#'. Please remove the character and try again."))
        return self.cleaned_data["image"]
        
    def clean(self):
        self.check_group_membership()
        return self.cleaned_data
    



class PhotoEditForm(ModelForm):
    
    class Meta:
        model = Image
        exclude = [
            "member",
            "photoset",
            "title_slug",
            "effect",
            "crop_from",
            "image",
            'group_content_type', 'group_object_id',
        ]
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(PhotoEditForm, self).__init__(*args, **kwargs)

class FacebookPhotosForm(forms.Form):
    """
    Maybe used for album ids (aids) or picture ids (pids)
    """
    
    selected_ids = forms.MultipleChoiceField(required=False, label='')
    
    def __init__(self, objects=(), initial=[], *args, **kwargs):
        super(FacebookPhotosForm, self).__init__(*args, **kwargs)
        # set choice field's choices dynamically
        choices = [(obj['aid'], obj['name']) for obj in objects]
        thumbs = [obj['thumb_url'] for obj in objects]
        self.fields['selected_ids'].choices = choices        
        self.fields['selected_ids'].initial = initial        
        self.fields['selected_ids'].widget = TableCheckboxSelectMultiple(choices=choices, thumb_urls=thumbs, cols_count=3)