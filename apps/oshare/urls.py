from django.conf.urls.defaults import *

urlpatterns = patterns("",
    url(r"^fblogin/$", "oshare.views.fblogin", name="oshare_fblogin"),
)