from django import VERSION
from django.conf.urls import url
from django.views.defaults import server_error


def raise_exception(request):
    raise Exception('This one should be handled by 500 technical view')


urlpatterns = [
    url(r'contacts/australia/(?P<value>[^/]+)/', lambda r, value: None, name='contacts_australia'),
    url(r'contacts/australia/(?P<value>\d+)/', lambda r, value: None, name='contacts_china'),
    url(r'raiser/', raise_exception, name='raiser'),
]


if VERSION < (1, 10):
    from django.conf.urls import patterns
    urlpatterns.insert(0, '')
    urlpatterns = patterns(*urlpatterns)


handler500 = lambda request: server_error(request, template_name='my500.html')
