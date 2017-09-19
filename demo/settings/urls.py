from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from demo import urls as demo_urls


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include(demo_urls, namespace='demo')),
]


if settings.DEBUG and settings.USE_DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
