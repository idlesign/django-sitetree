#!/usr/bin/env python
from django.conf import settings
from django.core.management import call_command


if not settings.configured:
    settings.configure(
        INSTALLED_APPS=('django.contrib.auth', 'django.contrib.contenttypes', 'sitetree'),
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'}},
    )

if __name__ == "__main__":
    call_command('test', 'sitetree')
