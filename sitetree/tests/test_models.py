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
