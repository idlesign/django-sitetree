

def test_form(common_tree):
    from sitetree.toolbox import TreeItemForm

    form = TreeItemForm(tree='mytree', tree_item='root')

    items_field = form.fields['tree_item']

    assert items_field.tree == 'mytree'
    assert items_field.initial == 'root'
    assert len(items_field.choices) == len(common_tree)


def test_field(common_tree):
    from sitetree.toolbox import TreeItemChoiceField

    len_common_tree = len(common_tree)
    items_field = TreeItemChoiceField('mytree', initial='root')

    assert items_field.tree == 'mytree'
    assert items_field.initial == 'root'
    assert len(items_field.choices) == len_common_tree

    home_item = common_tree['']
    item = items_field.clean(home_item.id)

    assert item == home_item

    assert items_field.clean('') is None
    assert items_field.clean(len_common_tree + 100) is None  # Unknown id

    items_field = TreeItemChoiceField(home_item.tree, initial='root')
    assert items_field.tree == 'mytree'
