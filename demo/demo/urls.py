from django.conf.urls import url

from .views import index, listing, detailed


urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^articles/$', listing, name='articles-listing'),
    url(r'^articles/(?P<article_id>\d+)/$', detailed, name='articles-detailed'),
]
