from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

from account.openid_consumer import PinaxConsumer
from account.forms import GroupEmailSignupForm


handler500 = "pinax.views.server_error"
 


urlpatterns = patterns("",
    url(r"^$", direct_to_template, {
        "template": "homepage.html",
    }, name="home"),
    
    url(r"^account/signup/$", 'account.views.signup', { 'form_class': GroupEmailSignupForm }, name="acct_signup"),
    
    (r"^about/", include("about.urls")),
    (r"^account/", include("account.urls")),
    (r"^openid/(.*)", PinaxConsumer()),
    (r"^profiles/", include("basic_profiles.urls")),
    (r"^notices/", include("notification.urls")),
    (r"^announcements/", include("announcements.urls")),
    (r"^messages/", include("messages.urls")),
    
    (r"^photos/", include("photos.urls")),
    (r"^avatar/", include("avatar.urls")),
    (r"^flag/", include("flag.urls")),
    (r"^comments/", include("threadedcomments.urls")),
    (r"^tribes/", include("tribes.urls")),
    (r"^tags/", include("tag_app.urls")),
    (r"^oshare/", include("oshare.urls")),
    
    (r"^admin/", include(admin.site.urls)),
)

if settings.SERVE_MEDIA:
    urlpatterns += patterns("",
        (r"", include("staticfiles.urls")),
    )
