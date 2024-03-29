from django.conf import settings
from django.urls import path, include
from django.contrib import admin


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('demo.urls', 'demo'), namespace='demo')),
]


if settings.DEBUG and settings.USE_DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
