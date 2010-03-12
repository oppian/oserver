from django.conf.urls.defaults import *

urlpatterns = patterns("",
    url(r"^fblogin/$", "oshare.views.fblogin", name="oshare_fblogin"),
    url(r"^fblogout/$", "oshare.views.fblogout", name="oshare_fblogout"),
)