#! -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from sitetree.settings import ALIAS_TRUNK

from .common import strip_tags


@pytest.mark.django_db
def test_stress(render_template_tag, mock_template_context, common_tree):

    context = mock_template_context(request_path='/contacts/russia/web/private/')

    title = render_template_tag('sitetree', 'sitetree_page_title from "mytree"', context)
    hint = render_template_tag('sitetree', 'sitetree_page_hint from "mytree"', context)
    description = render_template_tag('sitetree', 'sitetree_page_description from "mytree"', context)
    tree = strip_tags(render_template_tag('sitetree', 'sitetree_tree from "mytree"', context))
    breadcrumbs = strip_tags(render_template_tag('sitetree', 'sitetree_breadcrumbs from "mytree"', context))
    menu = strip_tags(
        render_template_tag('sitetree', 'sitetree_menu from "mytree" include "%s"' % ALIAS_TRUNK, context))

    assert title == 'Private'
    assert hint == 'Private Area Hint'
    assert description == 'Private Area Description'
    assert breadcrumbs == 'Home|&gt;|Russia|&gt;|Web|&gt;|Private'
    assert menu == 'Home|Users|Moderators|Ordinary|Articles|About cats|Good|Bad|Ugly|About dogs|Contacts|Russia|Web|' \
                   'Public|Private|Postal|Australia|Darwin|China'
    assert tree == 'Home|Users|Moderators|Ordinary|Articles|About cats|Good|Bad|Ugly|About dogs|About mice|Contacts|' \
                   'Russia|Web|Public|Private|Australia|Darwin|China'


def test_lazy_title(mock_template_context):

    from sitetree.sitetreeapp import LazyTitle, get_sitetree

    assert LazyTitle('one') == 'one'

    title = LazyTitle('here{% no_way %}there')

    get_sitetree().current_page_context = mock_template_context()

    assert title == 'herethere'
