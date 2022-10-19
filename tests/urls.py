from django.contrib import admin
from django.contrib.auth import urls as auth_urls
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(auth_urls)),
    path("herald/", include("herald.urls")),
]
