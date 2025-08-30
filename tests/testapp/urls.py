from django.shortcuts import render
from django.urls import re_path, path
from django.contrib import admin
from django.views.defaults import server_error
from .models import MyModel


def raise_exception(request):
    raise Exception('This one should be handled by 500 technical view')


def show_mymodel(request):
    model = MyModel(afield='thisismine')
    model.save()
    return render(request, 'mymodel.html', {'model': model})


urlpatterns = [
    path('mymodel/', show_mymodel),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'contacts/australia/(?P<value>[^/]+)/', lambda r, value: None, name='contacts_australia'),
    re_path(r'contacts/australia/(?P<value>\d+)/', lambda r, value: None, name='contacts_china'),
    re_path(r'raiser/', raise_exception, name='raiser'),
    re_path(r'^devices/(?P<grp>([\w() 0-9a-zA-Z!*:.?+=_-])+)$', lambda r, value: None, name='devices_grp'),
]

handler500 = lambda request: server_error(request, template_name='my500.html')
