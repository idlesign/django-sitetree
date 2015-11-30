import sys
from json import loads

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
    
try:
    from unittest import mock
except ImportError:
    import mock

from django.conf import settings
from django.utils.translation import activate
from django.template.base import Template, TemplateSyntaxError
from django.template.context import Context
from django.test.utils import override_settings
from django.test import TestCase
from django.contrib.auth.models import Permission
from django.contrib.admin.sites import site
from django.core.management import call_command
from django.core.exceptions import ImproperlyConfigured
from django.conf.urls import patterns, url

from sitetree.models import Tree, TreeItem
from sitetree.forms import TreeItemForm
from sitetree.admin import TreeAdmin, TreeItemAdmin, redirects_handler
from sitetree.utils import (
    tree, item, get_app_n_model, import_app_sitetree_module, import_project_sitetree_modules, get_model_class
)
from sitetree.sitetreeapp import (
    SiteTree, SiteTreeError, register_items_hook, register_i18n_trees, register_dynamic_trees, compose_dynamic_tree,
    get_dynamic_trees
)


urlpatterns = patterns(
    '',
    url(r'articles/', lambda r: None, name='articles_list'),
    url(r'articles/(\d+)/', lambda r: None, name='articles_detailed'),
    url(r'articles/(?P<id>\d+)_(?P<slug>[\w-]+)/', lambda r: None, name='url'),
)


class MockRequest(object):

    def __init__(self, path=None, user_authorized=None, meta=None):
        if path is None:
            path = '/'

        if user_authorized is None:
            user_authorized = True

        self.path = path
        self.user = MockUser(user_authorized)
        self.META = meta


class MockUser(object):

    def __init__(self, authorized, permissions=None):
        self.authorized = authorized
        self.permissions = permissions or ['auth.add_group', 'perm2']

    def is_authenticated(self):
        return self.authorized

    def get_all_permissions(self):
        return self.permissions


def get_mock_context(app=None, path=None, user_authorized=False, tree_item=None, put_var=None):
    ctx = Context(
        {
            'request': MockRequest(path, user_authorized),
            't2_root2_title': 'my_real_title', 'art_id': 10, 'tree_item': tree_item,
            'somevar_str': 'articles_list', 'somevar_list': ['a', 'b'], 'put_var': put_var
        },
        current_app=app
    )
    ctx.template = mock.MagicMock()
    ctx.template.engine.string_if_invalid = ''
    return ctx


def render_string(string, context=None, context_put_var=None, context_path=None):
    return Template(string).render(Context(context or get_mock_context(path=context_path, put_var=context_put_var)))


def get_permission_and_name():
    perm = Permission.objects.all()[0]
    perm_name = '%s.%s' % (perm.content_type.app_label, perm.codename)
    return perm, perm_name


class SitetreeTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.init_trees()

    @classmethod
    def init_trees(cls):
        cls.sitetree = SiteTree()

        ###########################################################

        t1 = Tree(alias='tree1')
        t1.save()
        cls.t1 = t1

        t1_root = TreeItem(title='root', tree=t1, url='/')
        t1_root.save()
        cls.tree_ttags_root = t1_root

        t1_root_child1 = TreeItem(title='child1', tree=t1, parent=t1_root, url='/about/')
        t1_root_child1.save()
        cls.tree_ttags_root_child1 = t1_root_child1

        t1_root_child2 = TreeItem(title='child2', tree=t1, parent=t1_root, url='articles_list', urlaspattern=True,
                                  description='items_descr')
        t1_root_child2.save()
        cls.t1_root_child2 = t1_root_child2

        t1_root_child2_sub1 = TreeItem(title='subchild1', tree=t1, parent=t1_root_child2,
                                       url='articles_detailed art_id', urlaspattern=True)
        t1_root_child2_sub1.save()
        cls.t1_root_child2_sub1 = t1_root_child2_sub1

        t1_root_child2_sub2 = TreeItem(title='subchild2', tree=t1, parent=t1_root_child2, url='/not_articles/10/')
        t1_root_child2_sub2.save()
        cls.t1_root_child2_sub2 = t1_root_child2_sub2

        t1_root_child3 = TreeItem(title='child_with_var_str', tree=t1, parent=t1_root, url='somevar_str',
                                  urlaspattern=True)
        t1_root_child3.save()
        cls.t1_root_child3 = t1_root_child3

        t1_root_child4 = TreeItem(title='child_with_var_list', tree=t1, parent=t1_root, url='somevar_list',
                                  urlaspattern=True)
        t1_root_child4.save()

        t2 = Tree(alias='tree2')
        t2.save()
        cls.t2 = t2

        t2_root1 = TreeItem(title='{{ t2_root1_title }}', tree=t2, url='/')
        t2_root1.save()
        cls.t2_root1 = t2_root1

        t2_root2 = TreeItem(title='put {{ t2_root2_title }} inside', tree=t2, url='/sub/')
        t2_root2.save()
        cls.t2_root2 = t2_root2

        t2_root3 = TreeItem(title='for logged in only', tree=t2, url='/some/', access_loggedin=True)
        t2_root3.save()
        cls.t2_root3 = t2_root3

        t2_root4 = TreeItem(title='url quoting', tree=t2, url='url 2 put_var', urlaspattern=True)
        t2_root4.save()
        cls.t2_root4 = t2_root4

        t2_root5 = TreeItem(title='url quoting 1.5 style', tree=t2, url="'url' 2 put_var", urlaspattern=True)
        t2_root5.save()
        cls.t2_root5 = t2_root5

        t2_root6 = TreeItem(title='url quoting 1.5 style', tree=t2, url='"url" 2 put_var', urlaspattern=True)
        t2_root6.save()
        cls.t2_root6 = t2_root6

        t2_root7 = TreeItem(title='for guests only', tree=t2, url='/some_other/', access_guest=True)
        t2_root7.save()
        cls.t2_root7 = t2_root7

        ###########################################################

        t3 = Tree(alias='tree3')
        t3.save()
        cls.t3 = t3

        t3_en_root = TreeItem(title='root', tree=t3, url='/', hidden=True)
        t3_en_root.save()
        cls.t3_root = t3_en_root

        t3_root_child1 = TreeItem(title='child1', tree=t3, parent=t3_en_root, url='/0/', access_loggedin=True)
        t3_root_child1.save()
        cls.t3_root_child1 = t3_root_child1

        t3_root_child2 = TreeItem(title='child2', tree=t3, parent=t3_en_root, url='/1/', inmenu=True, hidden=True)
        t3_root_child2.save()
        cls.t3_root_child2 = t3_root_child2

        t3_root_child3 = TreeItem(title='child3', tree=t3, parent=t3_en_root, url='/the_same_url/', inmenu=False)
        t3_root_child3.save()
        cls.t3_root_child3 = t3_root_child3

        t3_root_child4 = TreeItem(title='child4', tree=t3, parent=t3_en_root, url='/3/', hidden=True)
        t3_root_child4.save()
        cls.t3_root_child4 = t3_root_child4

        t3_root_child5 = TreeItem(title='child5', tree=t3, parent=t3_en_root, url='/4/', inmenu=True, hidden=True)
        t3_root_child5.save()
        cls.t3_root_child5 = t3_root_child5

        t3_en = Tree(alias='tree3_en', title='tree3en_title')
        t3_en.save()
        cls.t3_en = t3_en

        t3_en_root = TreeItem(title='root_en', tree=t3_en, url='/')
        t3_en_root.save()
        cls.t3_en_root = t3_en_root

        t3_en_root_child1 = TreeItem(title='child1_en', tree=t3_en, parent=t3_en_root, url='/0_en/')
        t3_en_root_child1.save()

        t3_en_root_child2 = TreeItem(title='child2_en', tree=t3_en, parent=t3_en_root, url='/the_same_url/')
        t3_en_root_child2.save()

        ###########################################################

        tree_main = Tree(alias='main')
        tree_main.save()
        cls.tree_main = tree_main

        tree_main_root = TreeItem(title='root', tree=tree_main, url='/', alias='for_dynamic')
        tree_main_root.save()
        cls.tree_main_root = tree_main_root

    @classmethod
    def tearDownClass(cls):
        Tree.objects.all().delete()
        TreeItem.objects.all().delete()


class TreeModelTest(SitetreeTest):

    def test_create_rename_delete(self):
        tree = Tree(alias='mytree')
        tree.save()
        self.assertIsNotNone(tree.id)
        self.assertEqual(tree.alias, 'mytree')
        tree.alias = 'not_mytree'
        tree.save(force_update=True)
        self.assertEqual(tree.alias, 'not_mytree')
        tree.delete()
        self.assertIsNone(tree.id)

    def test_unique_aliases(self):
        tree1 = Tree(alias='mytree')
        tree1.save()
        tree2 = Tree(alias='mytree')
        self.assertRaises(Exception, tree2.save)


class TreeItemModelTest(SitetreeTest):

    def test_url_resolve(self):
        self.sitetree.menu('tree1', 'trunk', get_mock_context(path='/', put_var='abrakadabra'))

        url = self.sitetree.url(self.t2_root4, get_mock_context(path='/articles/2_slugged/'))
        self.assertTrue(url.find('abrakadabra') > -1)

        self.sitetree.menu('tree1', 'trunk', get_mock_context(path='/', put_var='booo'))
        url = self.sitetree.url(self.t2_root4, get_mock_context(path='/articles/2_slugged-mugged/'))
        self.assertTrue(url.find('booo') > -1)

        self.sitetree.menu('tree1', 'trunk', get_mock_context(path='/', put_var='rolling'))
        url = self.sitetree.url(self.t2_root5, get_mock_context(path='/articles/2_quoted/'))
        self.assertTrue(url.find('rolling') > -1)

        self.sitetree.menu('tree1', 'trunk', get_mock_context(path='/', put_var='spoon'))
        url = self.sitetree.url(self.t2_root6, get_mock_context(path='/articles/2_quoted/'))
        self.assertTrue(url.find('spoon') > -1)

    def test_no_tree(self):
        ti = TreeItem(title='notree_item')
        self.assertRaises(Exception, ti.save)

    def test_create_rename_delete(self):
        ti1 = TreeItem(title='new_root_item', tree=self.t1)
        ti1.save()
        self.assertIsNotNone(ti1.id)
        self.assertEqual(ti1.title, 'new_root_item')
        ti1.title = 'not_new_root_item'
        ti1.save(force_update=True)
        self.assertEqual(ti1.title, 'not_new_root_item')
        ti1.delete()
        self.assertIsNone(ti1.id)

    def test_context_proc_required(self):
        context = Context()
        old_debug = settings.DEBUG
        settings.DEBUG = True
        self.assertRaises(SiteTreeError, self.sitetree.menu, 'tree1', 'trunk', context)
        settings.DEBUG = old_debug

    def test_menu(self):
        menu = self.sitetree.menu('tree1', 'trunk', get_mock_context(path='/about/'))
        self.assertEqual(len(menu), 1)
        self.assertEqual(menu[0].id, self.tree_ttags_root.id)
        self.assertEqual(menu[0].is_current, False)
        self.assertEqual(menu[0].depth, 0)
        self.assertEqual(menu[0].has_children, True)
        self.assertEqual(menu[0].in_current_branch, True)

        menu = self.sitetree.menu('tree2', 'trunk', get_mock_context(path='/sub/'))
        self.assertEqual(len(menu), 6)
        self.assertEqual(menu[0].id, self.t2_root1.id)
        self.assertEqual(menu[1].id, self.t2_root2.id)
        self.assertEqual(menu[0].is_current, False)
        self.assertEqual(menu[0].in_current_branch, False)
        self.assertEqual(menu[1].is_current, True)
        self.assertEqual(menu[1].in_current_branch, True)
        self.assertEqual(menu[0].depth, 0)
        self.assertEqual(menu[1].depth, 0)
        self.assertEqual(menu[0].has_children, False)
        self.assertEqual(menu[1].has_children, False)

    def test_breadcrumbs(self):
        bc1 = self.sitetree.breadcrumbs('tree1', get_mock_context(path='/not_articles/10/'))

        self.assertEqual(len(bc1), 3)

        self.assertEqual(bc1[0].id, self.tree_ttags_root.id)
        self.assertEqual(bc1[1].id, self.t1_root_child2.id)
        self.assertEqual(bc1[1].url_resolved, '/articles/')
        self.assertEqual(bc1[2].id, self.t1_root_child2_sub2.id)

        self.assertEqual(bc1[0].is_current, False)
        self.assertEqual(bc1[1].is_current, False)
        self.assertEqual(bc1[2].is_current, True)

        self.assertEqual(bc1[0].has_children, True)
        self.assertEqual(bc1[1].has_children, True)
        self.assertEqual(bc1[2].has_children, False)

        self.assertEqual(bc1[0].depth, 0)
        self.assertEqual(bc1[1].depth, 1)
        self.assertEqual(bc1[2].depth, 2)

    def test_page_title(self):
        title = self.sitetree.get_current_page_title('tree1', get_mock_context(path='/articles/'))
        self.assertEqual(title, self.t1_root_child2.title)

        title = self.sitetree.get_current_page_title('tree1', get_mock_context(path='/not_articles/'))
        self.assertEqual(title, '')

    def test_page_attr(self):
        attr = self.sitetree.get_current_page_attr('description', 'tree1', get_mock_context(path='/articles/'))
        self.assertEqual(attr, self.t1_root_child2.description)

        attr = self.sitetree.get_current_page_attr('description', 'tree1', get_mock_context(path='/not_articles/'))
        self.assertEqual(attr, '')

    def test_sitetree(self):
        st1 = self.sitetree.tree('tree1', get_mock_context(path='/articles/'))
        self.assertEqual(len(st1), 1)
        self.assertEqual(st1[0].id, self.tree_ttags_root.id)
        self.assertEqual(st1[0].is_current, False)
        self.assertEqual(st1[0].depth, 0)
        self.assertEqual(st1[0].has_children, True)

        st2 = self.sitetree.tree('tree2', get_mock_context(path='/'))
        self.assertIn(self.t2_root7, st2)   # Not every item is visible for non logged in.
        self.assertNotIn(self.t2_root3, st2)
        self.assertEqual(len(st2), 6)

        self.assertEqual(st2[0].id, self.t2_root1.id)
        self.assertEqual(st2[1].id, self.t2_root2.id)

        self.assertEqual(self.t2_root1.access_loggedin, False)
        self.assertEqual(self.t2_root1.access_guest, False)
        self.assertEqual(self.t2_root2.access_loggedin, False)
        self.assertEqual(self.t2_root2.access_guest, False)
        self.assertEqual(self.t2_root3.access_loggedin, True)
        self.assertEqual(self.t2_root3.access_guest, False)

        self.assertEqual(self.t2_root7.access_loggedin, False)
        self.assertEqual(self.t2_root7.access_guest, True)

        self.assertEqual(st2[0].title, '{{ t2_root1_title }}')
        self.assertEqual(st2[1].title, 'put {{ t2_root2_title }} inside')

        self.assertEqual(st2[0].title_resolved, '')
        self.assertEqual(st2[1].title_resolved, 'put my_real_title inside')

        self.assertEqual(st2[0].is_current, True)
        self.assertEqual(st2[1].is_current, False)
        self.assertEqual(st2[0].depth, 0)
        self.assertEqual(st2[1].depth, 0)
        self.assertEqual(st2[0].has_children, False)
        self.assertEqual(st2[1].has_children, False)

        st2 = self.sitetree.tree('tree2', get_mock_context(path='/', user_authorized=True))
        self.assertNotIn(self.t2_root7, st2)   # Not every item is visible for non logged in.
        self.assertIn(self.t2_root3, st2)
        self.assertEqual(len(st2), 6)

    def test_items_hook_tree(self):
        def my_processor(tree_items, tree_sender):
            for item in tree_items:
                item.title_resolved = 'FakedTreeItem'
            return tree_items

        register_items_hook(my_processor)
        items = self.sitetree.tree('tree1', get_mock_context(path='/'))
        register_items_hook(None)

        self.assertEqual(items[0].title_resolved, 'FakedTreeItem')

    def test_items_hook_menu(self):
        def my_processor(tree_items, tree_sender):
            for item in tree_items:
                item.title_resolved = 'FakedMenuItem'
            return tree_items

        register_items_hook(my_processor)
        items = self.sitetree.menu('tree1', 'trunk', get_mock_context(path='/'))
        register_items_hook(None)

        self.assertEqual(items[0].title_resolved, 'FakedMenuItem')

    def test_items_hook_breadcrumbs(self):
        def my_processor(tree_items, tree_sender):
            for item in tree_items:
                item.title_resolved = 'FakedBreadcrumbsItem'
            return tree_items

        register_items_hook(my_processor)
        items = self.sitetree.breadcrumbs('tree1', get_mock_context(path='/not_articles/10/'))
        register_items_hook(None)

        self.assertEqual(items[0].title_resolved, 'FakedBreadcrumbsItem')


class TemplateTagsTest(SitetreeTest):

    @classmethod
    def setUpClass(cls):
        cls.sitetree = SiteTree()

        tree_ttags = Tree(alias='ttags')
        tree_ttags.save()
        cls.tree_ttags = tree_ttags

        tree_ttags_root = TreeItem(
            title='root', tree=tree_ttags, url='/',
            insitetree=True, inbreadcrumbs=True, inmenu=True,
            hint='roothint', description='rootdescr'
        )
        tree_ttags_root.save()
        cls.tree_ttags_root = tree_ttags_root

        tree_ttags_root_child1 = TreeItem(
            title='sometitle', tree=tree_ttags, parent=tree_ttags_root, url='/child1',
            insitetree=True, inbreadcrumbs=True, inmenu=True,
            hint='somehint', description='somedescr'
        )
        tree_ttags_root_child1.save()
        cls.tree_ttags_root_child1 = tree_ttags_root_child1

    def test_sitetree_tree(self):

        tpl = '{% load sitetree %}{% sitetree_tree "mytree" %}'
        self.assertRaises(TemplateSyntaxError, render_string, tpl)

        tpl = '{% load sitetree %}{% sitetree_tree from "mytree" %}'
        result = render_string(tpl)
        self.assertEqual(result.strip(), '')

        tpl = '{% load sitetree %}{% sitetree_tree from "ttags" %}'
        result = render_string(tpl)
        self.assertIn('href="/"', result)

    def test_sitetree_children(self):

        context = get_mock_context(put_var=self.tree_ttags_root)
        self.sitetree.set_global_context(context)

        tpl = '{% load sitetree %}{% sitetree_children %}'
        self.assertRaises(TemplateSyntaxError, render_string, tpl)

        tpl = '{% load sitetree %}{% sitetree_children of put_var for sitetree template "sitetree/tree.html" %}'
        result = render_string(tpl, context=context)
        self.assertIn('href="/child1"', result)

    def test_sitetree_breadcrumbs(self):

        tpl = '{% load sitetree %}{% sitetree_breadcrumbs %}'
        self.assertRaises(TemplateSyntaxError, render_string, tpl)

        tpl = '{% load sitetree %}{% sitetree_breadcrumbs from "mytree" %}'
        result = render_string(tpl)
        self.assertEqual(result.strip(), '<ul>\n\t\n</ul>')

        tpl = '{% load sitetree %}{% sitetree_breadcrumbs from "ttags" %}'
        result = render_string(tpl, context_path='/child1')

        self.assertIn('href="/"', result)
        self.assertIn('root', result)
        self.assertIn('sometitle', result)

    def test_sitetree_menu(self):

        tpl = '{% load sitetree %}{% sitetree_menu %}'
        self.assertRaises(TemplateSyntaxError, render_string, tpl)

        tpl = '{% load sitetree %}{% sitetree_menu from "mytree" include "trunk" %}'
        result = render_string(tpl)
        self.assertEqual(result.strip(), '<ul>\n\t\n</ul>')

        tpl = '{% load sitetree %}{% sitetree_menu from "ttags" include "trunk" %}'
        result = render_string(tpl, context_path='/child1')
        self.assertIn('current_branch">root', result)
        self.assertIn('current_item current_branch">sometitle', result)

    def test_sitetree_page_title(self):
        tpl = '{% load sitetree %}{% sitetree_page_title %}'
        self.assertRaises(TemplateSyntaxError, render_string, tpl)

        with override_settings(DEBUG=True):
            tpl = '{% load sitetree %}{% sitetree_page_title from "ttags" %}'
            self.assertRaises(SiteTreeError, render_string, tpl, context_path='/somewhere')

        tpl = '{% load sitetree %}{% sitetree_page_title from "ttags" %}'
        result = render_string(tpl, context_path='/child1')
        self.assertEqual(result, 'sometitle')

        context = get_mock_context()
        tpl = '{% load sitetree %}{% sitetree_page_title from "ttags" as somev %}'
        render_string(tpl,  context=context)
        self.assertEqual(context.get('somev'), 'root')

    def test_sitetree_page_hint(self):
        tpl = '{% load sitetree %}{% sitetree_page_hint %}'
        self.assertRaises(TemplateSyntaxError, render_string, tpl)

        with override_settings(DEBUG=True):
            tpl = '{% load sitetree %}{% sitetree_page_hint from "ttags" %}'
            self.assertRaises(SiteTreeError, render_string, tpl, context_path='/somewhere')

        tpl = '{% load sitetree %}{% sitetree_page_hint from "ttags" %}'
        result = render_string(tpl, context_path='/child1')
        self.assertEqual(result, 'somehint')

        context = get_mock_context()
        tpl = '{% load sitetree %}{% sitetree_page_hint from "ttags" as somev %}'
        render_string(tpl,  context=context)
        self.assertEqual(context.get('somev'), 'roothint')

    def test_sitetree_page_description(self):
        tpl = '{% load sitetree %}{% sitetree_page_description %}'
        self.assertRaises(TemplateSyntaxError, render_string, tpl)

        with override_settings(DEBUG=True):
            tpl = '{% load sitetree %}{% sitetree_page_description from "ttags" %}'
            self.assertRaises(SiteTreeError, render_string, tpl, context_path='/somewhere')

        tpl = '{% load sitetree %}{% sitetree_page_description from "ttags" %}'
        result = render_string(tpl, context_path='/child1')
        self.assertEqual(result, 'somedescr')

        context = get_mock_context()
        tpl = '{% load sitetree %}{% sitetree_page_description from "ttags" as somev %}'
        render_string(tpl,  context=context)
        self.assertEqual(context.get('somev'), 'rootdescr')

    def test_sitetree_url(self):
        tpl = '{% load sitetree %}{% sitetree_url %}'
        self.assertRaises(TemplateSyntaxError, render_string, tpl)

        context = get_mock_context(path='/child1', put_var=self.tree_ttags_root_child1)
        tpl = '{% load sitetree %}{% sitetree_url for put_var %}'
        result = render_string(tpl, context)
        self.assertEqual(result, '/child1')

        tpl = '{% load sitetree %}{% sitetree_url for put_var as res_var %}'
        render_string(tpl, context)
        self.assertEqual(context.get('res_var'), '/child1')


class TreeTest(SitetreeTest):

    def test_str(self):
        self.assertEqual(self.t3.alias, str(self.t3))

    def test_get_title(self):
        self.assertEqual(self.t3.get_title(), 'tree3')
        self.assertEqual(self.t3_en.get_title(), 'tree3en_title')

    def test_children_filtering(self):
        self.sitetree._global_context = get_mock_context(path='/')
        self.sitetree.get_sitetree('tree3')
        children = self.sitetree.get_children('tree3', self.t3_root)
        filtered = self.sitetree.filter_items(children, 'menu')
        self.assertEqual(filtered, [])

    def test_tree_filtering(self):
        tree = self.sitetree.tree('tree3', get_mock_context(path='/'))
        self.assertEqual(len(tree), 0)

    def test_register_i18n_trees(self):
        register_i18n_trees(['tree3'])
        self.sitetree._global_context = get_mock_context(path='/the_same_url/')

        activate('en')
        self.sitetree.get_sitetree('tree3')
        children = self.sitetree.get_children('tree3', self.t3_en_root)
        self.assertEqual(len(children), 2)
        self.assertFalse(children[0].is_current)
        self.assertTrue(children[1].is_current)

        activate('ru')
        self.sitetree.lang_init()
        self.sitetree.get_sitetree('tree3')
        children = self.sitetree.get_children('tree3', self.t3_root)
        self.assertEqual(len(children), 5)
        self.assertFalse(children[1].is_current)
        self.assertTrue(children[2].is_current)
        self.assertFalse(children[3].is_current)


class DynamicTreeTest(SitetreeTest):

    def test_basic_old_and_new(self):

        # Assert no dynamic attached.
        tree_alias, sitetree_items = self.sitetree.get_sitetree('main')
        self.assertEqual(len(sitetree_items), 1)

        # Assert cache hit.
        tree_alias, sitetree_items = self.sitetree.get_sitetree('main')
        self.assertEqual(len(sitetree_items), 1)

        # Empty cache before dynamic items added.
        self.sitetree.cache.empty()

        self.assertEqual(len(get_dynamic_trees().keys()), 0)

        self.basic_test()  # old-style

        self.assertEqual(len(get_dynamic_trees().keys()), 3)

        self.basic_test(new_style=True)
        self.basic_test(new_style=True, reset_cache=True)

        self.assertEqual(len(get_dynamic_trees().keys()), 3)

    def basic_test(self, new_style=False, reset_cache=False):
        trees = (
            compose_dynamic_tree((
                tree('dynamic_main_root', items=(
                    item('dynamic_main_root_1', 'dynamic_main_root_1_url', url_as_pattern=False, sort_order=2),
                    item('dynamic_main_root_2', 'dynamic_main_root_2_url', url_as_pattern=False, sort_order=1),
                )),
            ), target_tree_alias='main'),
            compose_dynamic_tree((
                tree('dynamic_main_sub', items=(
                    item('dynamic_main_sub_1', 'dynamic_main_sub_1_url',
                         url_as_pattern=False, access_by_perms=['auth.add_group', 'auth.change_group']),
                    item('dynamic_main_sub_2', 'dynamic_main_sub_2_url',
                         url_as_pattern=False, access_by_perms=['auth.add_group'], perms_mode_all=False),
                )),
            ), target_tree_alias='main', parent_tree_item_alias='for_dynamic'),
            compose_dynamic_tree((
                tree('dynamic', items=(
                    item('dynamic_1', 'dynamic_1_url', children=(
                        item('dynamic_1_sub_1', 'dynamic_1_sub_1_url', url_as_pattern=False),
                    ), url_as_pattern=False),
                    item('dynamic_2', 'dynamic_2_url', url_as_pattern=False),
                )),
            )),
        )

        kwargs = {
            'reset_cache': reset_cache
        }

        if new_style:
            register_dynamic_trees(*trees, **kwargs)
        else:
            register_dynamic_trees(trees, **kwargs)

        mock_context = get_mock_context(path='/the_same_url/')
        self.sitetree._global_context = mock_context
        tree_alias, sitetree_items = self.sitetree.get_sitetree('main')

        if reset_cache:
            self.assertEqual(len(sitetree_items), 13)
            children = self.sitetree.get_children('main', self.tree_main_root)
            self.assertEqual(len(children), 6)
            tree_alias, sitetree_items = self.sitetree.get_sitetree('dynamic')
            self.assertEqual(len(sitetree_items), 9)
            children = self.sitetree.get_children('dynamic', sitetree_items[0])
            self.assertEqual(len(children), 1)

        else:

            mock_user = MockUser(True)
            self.assertFalse(self.sitetree.check_access(sitetree_items[1], {'user': mock_user}))
            self.assertTrue(self.sitetree.check_access(sitetree_items[2], {'user': mock_user}))
            self.assertFalse(self.sitetree.check_access(sitetree_items[2], {
                'user': MockUser(True, permissions=['dummy.dummy'])}))

            self.assertEqual(len(sitetree_items), 5)
            self.assertEqual(sitetree_items[1].perms, set(['auth.add_group', 'auth.change_group']))
            self.assertEqual(sitetree_items[3].title, 'dynamic_main_root_1')
            self.assertEqual(sitetree_items[4].title, 'dynamic_main_root_2')
            self.assertEqual(sitetree_items[3].sort_order, 2)
            self.assertEqual(sitetree_items[4].sort_order, 1)
            self.assertIsNone(getattr(sitetree_items[3], 'perms', None))
            children = self.sitetree.get_children('main', self.tree_main_root)
            self.assertEqual(len(children), 2)

            tree_alias, sitetree_items = self.sitetree.get_sitetree('dynamic')
            self.assertEqual(len(sitetree_items), 3)
            children = self.sitetree.get_children('dynamic', sitetree_items[0])
            self.assertEqual(len(children), 1)


class UtilsItemTest(SitetreeTest):

    def test_permission_any(self):
        i1 = item('root', 'url')
        self.assertEqual(i1.access_perm_type, i1.PERM_TYPE_ALL)

        i2 = item('root', 'url', perms_mode_all=True)
        self.assertEqual(i2.access_perm_type, i1.PERM_TYPE_ALL)

        i3 = item('root', 'url', perms_mode_all=False)
        self.assertEqual(i3.access_perm_type, i1.PERM_TYPE_ANY)

    def test_permissions_none(self):
        i1 = item('root', 'url')
        self.assertEqual(i1.permissions, [])

    def test_int_permissions(self):
        i1 = item('root', 'url', access_by_perms=[1, 2, 3])
        self.assertEqual(i1.permissions, [1, 2, 3])

    def test_import_project_sitetree_modules(self):
        cls = get_model_class('MODEL_TREE')
        self.assertIs(cls, Tree)

    def test_get_model_class(self):
        import_project_sitetree_modules()

    def test_import_app_sitetree_module(self):
        self.assertRaises(ImportError, import_app_sitetree_module, 'sitetre')

    def test_get_app_n_model(self):
        app, model = get_app_n_model('MODEL_TREE')
        self.assertEqual(app, 'sitetree')
        self.assertEqual(model, 'Tree')
        self.assertRaises(ImproperlyConfigured, get_app_n_model, 'ALIAS_TRUNK')

    def test_valid_string_permissions(self):
        perm, perm_name = get_permission_and_name()

        i1 = item('root', 'url', access_by_perms=perm_name)
        self.assertEqual(i1.permissions, [perm])

    def test_perm_obj_permissions(self):
        perm, __ = get_permission_and_name()

        i1 = item('root', 'url', access_by_perms=perm)
        self.assertEqual(i1.permissions, [perm])

    def test_bad_string_permissions(self):
        self.assertRaises(ValueError, item, 'root', 'url', access_by_perms='bad name')
        self.assertRaises(ValueError, item, 'root', 'url', access_by_perms='unknown.name')
        self.assertRaises(ValueError, item, 'root', 'url', access_by_perms=42.2)

    def test_access_restricted(self):
        # Test that default is False
        i0 = item('root', 'url', access_by_perms=1)
        self.assertEqual(i0.access_restricted, True)

        # True is respected
        i1 = item('root', 'url')
        self.assertEqual(i1.access_restricted, False)


class TestAdmin(SitetreeTest):

    def test_redirects_handler(self):

        def get_handler(referer, item_id=None):
            req = MockRequest(referer, True, {
                'HTTP_REFERER': referer
            })

            args = [req]
            kwargs = {}
            if item_id is not None:
                kwargs['item_id'] = item_id
            return redirects_handler(*args, **kwargs)

        handler = get_handler('/')
        self.assertEqual(handler._headers['location'][1], '/../')

        handler = get_handler('/delete/')
        self.assertEqual(handler._headers['location'][1], '/delete/../../')

        handler = get_handler('/history/')
        self.assertEqual(handler._headers['location'][1], '/history/../../')

        handler = get_handler('/history/', 42)
        self.assertEqual(handler._headers['location'][1], '/history/../')

    def test_tree_item_admin(self):
        admin = TreeItemAdmin(TreeItem, site)
        admin.tree = Tree.objects.get(alias='main')
        form = admin.get_form(MockRequest())
        self.assertEqual(len(form.known_url_names), 3)
        self.assertIn('articles_list', form.known_url_names)
        self.assertIn('articles_detailed', form.known_url_names)
        self.assertIn('url', form.known_url_names)

    def test_tree_item_admin_get_tree(self):
        main_tree = Tree.objects.get(alias='main')
        main_tree_item = TreeItem.objects.filter(tree__alias='main')[0]

        admin = TreeItemAdmin(TreeItem, site)
        tree = admin.get_tree(MockRequest(), main_tree.pk)
        self.assertEqual(tree.alias, 'main')
        tree = admin.get_tree(MockRequest(), None, main_tree_item.pk)
        self.assertEqual(tree.alias, 'main')

    def test_tree_item_admin_item_move(self):
        main_tree = Tree.objects.get(alias='main')

        admin = TreeItemAdmin(TreeItem, site)

        new_item_1 = TreeItem(title='title_1', sort_order=1, tree_id=main_tree.pk)
        new_item_1.save()

        new_item_2 = TreeItem(title='title_2', sort_order=2, tree_id=main_tree.pk)
        new_item_2.save()

        new_item_3 = TreeItem(title='title_3', sort_order=3, tree_id=main_tree.pk)
        new_item_3.save()

        admin.item_move(None, None, new_item_2.id, 'up')

        self.assertEqual(TreeItem.objects.get(pk=new_item_1.id).sort_order, 2)
        self.assertEqual(TreeItem.objects.get(pk=new_item_2.id).sort_order, 1)
        self.assertEqual(TreeItem.objects.get(pk=new_item_3.id).sort_order, 3)

        admin.item_move(None, None, new_item_1.id, 'down')

        self.assertEqual(TreeItem.objects.get(pk=new_item_1.id).sort_order, 3)
        self.assertEqual(TreeItem.objects.get(pk=new_item_2.id).sort_order, 1)
        self.assertEqual(TreeItem.objects.get(pk=new_item_3.id).sort_order, 2)

    def test_tree_item_admin_save_model(self):
        main_tree = Tree.objects.get(alias='main')
        tree_item = TreeItem.objects.filter(tree__alias='main')[0]

        admin = TreeItemAdmin(TreeItem, site)
        admin.tree = main_tree
        admin.save_model(MockRequest(), tree_item, None, change=True)
        self.assertIs(tree_item.tree, admin.tree)

    def test_tree_admin(self):
        admin = TreeAdmin(Tree, site)
        urls = admin.get_urls()
        self.assertIn('tree_id', urls[1]._regex)


class TestForms(SitetreeTest):

    def test_basic(self):
        form = TreeItemForm(tree='main', tree_item='root')
        self.assertIn('tree_item', form.fields)

        self.assertEqual(form.fields['tree_item'].tree, 'main')
        self.assertEqual(form.fields['tree_item'].initial, 'root')
        self.assertEqual(form.fields['tree_item'].choices[1][1], 'root')


class TestManagementCommands(SitetreeTest):

    def setUp(self):
        self.file_contents = (
            '[{"pk": 2, "fields": {"alias": "/tree1/", "title": "tree one"}, "model": "sitetree.tree"}, '
            '{"pk": 3, "fields": {"alias": "/tree2/", "title": "tree two"}, "model": "sitetree.tree"}, '
            '{"pk": 7, "fields": {"access_restricted": false, "inmenu": true, "title": "tree item one",'
            ' "hidden": false, "description": "", "alias": null, "url": "/tree1/item1/", "access_loggedin": false,'
            ' "urlaspattern": false, "access_perm_type": 1, "tree": 2, "hint": "", "inbreadcrumbs": true,'
            ' "access_permissions": [], "sort_order": 7, "access_guest": false, "parent": null, "insitetree": true},'
            ' "model": "sitetree.treeitem"}]')

    def test_sitetreedump(self):
        stdout = sys.stdout
        sys.stdout = StringIO()

        call_command('sitetreedump')

        output = loads(sys.stdout.getvalue())
        sys.stdout = stdout

        self.assertEqual(output[0]['model'], 'sitetree.tree')
        self.assertEqual(output[5]['model'], 'sitetree.treeitem')

    def test_sitetreeload(self):
        try:
            import __builtin__
            patch_val = '__builtin__.open'
        except ImportError:
            # python3
            patch_val = 'builtins.open'

        with mock.patch(patch_val) as mock_file:
            mock_file.return_value.__enter__ = lambda s: s
            mock_file.return_value.__exit__ = mock.Mock()
            mock_file.return_value.read.return_value = self.file_contents

            call_command('sitetreeload', 'somefile.json')

            self.assertTrue(Tree.objects.filter(title='tree one').exists())
            self.assertTrue(Tree.objects.filter(title='tree two').exists())
            self.assertTrue(TreeItem.objects.filter(title='tree item one').exists())
