#! -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from sitetree.settings import ALIAS_TRUNK


def test_stress(template_render_tag, template_context, template_strip_tags, build_tree, common_tree):

    build_tree(
        {'alias': 'othertree'},
        [{'title': 'Root', 'url': '/', 'children': [
            {'title': 'Other title', 'url': '/contacts/russia/web/private/'},
            {'title': 'Title_{{ myvar }}', 'url': '/some/'}
        ]}],
    )

    context = template_context(context_dict={'myvar': 'myval'}, request='/contacts/russia/web/private/')

    title = template_render_tag('sitetree', 'sitetree_page_title from "mytree"', context)
    title_other = template_render_tag('sitetree', 'sitetree_page_title from "othertree"', context)

    hint = template_render_tag('sitetree', 'sitetree_page_hint from "mytree"', context)
    description = template_render_tag('sitetree', 'sitetree_page_description from "mytree"', context)
    tree = template_strip_tags(template_render_tag('sitetree', 'sitetree_tree from "mytree"', context))
    breadcrumbs = template_strip_tags(template_render_tag('sitetree', 'sitetree_breadcrumbs from "mytree"', context))

    menu = template_render_tag('sitetree', 'sitetree_menu from "mytree" include "%s"' % ALIAS_TRUNK, context)
    menu_other = template_render_tag('sitetree', 'sitetree_menu from "othertree" include "%s"' % ALIAS_TRUNK, context)

    assert title == 'Private'
    assert title_other == 'Other title'
    assert hint == 'Private Area Hint'
    assert description == 'Private Area Description'
    assert breadcrumbs == 'Home|&gt;|Russia|&gt;|Web|&gt;|Private'

    assert template_strip_tags(menu) == 'Home|Users|Moderators|Ordinary|Articles|About cats|Good|Bad|Ugly|About dogs|' \
                               'Contacts|Russia|Web|Public|Private|Postal|Australia|Darwin|China'
    assert 'current_item current_branch">Private' in menu

    assert template_strip_tags(menu_other) == 'Root|Other title|Title_myval'
    assert 'current_item current_branch">Other title' in menu_other

    assert tree == 'Home|Users|Moderators|Ordinary|Articles|About cats|Good|Bad|Ugly|About dogs|About mice|Contacts|' \
                   'Russia|Web|Public|Private|Australia|Darwin|China'


def test_lazy_title(template_context):

    from sitetree.sitetreeapp import LazyTitle, get_sitetree

    assert LazyTitle('one') == 'one'

    title = LazyTitle('here{% no_way %}there')

    get_sitetree().current_page_context = template_context()

    assert title == 'herethere'


def test_customized_tree_handler(template_context):

    from sitetree.sitetreeapp import get_sitetree

    assert get_sitetree().customized  # see MySiteTree
