import os
try:
    from unittest import mock
except ImportError:
    import mock

import pytest

from django.http import HttpRequest
from django.conf import settings, global_settings
from django import VERSION
from django.template.context import Context, RenderContext
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


class MockRequest(HttpRequest):

    def __init__(self, path='/', user=None, meta=None):
        self.path = path
        self.user = user
        self.META = meta


def contribute_to_context(context, current_app=''):
    template = mock.MagicMock()
    template.engine.string_if_invalid = ''

    context.template = template

    if VERSION >= (1, 11):
        context.render_context = RenderContext()

    if VERSION >= (1, 10):
        match = mock.MagicMock()
        match.app_name = current_app
        context.resolver_match = match

    else:
        context._current_app = current_app

@pytest.fixture
def mock_request():

    def get_request(**kwargs):
        return MockRequest(**kwargs)

    return get_request


@pytest.fixture
def mock_template_context():

    def get_context(context_dict=None, current_app='', request_path=None, user_data=None):

        user = user_data if hasattr(user_data, '_meta') else MockUser(user_data)

        context_dict = context_dict or {}
        context_updater = {
            'request': MockRequest(request_path, user),
        }
        if user_data:
            context_updater['user'] = user

        context_dict.update(context_updater)

        context = Context(context_dict)
        contribute_to_context(context, current_app)
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
    from django.contrib.auth.models import Permission

    def build(tree_dict, items):

        def attach_items(tree, items, parent=None):
            for item_dict in items:
                children = item_dict.pop('children', [])

                access_permissions = item_dict.pop('access_permissions', [])

                item = TreeItem(**item_dict)
                item.tree = tree
                item.parent = parent
                item.save()

                for permission in access_permissions:
                    item.access_permissions.add(Permission.objects.get(codename=permission))

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

        if not isinstance(context, Context):
            context = Context(context)

        contribute_to_context(context)
        string = '{%% load %s %%}{%% %s %%}' % (tag_library, tag_str)
        template = Template(string)

        if VERSION >= (1, 11):
            # Prevent "TypeError: 'NoneType' object is not iterable" in  get_exception_info
            template.nodelist[1].token.position = (0, 0)

        return template.render(context)
    return render


@pytest.fixture
def common_tree(build_tree):
    items = build_tree(
        {'alias': 'mytree'},
        [{
            'title': 'Home', 'url': '/home/', 'children': [
                {'title': 'Users', 'url': '/users/', 'children': [
                    {'title': 'Moderators', 'url': '/users/moderators/'},
                    {'title': 'Ordinary', 'url': '/users/ordinary/'},
                    {'title': 'Hidden', 'hidden': True, 'url': '/users/hidden/'},
                ]},
                {'title': 'Articles', 'url': '/articles/', 'children': [
                    {'title': 'About cats', 'url': '/articles/cats/', 'children': [
                        {'title': 'Good', 'url': '/articles/cats/good/'},
                        {'title': 'Bad', 'url': '/articles/cats/bad/'},
                        {'title': 'Ugly', 'url': '/articles/cats/ugly/'},
                    ]},
                    {'title': 'About dogs', 'url': '/articles/dogs/'},
                    {'title': 'About mice', 'inmenu': False, 'url': '/articles/mice/'},
                ]},
                {'title': 'Contacts', 'inbreadcrumbs': False, 'url': '/contacts/', 'children': [
                    {'title': 'Russia', 'url': '/contacts/russia/',
                     'hint': 'The place', 'description': 'Russian Federation', 'children': [
                        {'title': 'Web', 'alias': 'ruweb', 'url': '/contacts/russia/web/', 'children': [
                            {'title': 'Public {{ subtitle }}', 'url': '/contacts/russia/web/public/'},
                            {'title': 'Private',
                             'url': '/contacts/russia/web/private/',
                             'hint': 'Private Area Hint',
                             'description': 'Private Area Description',
                             },
                        ]},
                        {'title': 'Postal', 'insitetree': False, 'url': '/contacts/russia/postal/'},
                    ]},
                    {'title': 'Australia', 'urlaspattern': True, 'url': 'contacts_australia australia_var',
                     'children': [
                         {'title': 'Alice Springs', 'access_loggedin': True, 'url': '/contacts/australia/alice/'},
                         {'title': 'Darwin', 'access_guest': True, 'url': '/contacts/australia/darwin/'},
                     ]},
                    {'title': 'China', 'urlaspattern': True, 'url': 'contacts_china china_var'},
                ]},
            ]
        }]
    )
    items[''] = items['/home/']
    return items
