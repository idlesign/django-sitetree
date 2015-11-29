from django.template import Library

register = Library()

try:
    # Django < 1.9.0
    from django.templatetags.future import url
except ImportError:
    from django.template.defaulttags import url
