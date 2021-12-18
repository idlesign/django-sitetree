from django.urls import re_path

from .views import index, listing, detailed


urlpatterns = [
    re_path(r'^$', index, name='index'),
    re_path(r'^articles/$', listing, name='articles-listing'),
    re_path(r'^articles/(?P<article_id>\d+)/$', detailed, name='articles-detailed'),
]
