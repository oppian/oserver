from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from tagging.models import Tag, TaggedItem

from blog.models import Post
from bookmarks.models import BookmarkInstance
from photos.models import Image
# from tribes.models import Tribe
# from tribes.models import Topic as TribeTopic



def tags(request, tag, template_name="tags/index.html"):
    tag = get_object_or_404(Tag, name=tag)
    
    alltags = TaggedItem.objects.get_by_model(Post, tag).filter(status=2)
    
    phototags = TaggedItem.objects.get_by_model(Image, tag)
    bookmarktags = TaggedItem.objects.get_by_model(BookmarkInstance, tag)
   
    return render_to_response(template_name, {
        "tag": tag,
        "alltags": alltags,
        "phototags": phototags,
        "bookmarktags": bookmarktags,
    }, context_instance=RequestContext(request))
