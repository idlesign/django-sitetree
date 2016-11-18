from django import VERSION
from django.conf.urls import url


urlpatterns = [
    url(r'contacts/australia/(?P<value>[^/]+)/', lambda r, value: None, name='contacts_australia'),
    url(r'contacts/australia/(?P<value>\d+)/', lambda r, value: None, name='contacts_china'),
]

if VERSION < (1, 10):
    from django.conf.urls import patterns
    urlpatterns.insert(0, '')
    urlpatterns = patterns(*urlpatterns)
