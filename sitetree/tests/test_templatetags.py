#! -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import pytest
from django.template.base import TemplateSyntaxError
from django.utils.translation import activate, deactivate_all

from sitetree.exceptions import SiteTreeError
from sitetree.settings import ALIAS_THIS_ANCESTOR_CHILDREN, ALIAS_THIS_CHILDREN, ALIAS_THIS_PARENT_SIBLINGS, \
    ALIAS_THIS_SIBLINGS, ALIAS_TRUNK


@pytest.mark.django_db
def test_items_hook(render_template_tag, mock_template_context, common_tree):

    from sitetree.toolbox import register_items_hook

    def my_processor(tree_items, tree_sender):
        for item in tree_items:
            item.hint = 'hooked_hint_%s' % item.title
        return tree_items

    register_items_hook(my_processor)
    result = render_template_tag('sitetree', 'sitetree_tree from "mytree"', mock_template_context())

    assert 'hooked_hint_Darwin' in result
    assert 'hooked_hint_Australia' in result
    assert 'hooked_hint_China' in result

    register_items_hook(None)  # Reset.


@pytest.mark.django_db
def test_i18n(build_tree, render_template_tag, mock_template_context):

    from sitetree.toolbox import register_i18n_trees

    build_tree(
        {'alias': 'i18tree'},
        [{'title': 'My title', 'url': '/url_default/'}],
    )
    build_tree(
        {'alias': 'i18tree_ru'},
        [{'title': 'Заголовок', 'url': '/url_ru/'}],
    )
    register_i18n_trees(['i18tree'])

    activate('en')
    result = render_template_tag('sitetree', 'sitetree_tree from "i18tree"', mock_template_context())

    assert '/url_default/' in result
    assert 'My title' in result

    activate('ru')
    result = render_template_tag('sitetree', 'sitetree_tree from "i18tree"', mock_template_context())

    assert '/url_ru/' in result
    assert 'Заголовок' in result

    deactivate_all()


@pytest.mark.django_db
def test_restricted(render_template_tag, mock_template_context, common_tree):
    context = mock_template_context()
    result = render_template_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert '"/contacts/australia/darwin/"' in result
    assert '"/contacts/australia/alice/"' not in result

    context = mock_template_context(user_data='some')
    result = render_template_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert '"/contacts/australia/darwin/"' not in result
    assert '"/contacts/australia/alice/"' in result


@pytest.mark.django_db
def test_permissions(admin_user, build_tree, render_template_tag, mock_template_context):

    from sitetree.models import TreeItem

    build_tree(
        {'alias': 'restricted_tree'},
        [
            {'title': 'Minjilang', 'access_restricted': True, 'url': '/contacts/australia/minjilang/'},
            {'title': 'Broome', 'access_restricted': True, 'access_perm_type': TreeItem.PERM_TYPE_ANY,
             'access_permissions': ['add_group', 'add_tree'], 'url': '/contacts/australia/broome/'},
            {'title': 'Karratha', 'access_restricted': True, 'access_perm_type': TreeItem.PERM_TYPE_ALL,
             'access_permissions': ['add_group', 'add_tree'], 'url': '/contacts/australia/karratha/'},
        ],
    )

    context = mock_template_context(user_data=admin_user)
    result = render_template_tag('sitetree', 'sitetree_tree from "restricted_tree"', context)

    assert '"/contacts/australia/broome/"' in result
    assert '"/contacts/australia/karratha/"' in result
    assert '"/contacts/australia/minjilang/"' not in result

    admin_user._perm_cache.remove('sitetree.add_tree')

    context = mock_template_context(user_data=admin_user)
    result = render_template_tag('sitetree', 'sitetree_tree from "restricted_tree"', context)

    assert '"/contacts/australia/broome/"' in result
    assert '"/contacts/australia/karratha/"' not in result
    assert '"/contacts/australia/minjilang/"' not in result


@pytest.mark.django_db
def test_title_vars(render_template_tag, mock_template_context, common_tree):
    context = mock_template_context({'subtitle': 'title_from_var'})
    result = render_template_tag('sitetree', 'sitetree_tree from "mytree"', context)
    assert 'Public title_from_var' in result


@pytest.mark.django_db
def test_urlpattern_resolve(monkeypatch, render_template_tag, mock_template_context, common_tree):

    monkeypatch.setattr('sitetree.sitetreeapp.UNRESOLVED_ITEM_MARKER', 'UNKNOWN')

    context = mock_template_context()
    result = render_template_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert '"/contacts/australia/australia_var/"' in result
    assert 'href="UNKNOWN" >China' in result

    context = mock_template_context({'australia_var': 33})
    result = render_template_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert 'href="/contacts/australia/33/"' in result

    context = mock_template_context({'australia_var': 'пробапера'})  # non-ascii
    result = render_template_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert '"/contacts/australia/australia_var/"' in result


@pytest.mark.django_db
def test_sitetree_tree(render_template_tag, mock_template_context, common_tree):

    context = mock_template_context()

    with pytest.raises(TemplateSyntaxError):
        render_template_tag('sitetree', 'sitetree_tree "mytree"', context)

    assert render_template_tag('sitetree', 'sitetree_tree from "notree"', context) == '\n'

    result = render_template_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert '"/articles/cats/ugly/"' in result
    assert '"/contacts/russia/postal/"' not in result  # insitetree False
    assert '"/users/ordinary/"' in result
    assert '"/users/hidden/"' not in result


@pytest.mark.django_db
def test_sitetree_children(render_template_tag, mock_template_context, common_tree):

    context = mock_template_context({
        'parent_item': common_tree['/users/']
    })

    with pytest.raises(TemplateSyntaxError):
        render_template_tag('sitetree', 'sitetree_children', context)

    result = render_template_tag(
        'sitetree', 'sitetree_children of parent_item for sitetree template "sitetree/tree.html"', context)

    assert '"/users/moderators/"' in result
    assert '"/users/"' not in result
    assert '"/users/hidden/"' not in result


@pytest.mark.django_db
def test_sitetree_breadcrumbs(render_template_tag, mock_template_context, common_tree):

    result = render_template_tag('sitetree', 'sitetree_breadcrumbs from "notree"', mock_template_context())  # non-existing tree

    assert result.strip() == '<ul>\n\t\n</ul>'

    with pytest.raises(TemplateSyntaxError):
        render_template_tag('sitetree', 'sitetree_breadcrumbs')

    result = render_template_tag('sitetree', 'sitetree_breadcrumbs from "mytree"', mock_template_context())

    assert result.strip() == '<ul>\n\t\n</ul>'

    context = mock_template_context(request_path='/contacts/russia/web/private/')
    result = render_template_tag('sitetree', 'sitetree_breadcrumbs from "mytree"', context)

    assert '"/contacts/russia/web/"' in result
    assert '"/contacts/russia/"' in result
    assert '"/contacts/"' not in result  # inbreadcrumbs False
    assert '"/home/"' in result


def check_page_attr_tag(realm, value, settings, monkeypatch, render_template_tag, mock_template_context):

    with pytest.raises(TemplateSyntaxError):  # Invalid tag arguments.
        render_template_tag('sitetree', 'sitetree_page_%s' % realm)

    context = mock_template_context(request_path='/contacts/russia/')
    result = render_template_tag('sitetree', 'sitetree_page_%s from "mytree"' % realm, context)

    assert result == value

    result = render_template_tag('sitetree', 'sitetree_page_%s from "mytree" as somevar' % realm, context)

    assert result == ''
    assert context.get('somevar') == value

    settings.DEBUG = True

    with pytest.raises(SiteTreeError) as e:
        render_template_tag('sitetree', 'sitetree_page_%s from "mytree"' % realm)

    assert 'django.core.context_processors.request' in '%s' % e.value

    context = mock_template_context(request_path='/unknown_url/')

    with pytest.raises(SiteTreeError) as e:
        render_template_tag('sitetree', 'sitetree_page_%s from "mytree"' % realm, context)

    assert 'Unable to resolve current sitetree item' in '%s' % e.value

    monkeypatch.setattr('sitetree.sitetreeapp.RAISE_ITEMS_ERRORS_ON_DEBUG', False)
    result = render_template_tag('sitetree', 'sitetree_page_%s from "mytree"' % realm, context)

    assert result == ''


@pytest.mark.django_db
def test_sitetree_page_title(settings, monkeypatch, render_template_tag, mock_template_context, common_tree):
    check_page_attr_tag('title', 'Russia', settings, monkeypatch, render_template_tag, mock_template_context)


@pytest.mark.django_db
def test_sitetree_page_hint(settings, monkeypatch, render_template_tag, mock_template_context, common_tree):
    check_page_attr_tag('hint', 'The place', settings, monkeypatch, render_template_tag, mock_template_context)


@pytest.mark.django_db
def test_sitetree_page_description(settings, monkeypatch, render_template_tag, mock_template_context, common_tree):
    check_page_attr_tag(
        'description', 'Russian Federation', settings, monkeypatch, render_template_tag, mock_template_context)


@pytest.mark.django_db
def test_sitetree_url(render_template_tag, mock_template_context, common_tree):

    with pytest.raises(TemplateSyntaxError):
        render_template_tag('sitetree', 'sitetree_url')

    target_url = '/contacts/russia/'

    tree_item = common_tree[target_url]
    context = mock_template_context({'item_var': tree_item})

    result = render_template_tag('sitetree', 'sitetree_url for item_var', context)

    assert result == target_url

    result = render_template_tag('sitetree', 'sitetree_url for item_var as somevar', context)
    assert result == ''
    assert context.get('somevar') == target_url


@pytest.mark.django_db
def test_sitetree_menu(render_template_tag, mock_template_context, common_tree):

    result = render_template_tag(
        'sitetree', 'sitetree_menu from "notree" include "%s"' % ALIAS_TRUNK, mock_template_context())  # non-existing tree

    assert result.strip() == '<ul>\n\t\n</ul>'

    with pytest.raises(TemplateSyntaxError):
        render_template_tag('sitetree', 'sitetree_menu')

    item_ruweb = common_tree['/contacts/russia/web/']

    context = mock_template_context(request_path='/')
    result = render_template_tag('sitetree', 'sitetree_menu from "mytree" include "%s"' % item_ruweb.alias, context)

    assert '"/contacts/russia/web/"' not in result
    assert '"/contacts/russia/web/public/"' in result
    assert '"/contacts/russia/web/private/"' in result

    result = render_template_tag('sitetree', 'sitetree_menu from "mytree" include "%s"' % item_ruweb.id, context)

    assert '"/contacts/russia/web/"' not in result
    assert '"/contacts/russia/web/public/"' in result
    assert '"/contacts/russia/web/private/"' in result

    context = mock_template_context(request_path='/contacts/russia/web/')
    result = render_template_tag('sitetree', 'sitetree_menu from "mytree" include "%s"' % ALIAS_TRUNK, context)

    assert '"/users/moderators/"' in result
    assert '"/articles/cats/ugly/"' in result
    assert '"/home/"' in result
    assert '"/users/ordinary/"' in result
    assert '"/users/hidden/"' not in result

    assert 'class="current_item current_branch">Web' in result
    assert 'class="current_branch">Contacts' in result
    assert 'class="current_branch">Home' in result

    context = mock_template_context(request_path='/articles/')
    result = render_template_tag('sitetree', 'sitetree_menu from "mytree" include "%s"' % ALIAS_THIS_CHILDREN, context)

    assert '"/articles/"' not in result
    assert '"/articles/cats/"' in result
    assert '"/articles/cats/ugly/"' in result
    assert '"/articles/mice/"' not in result  # inmenu False

    context = mock_template_context(request_path='/articles/cats/bad/')
    result = render_template_tag(
        'sitetree', 'sitetree_menu from "mytree" include "%s"' % ALIAS_THIS_SIBLINGS, context)

    assert '"/articles/cats/"' not in result
    assert '"/articles/cats/good/"' in result
    assert '"/articles/cats/bad/"' in result
    assert '"/articles/cats/ugly/"' in result

    context = mock_template_context(request_path='/contacts/russia/web/public/')
    result = render_template_tag(
        'sitetree', 'sitetree_menu from "mytree" include "%s"' % ALIAS_THIS_PARENT_SIBLINGS, context)

    assert '"/contacts/russia/"' not in result
    assert '"/contacts/russia/web/"' in result
    assert '"/contacts/russia/web/public/"' in result
    assert '"/contacts/russia/postal/"' in result

    context = mock_template_context(request_path='/contacts/russia/web/public/')
    result = render_template_tag(
        'sitetree', 'sitetree_menu from "mytree" include "%s"' % ALIAS_THIS_ANCESTOR_CHILDREN, context)

    assert '"/home/"' not in result
    assert '"/contacts/russia/web/public/"' in result
