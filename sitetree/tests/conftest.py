import os
try:
    from unittest import mock
except ImportError:
    import mock

import pytest

from django.conf import settings, global_settings
from django import VERSION
from django.template.context import Context
from django.template.base import Template


def pytest_configure():

    app_name = os.path.basename(os.path.dirname(os.path.dirname(__file__)))

    if not pytest.config.pluginmanager.hasplugin('django'):
        raise Exception('`pytest-django` package is required to run `%s` tests.' % app_name)

    configure_kwargs = dict(
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            app_name,
            '%s.tests' % app_name
        ),
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        MIDDLEWARE_CLASSES=global_settings.MIDDLEWARE_CLASSES,  # Prevents Django 1.7 warning.
        ROOT_URLCONF='%s.tests.urls' % app_name,
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'APP_DIRS': True,
        }],
    )

    try:
        # Django < 1.8
        configure_kwargs['TEMPLATE_CONTEXT_PROCESSORS'] = tuple(global_settings.TEMPLATE_CONTEXT_PROCESSORS) + (
            'django.core.context_processors.request',
        )
    except AttributeError:
        pass

    settings.configure(**configure_kwargs)


class MockUser(object):

    def __init__(self, user_data):
        authorized = user_data
        permissions = None

        if isinstance(user_data, tuple):
            authorized, permissions = user_data

        self.authorized = authorized
        self.permissions = permissions

    def is_authenticated(self):
        return self.authorized

    def get_all_permissions(self):
        return self.permissions


class MockRequest(object):

    def __init__(self, path='/', user_data=None, meta=None):
        self.path = path
        self.user = MockUser(user_data)
        self.META = meta


@pytest.fixture
def mock_template_context():

    def get_context(context_dict=None, current_app='', request_path=None, user_data=None):

        context_dict = context_dict or {}
        context_dict.update({
            'request': MockRequest(request_path, user_data),
        })

        context = Context(context_dict)
        context.template = mock.MagicMock()
        context.template.engine.string_if_invalid = ''

        if VERSION >= (1, 10):
            match = mock.MagicMock()
            match.app_name = current_app
            context.resolver_match = match

        else:
            context._current_app = current_app

        return context

    return get_context


@pytest.fixture
def build_tree():
    """Builds a sitetree from dict definition.
    Returns items indexed by urls.

    Example:
        items_map = build_tree(
            {'alias': 'mytree'},
            [{
                'title': 'one', 'url': '/one/', 'children': [
                    {'title': 'subone', 'url': '/subone/'}
                ]
            }]
        )

    """
    from sitetree.models import Tree, TreeItem

    def build(tree_dict, items):

        def attach_items(tree, items, parent=None):
            for item_dict in items:
                children = item_dict.pop('children', [])

                item = TreeItem(**item_dict)
                item.tree = tree
                item.parent = parent
                item.save()

                items_map['%s' % item.url] = item

                children and attach_items(tree, children, parent=item)

        items_map = {}

        tree = Tree(**tree_dict)
        tree.save()
        attach_items(tree, items)

        return items_map

    return build


@pytest.fixture
def render_template_tag():
    """Renders a template tag from a given library by its name.

    Example:
        render_template_tag('library_name', 'mytag arg1 arg2')

    """
    def render(tag_library, tag_str, context=None):
        context = context or {}
        context = Context(context)
        string = '{%% load %s %%}{%% %s %%}' % (tag_library, tag_str)
        return Template(string).render(context)
    return render
