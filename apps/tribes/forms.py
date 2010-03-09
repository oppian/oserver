from django import forms
from django.utils.translation import ugettext_lazy as _

from tribes.models import Tribe



# @@@ we should have auto slugs, even if suggested and overrideable


class TribeForm(forms.ModelForm):
    
    slug = forms.SlugField(max_length=20,
        help_text = _("a short version of the name consisting only of letters, numbers, underscores and hyphens."),
    )
    
    def clean_slug(self):
        if Tribe.objects.filter(slug__iexact=self.cleaned_data["slug"]).exists():
            raise forms.ValidationError(_("A tribe already exists with that slug."))
        return self.cleaned_data["slug"].lower()
    
    def clean_name(self):
        if Tribe.objects.filter(name__iexact=self.cleaned_data["name"]).exists():
            raise forms.ValidationError(_("A tribe already exists with that name."))
        return self.cleaned_data["name"]
    
    class Meta:
        model = Tribe
        fields = ["name", "slug", "description"]


# @@@ is this the right approach, to have two forms where creation and update fields differ?

class TribeUpdateForm(forms.ModelForm):
    
    def clean_name(self):
        if Tribe.objects.filter(name__iexact=self.cleaned_data["name"]).exists():
            if self.cleaned_data["name"] == self.instance.name:
                pass # same instance
            else:
                raise forms.ValidationError(_("A tribe already exists with that name."))
        return self.cleaned_data["name"]
    
    class Meta:
        model = Tribe
        fields = ["name", "description"]
        
class GroupForm(forms.ModelForm):
    def __init__(self, user=None, group=None, *args, **kwargs):
        self.user = user
        self.group = group
        super(GroupForm, self).__init__(*args, **kwargs)
        
    def check_group_membership(self):
        """
        We only let valid group members.
        """
        if self.group and not self.group.user_is_member(self.user):
            raise forms.ValidationError(_("You must be a member"))
