import pytest

from pytest_djangoapp import configure_djangoapp_plugin

pytest_plugins = configure_djangoapp_plugin(
    settings=dict(
        SITETREE_CLS='sitetree.tests.testapp.mysitetree.MySiteTree',
    ),
    admin_contrib=True,
)


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

                items_map[f'{item.url}'] = item

                children and attach_items(tree, children, parent=item)

        items_map = {}

        tree = Tree(**tree_dict)
        tree.save()
        attach_items(tree, items)

        return items_map

    return build


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
