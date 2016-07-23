#! /usr/bin/env python
import sys
import os

from django.conf import settings, global_settings


APP_NAME = 'sitetree'


def main():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    if not settings.configured:

        configure_kwargs = dict(
            INSTALLED_APPS=('django.contrib.auth', 'django.contrib.contenttypes', APP_NAME),
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'}},
            ROOT_URLCONF='sitetree.tests',
            MIDDLEWARE_CLASSES=global_settings.MIDDLEWARE_CLASSES,  # Prevents Django 1.7 warning.
        )

        try:
            configure_kwargs['TEMPLATE_CONTEXT_PROCESSORS'] = tuple(global_settings.TEMPLATE_CONTEXT_PROCESSORS) + (
                'django.core.context_processors.request',
            )

        except AttributeError:

            # Django 1.8+
            configure_kwargs['TEMPLATES'] = [
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'APP_DIRS': True,
                },
            ]

        settings.configure(**configure_kwargs)

    try:  # Django 1.7 +
        from django import setup
        setup()
    except ImportError:
        pass

    from django.test.utils import get_runner
    runner = get_runner(settings)()
    failures = runner.run_tests((APP_NAME,))

    sys.exit(failures)


if __name__ == '__main__':
    main()
