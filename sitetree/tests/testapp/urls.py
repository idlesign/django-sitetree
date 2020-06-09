from django.conf.urls import url
from django.contrib import admin
from django.views.defaults import server_error


def raise_exception(request):
    raise Exception('This one should be handled by 500 technical view')


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'contacts/australia/(?P<value>[^/]+)/', lambda r, value: None, name='contacts_australia'),
    url(r'contacts/australia/(?P<value>\d+)/', lambda r, value: None, name='contacts_china'),
    url(r'raiser/', raise_exception, name='raiser'),
]

handler500 = lambda request: server_error(request, template_name='my500.html')
