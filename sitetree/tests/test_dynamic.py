#! -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import re

import pytest


RE_TAG_VALUES = re.compile('>([^<]+)<')


def strip_tags(src):

    result = []
    for match in RE_TAG_VALUES.findall(src):
        match = match.strip()
        if match:
            result.append(match)

    return '|'.join(result)


@pytest.mark.django_db
def test_dynamic_basic(render_template_tag, mock_template_context):

    from sitetree.toolbox import compose_dynamic_tree, register_dynamic_trees, tree, item

    trees = [
        compose_dynamic_tree([tree('dynamic1', items=[
            item('dynamic1_1', '/dynamic1_1_url', url_as_pattern=False, sort_order=2),
            item('dynamic1_2', '/dynamic1_2_url', url_as_pattern=False, sort_order=1),
        ])]),
        compose_dynamic_tree([tree('dynamic2', items=[
            item('dynamic2_1', '/dynamic2_1_url', url_as_pattern=False),
            item('dynamic2_2', '/dynamic2_2_url', url_as_pattern=False),
        ])]),
    ]

    register_dynamic_trees(*trees)  # new less-brackets style
    result = strip_tags(render_template_tag('sitetree', 'sitetree_tree from "dynamic1"', mock_template_context()))

    assert 'dynamic1_1|dynamic1_2' in result
    assert 'dynamic2_1' not in result

    register_dynamic_trees(trees,)

    result = strip_tags(render_template_tag('sitetree', 'sitetree_tree from "dynamic1"', mock_template_context()))
    assert 'dynamic1_1|dynamic1_2' in result
    assert 'dynamic2_1' not in result


@pytest.mark.django_db
def test_dynamic_attach(render_template_tag, mock_template_context, common_tree):

    from sitetree.toolbox import compose_dynamic_tree, register_dynamic_trees, tree, item

    register_dynamic_trees([
        compose_dynamic_tree([tree('dynamic1', items=[
            item('dynamic1_1', '/dynamic1_1_url', url_as_pattern=False),
            item('dynamic1_2', '/dynamic1_2_url', url_as_pattern=False),
        ])], target_tree_alias='mytree'),

        compose_dynamic_tree([tree('dynamic2', items=[
            item('dynamic2_1', '/dynamic2_1_url', url_as_pattern=False),
            item('dynamic2_2', '/dynamic2_2_url', url_as_pattern=False),
        ])], target_tree_alias='mytree', parent_tree_item_alias='ruweb'),

    ])
    result = strip_tags(render_template_tag('sitetree', 'sitetree_tree from "mytree"', mock_template_context()))

    assert 'Web|dynamic2_1|dynamic2_2' in result
    assert 'China|dynamic1_1|dynamic1_2' in result


@pytest.mark.django_db
def test_dynamic_attach_from_module(render_template_tag, mock_template_context, settings):

    from sitetree.toolbox import compose_dynamic_tree, register_dynamic_trees

    register_dynamic_trees(compose_dynamic_tree('tests', include_trees=['dynamic4']))

    result = strip_tags(render_template_tag('sitetree', 'sitetree_tree from "dynamic4"', mock_template_context()))

    assert 'dynamic4_1' in result

    settings.DEBUG = True
    with pytest.warns(UserWarning):
        compose_dynamic_tree('nonexistent')

