#! -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import pytest


def test_model_tree():
    from sitetree.models import Tree

    tree = Tree(alias='test')
    tree.save()

    assert str(tree) == tree.alias
    assert tree.get_title() == tree.alias

    with pytest.raises(Exception):
        Tree(alias='test').save()  # Unique alias


def test_model_tree_item():
    from sitetree.models import Tree, TreeItem

    tree1 = Tree(alias='test')
    tree1.save()

    item1 = TreeItem(tree=tree1, alias='only', title='only title')
    item1.save()

    assert str(item1) == item1.title

    item2 = TreeItem(tree=tree1, alias='other', parent=item1)
    item2.save()

    item3 = TreeItem(tree=tree1, parent=item1)
    item3.save()

    item3.sort_order = 100
    item3.parent = item3
    item3.save()

    assert item3.parent is None  # Can't be itself
    assert item3.sort_order == 100

    item3.sort_order = 0
    item3.save()

    assert item3.sort_order == item3.id  # Automatic ordering

    with pytest.raises(Exception):
        TreeItem(tree=tree1, alias='only').save()  # Unique alias within tree


def test_sitetree_url():
    """ Few simple tests to ensure SiteTree.url function works properly """
    from sitetree.models import Tree, TreeItem
    from sitetree.sitetreeapp import get_sitetree
    tree1 = Tree(alias='test')
    tree1.save()
    st = get_sitetree()

    item = TreeItem(tree=tree1, alias='other', url='foo', pk=1)
    assert st.url(item) == "foo"

    item = TreeItem(tree=tree1, alias='other', url='foo/bar', pk=2)
    assert st.url(item) == "foo/bar"

    item = TreeItem(tree=tree1, alias='other', url='contacts_china \'2\'', urlaspattern=True, pk=3)
    assert st.url(item) == "/contacts/australia/2/"

    item = TreeItem(tree=tree1, alias='other', url='contacts_china 2', urlaspattern=True, pk=4)
    assert st.url(item) == "/contacts/australia/2/"

    item = TreeItem(tree=tree1, alias='other', url='contacts_china', urlaspattern=True, pk=6)
    assert st.url(item) == "#unresolved"

    # Test that any of the symbols inserted as url don't break the app
    item = TreeItem(tree=tree1, alias='other', url='!contacts_china$%^čř%*#$@=!§¨`°"', urlaspattern=True, pk=7)
    assert st.url(item) == "#unresolved"

    # Test for bug #257
    item = TreeItem(tree=tree1, alias='other', url="contacts_ch'ina", urlaspattern=True, pk=8)
    assert st.url(item) == "#unresolved"
