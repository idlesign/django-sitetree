import pytest

from sitetree.sitetreeapp import _DYNAMIC_TREES, _IDX_ORPHAN_TREES
from sitetree.toolbox import compose_dynamic_tree, get_dynamic_trees, item, register_dynamic_trees, tree


def test_dynamic_only(template_render_tag, template_context, template_strip_tags, monkeypatch):
    # If DYNAMIC_ONLY is not set, pytest-django will tell: "Database access not allowed" on any DB access attempt.
    monkeypatch.setattr('sitetree.sitetreeapp.DYNAMIC_ONLY', 'UNKNOWN')

    register_dynamic_trees(compose_dynamic_tree([tree('dynamic1', items=[
            item('dynamic1_1', '/dynamic1_1_url', url_as_pattern=False, sort_order=2),
        ])]), reset_cache=True)

    result = template_strip_tags(template_render_tag('sitetree', 'sitetree_tree from "dynamic1"', template_context()))

    assert 'dynamic1_1' in result


dynamic_access_checked = []


def dynamic_access_check_it(tree):
    dynamic_access_checked.append('yes')
    return True


def test_dynamic_basic(template_render_tag, template_context, template_strip_tags):

    item_dyn_attrs = item('dynamic2_1', '/dynamic2_1_url', url_as_pattern=False, dynamic_attrs={'a': 'b'})
    assert item_dyn_attrs.a == 'b'

    item_dyn_access_check = item(
        'dynamic1_1', '/dynamic1_1_url', url_as_pattern=False, sort_order=2,
        access_check=dynamic_access_check_it
    )
    assert item_dyn_access_check.access_check is dynamic_access_check_it

    trees = [
        compose_dynamic_tree([tree('dynamic1', items=[
            item_dyn_access_check,
            item('dynamic1_2', '/dynamic1_2_url', url_as_pattern=False, sort_order=1),
        ])]),
        compose_dynamic_tree([tree('dynamic2', items=[
            item_dyn_attrs,
            item('dynamic2_2', '/dynamic2_2_url', url_as_pattern=False),
        ])]),
    ]

    register_dynamic_trees(*trees, reset_cache=True)  # new less-brackets style
    result = template_strip_tags(template_render_tag('sitetree', 'sitetree_tree from "dynamic1"', template_context()))

    assert 'dynamic1_1|dynamic1_2' in result
    assert 'dynamic2_1' not in result
    assert dynamic_access_checked == ['yes']

    register_dynamic_trees(trees)

    result = template_strip_tags(template_render_tag('sitetree', 'sitetree_tree from "dynamic1"', template_context()))
    assert 'dynamic1_1|dynamic1_2' in result
    assert 'dynamic2_1' not in result

    trees = get_dynamic_trees()
    assert len(trees[_IDX_ORPHAN_TREES]) == 2

    _DYNAMIC_TREES.clear()


def test_dynamic_attach(template_render_tag, template_context, template_strip_tags, common_tree):

    children = [
        item('dynamic2_2_child', '/dynamic2_2_url_child', url_as_pattern=False),
    ]

    register_dynamic_trees([
        compose_dynamic_tree([tree('dynamic1', items=[
            item('dynamic1_1', '/dynamic1_1_url', url_as_pattern=False),
            item('dynamic1_2', '/dynamic1_2_url', url_as_pattern=False),
        ])], target_tree_alias='mytree'),

        compose_dynamic_tree([tree('dynamic2', items=[
            item('dynamic2_1', '/dynamic2_1_url', url_as_pattern=False),
            item('dynamic2_2', '/dynamic2_2_url', url_as_pattern=False, children=children),
        ], title='some_title')], target_tree_alias='mytree', parent_tree_item_alias='ruweb'),

    ])
    result = template_strip_tags(template_render_tag('sitetree', 'sitetree_tree from "mytree"', template_context()))

    assert 'Web|dynamic2_1|dynamic2_2' in result
    assert 'China|dynamic1_1|dynamic1_2' in result

    _DYNAMIC_TREES.clear()


def test_dynamic_attach_from_module(template_render_tag, template_context, template_strip_tags, settings):

    register_dynamic_trees(compose_dynamic_tree('tests.testapp', include_trees=['dynamic4']))

    result = template_strip_tags(template_render_tag('sitetree', 'sitetree_tree from "dynamic4"', template_context()))

    assert 'dynamic4_1' in result

    settings.DEBUG = True
    with pytest.warns(UserWarning, match='Unable to register dynamic sitetree'):
        compose_dynamic_tree('nonexistent')

    _DYNAMIC_TREES.clear()


def test_dynamic_attach_dynamic_into_dynamic(template_render_tag, template_context, template_strip_tags):

    register_dynamic_trees([
        compose_dynamic_tree([tree("base_dyn", items=[
            item("base item", "/base/", url_as_pattern=False, alias="base_item"),
        ])]),
        compose_dynamic_tree([tree("attached_dyn", items=[
            item("attached item", "/attached/", url_as_pattern=False),
        ])], target_tree_alias="base_dyn", parent_tree_item_alias="base_item"),
    ], reset_cache=True)

    result = template_strip_tags(template_render_tag('sitetree', 'sitetree_tree from "base_dyn"', template_context()))

    assert "base item" in result
    assert "attached item" in result

    _DYNAMIC_TREES.clear()
