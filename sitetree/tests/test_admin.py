#! -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from django.contrib.admin.sites import site


def get_item_admin():
    from sitetree.models import TreeItem
    from sitetree.admin import TreeItemAdmin
    admin = TreeItemAdmin(TreeItem, site)
    return admin


@pytest.mark.django_db
def test_admin_tree_item_basic(mock_request, common_tree):

    admin = get_item_admin()
    admin.tree = common_tree['']
    form = admin.get_form(mock_request())

    known_url_names = form.known_url_names
    assert set(known_url_names) == {'contacts_china', 'contacts_australia'}


@pytest.mark.django_db
def test_admin_tree_item_move(mock_request, common_tree):
    from sitetree.models import TreeItem, Tree

    main_tree = Tree(alias='main')
    main_tree.save()

    new_item_1 = TreeItem(title='title_1', sort_order=1, tree_id=main_tree.pk)
    new_item_1.save()

    new_item_2 = TreeItem(title='title_2', sort_order=2, tree_id=main_tree.pk)
    new_item_2.save()

    new_item_3 = TreeItem(title='title_3', sort_order=3, tree_id=main_tree.pk)
    new_item_3.save()

    admin = get_item_admin()

    admin.item_move(None, None, new_item_2.id, 'up')

    assert TreeItem.objects.get(pk=new_item_1.id).sort_order == 2
    assert TreeItem.objects.get(pk=new_item_2.id).sort_order == 1
    assert TreeItem.objects.get(pk=new_item_3.id).sort_order == 3

    admin.item_move(None, None, new_item_1.id, 'down')

    assert TreeItem.objects.get(pk=new_item_1.id).sort_order == 3
    assert TreeItem.objects.get(pk=new_item_2.id).sort_order == 1
    assert TreeItem.objects.get(pk=new_item_3.id).sort_order == 2


@pytest.mark.django_db
def test_admin_tree_item_get_tree(mock_request, common_tree):
    home = common_tree['']
    tree = home.tree

    admin = get_item_admin()

    assert admin.get_tree(mock_request(), tree.pk) == tree
    assert admin.get_tree(mock_request(), None, home.pk) == tree


@pytest.mark.django_db
def test_admin_tree_item_save_model(mock_request, common_tree):
    users = common_tree['/users/']
    tree = users.tree

    admin = get_item_admin()

    # Simulate bogus
    admin.previous_parent = users.parent
    users.parent = users

    admin.tree = tree
    admin.save_model(mock_request(), users, None, change=True)

    assert users.tree == admin.tree
    assert users.parent == admin.previous_parent


@pytest.mark.django_db
def test_admin_tree():
    from sitetree.admin import TreeAdmin
    from sitetree.models import Tree

    admin = TreeAdmin(Tree, site)
    urls = admin.get_urls()

    assert len(urls) > 0
