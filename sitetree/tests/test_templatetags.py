import pytest
from django.template.base import TemplateSyntaxError
from django.utils.translation import activate, deactivate_all

from sitetree.exceptions import SiteTreeError
from sitetree.settings import ALIAS_THIS_ANCESTOR_CHILDREN, ALIAS_THIS_CHILDREN, ALIAS_THIS_PARENT_SIBLINGS, \
    ALIAS_THIS_SIBLINGS, ALIAS_TRUNK


def test_items_hook(template_render_tag, template_context, common_tree):

    from sitetree.toolbox import register_items_hook

    with pytest.raises(SiteTreeError):
        register_items_hook(lambda: [])

    def my_processor(tree_items, tree_sender):
        for item in tree_items:
            item.hint = f'hooked_hint_{item.title}'
        return tree_items

    register_items_hook(my_processor)
    result = template_render_tag('sitetree', 'sitetree_tree from "mytree"', template_context())

    assert 'hooked_hint_Darwin' in result
    assert 'hooked_hint_Australia' in result
    assert 'hooked_hint_China' in result

    # hook with context

    def my_processor(tree_items, tree_sender, context):
        prefix = context.__class__.__name__

        for item in tree_items:
            item.hint = prefix + item.title

        return tree_items

    register_items_hook(my_processor)
    result = template_render_tag('sitetree', 'sitetree_tree from "mytree"', template_context())

    assert 'ContextDarwin' in result
    assert 'ContextAustralia' in result
    assert 'ContextChina' in result

    register_items_hook(None)  # Reset.


def test_i18n(build_tree, template_render_tag, template_context):

    from sitetree.toolbox import register_i18n_trees

    build_tree(
        {'alias': 'i18tree'},
        [{'title': 'My title', 'url': '/url_default/'}],
    )
    build_tree(
        {'alias': 'i18tree_ru'},
        [{'title': 'Заголовок', 'url': '/url_ru/'}],
    )
    build_tree(
        {'alias': 'i18tree_pt-br'},
        [{'title': 'Meu Título', 'url': '/url_pt-br/'}],
    )
    build_tree(
        {'alias': 'i18tree_zh-hans'},
        [{'title': '我蒂特', 'url': '/url_zh-hans/'}],
    )
    register_i18n_trees(['i18tree'])

    activate('en')
    result = template_render_tag('sitetree', 'sitetree_tree from "i18tree"', template_context())

    assert '/url_default/' in result
    assert 'My title' in result

    activate('ru')
    result = template_render_tag('sitetree', 'sitetree_tree from "i18tree"', template_context())

    assert '/url_ru/' in result
    assert 'Заголовок' in result

    activate('pt-br')
    result = template_render_tag('sitetree', 'sitetree_tree from "i18tree"', template_context())

    assert '/url_pt-br/' in result
    assert 'Meu Título' in result

    activate('zh-hans')
    result = template_render_tag('sitetree', 'sitetree_tree from "i18tree"', template_context())

    assert '/url_zh-hans/' in result
    assert '我蒂特' in result

    deactivate_all()


def test_restricted(user_create, template_render_tag, template_context, common_tree):
    context = template_context()
    result = template_render_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert '"/contacts/australia/darwin/"' in result
    assert '"/contacts/australia/alice/"' not in result

    context = template_context(user=user_create())
    result = template_render_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert '"/contacts/australia/darwin/"' not in result
    assert '"/contacts/australia/alice/"' in result


def test_permissions(user_create, build_tree, template_render_tag, template_context):

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

    admin_user = user_create(superuser=True)
    context = template_context(user=admin_user)
    result = template_render_tag('sitetree', 'sitetree_tree from "restricted_tree"', context)

    assert '"/contacts/australia/broome/"' in result
    assert '"/contacts/australia/karratha/"' in result
    assert '"/contacts/australia/minjilang/"' not in result

    admin_user._perm_cache.remove('sitetree.add_tree')

    context = template_context(user=admin_user)
    result = template_render_tag('sitetree', 'sitetree_tree from "restricted_tree"', context)

    assert '"/contacts/australia/broome/"' in result
    assert '"/contacts/australia/karratha/"' not in result
    assert '"/contacts/australia/minjilang/"' not in result


def test_title_vars(template_render_tag, template_context, common_tree):
    context = template_context({'subtitle': 'title_from_var'})
    result = template_render_tag('sitetree', 'sitetree_tree from "mytree"', context)
    assert 'Public title_from_var' in result


def test_urlpattern_resolve(monkeypatch, template_render_tag, template_context, common_tree):

    monkeypatch.setattr('sitetree.sitetreeapp.UNRESOLVED_ITEM_MARKER', 'UNKNOWN')

    context = template_context()
    result = template_render_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert '"/contacts/australia/australia_var/"' in result
    assert 'href="UNKNOWN" >China' in result

    context = template_context({'australia_var': 33})
    result = template_render_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert 'href="/contacts/australia/33/"' in result

    context = template_context({'australia_var': 'пробапера'})  # non-ascii
    result = template_render_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert '"/contacts/australia/%D0%BF%D1%80%D0%BE%D0%B1%D0%B0%D0%BF%D0%B5%D1%80%D0%B0/"' in result


def test_sitetree_tree(template_render_tag, template_context, common_tree):

    context = template_context()

    with pytest.raises(TemplateSyntaxError):
        template_render_tag('sitetree', 'sitetree_tree "mytree"', context)

    assert template_render_tag('sitetree', 'sitetree_tree from "notree"', context) == '\n'

    result = template_render_tag('sitetree', 'sitetree_tree from "mytree"', context)

    assert '"/articles/cats/ugly/"' in result
    assert '"/contacts/russia/postal/"' not in result  # insitetree False
    assert '"/users/ordinary/"' in result
    assert '"/users/hidden/"' not in result


def test_sitetree_children(template_render_tag, template_context, common_tree):

    context = template_context({
        'parent_item': common_tree['/users/']
    })

    with pytest.raises(TemplateSyntaxError):
        template_render_tag('sitetree', 'sitetree_children', context)

    result = template_render_tag(
        'sitetree', 'sitetree_children of parent_item for sitetree template "sitetree/tree.html"', context)

    assert '"/users/moderators/"' in result
    assert '"/users/"' not in result
    assert '"/users/hidden/"' not in result


def test_sitetree_breadcrumbs(template_render_tag, template_context, common_tree):

    result = template_render_tag('sitetree', 'sitetree_breadcrumbs from "notree"', template_context())  # non-existing tree

    assert result.strip() == '<ul>\n\t\n</ul>'

    with pytest.raises(TemplateSyntaxError):
        template_render_tag('sitetree', 'sitetree_breadcrumbs')

    result = template_render_tag('sitetree', 'sitetree_breadcrumbs from "mytree"', template_context())

    assert result.strip() == '<ul>\n\t\n</ul>'

    context = template_context(request='/contacts/russia/web/private/')
    result = template_render_tag('sitetree', 'sitetree_breadcrumbs from "mytree"', context)

    assert '"/contacts/russia/web/"' in result
    assert '"/contacts/russia/"' in result
    assert '"/contacts/"' not in result  # inbreadcrumbs False
    assert '"/home/"' in result


def check_page_attr_tag(realm, value, settings, monkeypatch, template_render_tag, template_context):

    with pytest.raises(TemplateSyntaxError):  # Invalid tag arguments.
        template_render_tag('sitetree', f'sitetree_page_{realm}')

    context = template_context(request='/contacts/russia/')
    result = template_render_tag('sitetree', f'sitetree_page_{realm} from "mytree"', context)

    assert result == value

    result = template_render_tag('sitetree', f'sitetree_page_{realm} from "mytree" as somevar', context)

    assert result == ''
    assert context.get('somevar') == value

    settings.DEBUG = True

    with pytest.raises(SiteTreeError) as e:
        template_render_tag('sitetree', f'sitetree_page_{realm} from "mytree"')

    assert 'django.core.context_processors.request' in f'{e.value}'

    context = template_context(request='/unknown_url/')

    with pytest.raises(SiteTreeError) as e:
        template_render_tag('sitetree', f'sitetree_page_{realm} from "mytree"', context)

    assert 'Unable to resolve current sitetree item' in f'{e.value}'

    monkeypatch.setattr('sitetree.sitetreeapp.RAISE_ITEMS_ERRORS_ON_DEBUG', False)
    result = template_render_tag('sitetree', f'sitetree_page_{realm} from "mytree"', context)

    assert result == ''


def test_sitetree_page_title(settings, monkeypatch, template_render_tag, template_context, common_tree):
    check_page_attr_tag('title', 'Russia', settings, monkeypatch, template_render_tag, template_context)


def test_sitetree_page_hint(settings, monkeypatch, template_render_tag, template_context, common_tree):
    check_page_attr_tag('hint', 'The place', settings, monkeypatch, template_render_tag, template_context)


def test_sitetree_page_description(settings, monkeypatch, template_render_tag, template_context, common_tree):
    check_page_attr_tag(
        'description', 'Russian Federation', settings, monkeypatch, template_render_tag, template_context)


def test_sitetree_url(template_render_tag, template_context, common_tree):

    with pytest.raises(TemplateSyntaxError):
        template_render_tag('sitetree', 'sitetree_url')

    target_url = '/contacts/russia/'

    tree_item = common_tree[target_url]
    context = template_context({'item_var': tree_item})

    result = template_render_tag('sitetree', 'sitetree_url for item_var', context)

    assert result == target_url

    result = template_render_tag('sitetree', 'sitetree_url for item_var as somevar', context)
    assert result == ''
    assert context.get('somevar') == target_url


def test_sitetree_menu(template_render_tag, template_context, common_tree):

    result = template_render_tag(
        'sitetree', f'sitetree_menu from "notree" include "{ALIAS_TRUNK}"', template_context())  # non-existing tree

    assert result.strip() == '<ul>\n\t\n</ul>'

    with pytest.raises(TemplateSyntaxError):
        template_render_tag('sitetree', 'sitetree_menu')

    item_ruweb = common_tree['/contacts/russia/web/']

    context = template_context(request='/')
    result = template_render_tag('sitetree', f'sitetree_menu from "mytree" include "{item_ruweb.alias}"', context)

    assert '"/contacts/russia/web/"' not in result
    assert '"/contacts/russia/web/public/"' in result
    assert '"/contacts/russia/web/private/"' in result

    result = template_render_tag('sitetree', f'sitetree_menu from "mytree" include "{item_ruweb.id}"', context)

    assert '"/contacts/russia/web/"' not in result
    assert '"/contacts/russia/web/public/"' in result
    assert '"/contacts/russia/web/private/"' in result

    context = template_context(request='/contacts/russia/web/')
    result = template_render_tag('sitetree', f'sitetree_menu from "mytree" include "{ALIAS_TRUNK}"', context)

    assert '"/users/moderators/"' in result
    assert '"/articles/cats/ugly/"' in result
    assert '"/home/"' in result
    assert '"/users/ordinary/"' in result
    assert '"/users/hidden/"' not in result

    assert 'class="current_item current_branch">Web' in result
    assert 'class="current_branch">Contacts' in result
    assert 'class="current_branch">Home' in result

    context = template_context(request='/articles/')
    result = template_render_tag('sitetree', f'sitetree_menu from "mytree" include "{ALIAS_THIS_CHILDREN}"', context)

    assert '"/articles/"' not in result
    assert '"/articles/cats/"' in result
    assert '"/articles/cats/ugly/"' in result
    assert '"/articles/mice/"' not in result  # inmenu False

    context = template_context(request='/articles/cats/bad/')
    result = template_render_tag(
        'sitetree', f'sitetree_menu from "mytree" include "{ALIAS_THIS_SIBLINGS}"', context)

    assert '"/articles/cats/"' not in result
    assert '"/articles/cats/good/"' in result
    assert '"/articles/cats/bad/"' in result
    assert '"/articles/cats/ugly/"' in result

    context = template_context(request='/contacts/russia/web/public/')
    result = template_render_tag(
        'sitetree', f'sitetree_menu from "mytree" include "{ALIAS_THIS_PARENT_SIBLINGS}"', context)

    assert '"/contacts/russia/"' not in result
    assert '"/contacts/russia/web/"' in result
    assert '"/contacts/russia/web/public/"' in result
    assert '"/contacts/russia/postal/"' in result

    context = template_context(request='/contacts/russia/web/public/')
    result = template_render_tag(
        'sitetree', f'sitetree_menu from "mytree" include "{ALIAS_THIS_ANCESTOR_CHILDREN}"', context)

    assert '"/home/"' not in result
    assert '"/contacts/russia/web/public/"' in result
