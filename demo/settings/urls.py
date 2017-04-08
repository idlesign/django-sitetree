from django.conf.urls import url, include
from django.contrib import admin
from demo import urls as demo_urls


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include(demo_urls, namespace='demo')),
]
