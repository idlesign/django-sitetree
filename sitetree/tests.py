from django.conf import settings
from django.utils import unittest
from django.utils.translation import activate
from django import template
from django.contrib.auth.models import Permission
from django.core import urlresolvers

from sitetree.models import Tree, TreeItem
from sitetree.utils import tree, item
from sitetree.sitetreeapp import SiteTree, SiteTreeError, register_items_hook, register_i18n_trees, register_dynamic_trees, compose_dynamic_tree

from django.conf.urls import patterns, url


urlpatterns = patterns('',
    url(r'articles/', lambda r: None, name='articles_list'),
    url(r'articles/(\d+)/', lambda r: None, name='articles_detailed'),
    url(r'articles/(?P<id>\d+)_(?P<slug>[\w-]+)/', lambda r: None, name='url'),
)


class MockRequest(object):
    def __init__(self, path, user_authorized):
        self.path = path
        self.user = MockUser(user_authorized)


class MockUser(object):
    def __init__(self, authorized):
        self.authorized = authorized

    def is_authenticated(self):
        return self.authorized


def get_mock_context(app=None, path=None, user_authorized=False, tree_item=None, put_var=None):
    ctx = template.Context({'request': MockRequest(path, user_authorized),
                            't2_root2_title': 'my_real_title', 'art_id': 10, 'tree_item': tree_item,
                            'somevar_str': 'articles_list', 'somevar_list': ['a', 'b'], 'put_var': put_var}, current_app=app)
    return ctx


class TreeModelTest(unittest.TestCase):
    def test_create_rename_delete(self):
        tree = Tree(alias='mytree')
        tree.save(force_insert=True)
        self.assertIsNotNone(tree.id)
        self.assertEqual(tree.alias, 'mytree')
        tree.alias = 'not_mytree'
        tree.save(force_update=True)
        self.assertEqual(tree.alias, 'not_mytree')
        tree.delete()
        self.assertIsNone(tree.id)

    def test_unique_aliases(self):
        tree1 = Tree(alias='mytree')
        tree1.save(force_insert=True)
        tree2 = Tree(alias='mytree')
        self.assertRaises(Exception, tree2.save)


class TreeItemModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sitetree = SiteTree()

        t1 = Tree(alias='tree1')
        t1.save(force_insert=True)

        t1_root = TreeItem(title='root', tree=t1, url='/')
        t1_root.save(force_insert=True)

        t1_root_child1 = TreeItem(title='child1', tree=t1, parent=t1_root, url='/about/')
        t1_root_child1.save(force_insert=True)

        t1_root_child2 = TreeItem(title='child2', tree=t1, parent=t1_root, url='articles_list', urlaspattern=True, description='items_descr')
        t1_root_child2.save(force_insert=True)

        t1_root_child2_sub1 = TreeItem(title='subchild1', tree=t1, parent=t1_root_child2,
            url='articles_detailed art_id', urlaspattern=True)
        t1_root_child2_sub1.save(force_insert=True)

        t1_root_child2_sub2 = TreeItem(title='subchild2', tree=t1, parent=t1_root_child2, url='/not_articles/10/')
        t1_root_child2_sub2.save(force_insert=True)

        t1_root_child3 = TreeItem(title='child_with_var_str', tree=t1, parent=t1_root, url='somevar_str', urlaspattern=True)
        t1_root_child3.save(force_insert=True)

        t1_root_child4 = TreeItem(title='child_with_var_list', tree=t1, parent=t1_root, url='somevar_list', urlaspattern=True)
        t1_root_child4.save(force_insert=True)

        t2 = Tree(alias='tree2')
        t2.save(force_insert=True)

        t2_root1 = TreeItem(title='{{ t2_root1_title }}', tree=t2, url='/')
        t2_root1.save(force_insert=True)

        t2_root2 = TreeItem(title='put {{ t2_root2_title }} inside', tree=t2, url='/sub/')
        t2_root2.save(force_insert=True)

        t2_root3 = TreeItem(title='for logged in only', tree=t2, url='/some/', access_loggedin=True)
        t2_root3.save(force_insert=True)

        t2_root4 = TreeItem(title='url quoting', tree=t2, url='url 2 put_var', urlaspattern=True)
        t2_root4.save(force_insert=True)

        t2_root5 = TreeItem(title='url quoting 1.5 style', tree=t2, url="'url' 2 put_var", urlaspattern=True)
        t2_root5.save(force_insert=True)

        t2_root6 = TreeItem(title='url quoting 1.5 style', tree=t2, url='"url" 2 put_var', urlaspattern=True)
        t2_root6.save(force_insert=True)

        t2_root7 = TreeItem(title='for guests only', tree=t2, url='/some_other/', access_guest=True)
        t2_root7.save(force_insert=True)

        cls.t1 = t1
        cls.t1_root = t1_root
        cls.t1_root_child1 = t1_root_child1
        cls.t1_root_child2 = t1_root_child2
        cls.t1_root_child3 = t1_root_child3
        cls.t1_root_child2_sub1 = t1_root_child2_sub1
        cls.t1_root_child2_sub2 = t1_root_child2_sub2

        cls.t2 = t2
        cls.t2_root1 = t2_root1

        cls.t2_root2 = t2_root2
        cls.t2_root3 = t2_root3
        cls.t2_root4 = t2_root4
        cls.t2_root5 = t2_root5
        cls.t2_root6 = t2_root6
        cls.t2_root7 = t2_root7

        # set urlconf to test's one
        cls.old_urlconf = urlresolvers.get_urlconf()
        urlresolvers.set_urlconf('sitetree.tests')

    @classmethod
    def tearDownClass(cls):
        urlresolvers.set_urlconf(cls.old_urlconf)

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
        ti1.save(force_insert=True)
        self.assertIsNotNone(ti1.id)
        self.assertEqual(ti1.title, 'new_root_item')
        ti1.title = 'not_new_root_item'
        ti1.save(force_update=True)
        self.assertEqual(ti1.title, 'not_new_root_item')
        ti1.delete()
        self.assertIsNone(ti1.id)

    def test_context_proc_required(self):
        context = template.Context()
        old_debug = settings.DEBUG
        settings.DEBUG = True
        self.assertRaises(SiteTreeError, self.sitetree.menu, 'tree1', 'trunk', context)
        settings.DEBUG = old_debug

    def test_menu(self):
        menu = self.sitetree.menu('tree1', 'trunk', get_mock_context(path='/about/'))
        self.assertEqual(len(menu), 1)
        self.assertEqual(menu[0].id, self.t1_root.id)
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

        self.assertEqual(bc1[0].id, self.t1_root.id)
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
        self.assertEqual(st1[0].id, self.t1_root.id)
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


class TreeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sitetree = SiteTree()

        t1 = Tree(alias='tree3')
        t1.save(force_insert=True)

        t1_root = TreeItem(title='root', tree=t1, url='/', hidden=True)
        t1_root.save(force_insert=True)

        t1_root_child1 = TreeItem(title='child1', tree=t1, parent=t1_root, url='/0/', access_loggedin=True)
        t1_root_child1.save(force_insert=True)

        t1_root_child2 = TreeItem(title='child2', tree=t1, parent=t1_root, url='/1/', inmenu=True, hidden=True)
        t1_root_child2.save(force_insert=True)

        t1_root_child3 = TreeItem(title='child3', tree=t1, parent=t1_root, url='/the_same_url/', inmenu=False)
        t1_root_child3.save(force_insert=True)

        t1_root_child4 = TreeItem(title='child4', tree=t1, parent=t1_root, url='/3/', hidden=True)
        t1_root_child4.save(force_insert=True)

        t1_root_child5 = TreeItem(title='child5', tree=t1, parent=t1_root, url='/4/', inmenu=True, hidden=True)
        t1_root_child5.save(force_insert=True)

        t2 = Tree(alias='tree3_en')
        t2.save(force_insert=True)

        t2_root = TreeItem(title='root_en', tree=t2, url='/')
        t2_root.save(force_insert=True)

        t2_root_child1 = TreeItem(title='child1_en', tree=t2, parent=t2_root, url='/0_en/')
        t2_root_child1.save(force_insert=True)

        t2_root_child2 = TreeItem(title='child2_en', tree=t2, parent=t2_root, url='/the_same_url/')
        t2_root_child2.save(force_insert=True)

        cls.t1 = t1
        cls.t1_root = t1_root
        cls.t1_root_child1 = t1_root_child1
        cls.t1_root_child2 = t1_root_child2
        cls.t1_root_child2 = t1_root_child3
        cls.t1_root_child2 = t1_root_child4
        cls.t1_root_child2 = t1_root_child5

        cls.t2_root = t2_root

    def test_children_filtering(self):
        self.sitetree._global_context = get_mock_context(path='/')
        self.sitetree.get_sitetree('tree3')
        children = self.sitetree.get_children('tree3', self.t1_root)
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
        children = self.sitetree.get_children('tree3', self.t2_root)
        self.assertEqual(len(children), 2)
        self.assertFalse(children[0].is_current)
        self.assertTrue(children[1].is_current)

        activate('ru')
        self.sitetree.get_sitetree('tree3')
        children = self.sitetree.get_children('tree3', self.t1_root)
        self.assertEqual(len(children), 5)
        self.assertFalse(children[1].is_current)
        self.assertTrue(children[2].is_current)
        self.assertFalse(children[3].is_current)


class DynamicTreeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sitetree = SiteTree()

        t1 = Tree(alias='main')
        t1.save(force_insert=True)

        t1_root = TreeItem(title='root', tree=t1, url='/', alias='for_dynamic')
        t1_root.save(force_insert=True)

        cls.t1 = t1
        cls.t1_root = t1_root

    def test_basic(self):
        register_dynamic_trees((
            compose_dynamic_tree((
                tree('dynamic_main_root', items=(
                    item('dynamic_main_root_1', 'dynamic_main_root_1_url', url_as_pattern=False),
                    item('dynamic_main_root_2', 'dynamic_main_root_2_url', url_as_pattern=False),
                )),
            ), target_tree_alias='main'),
            compose_dynamic_tree((
                tree('dynamic_main_sub', items=(
                    item('dynamic_main_sub_1', 'dynamic_main_sub_1_url', url_as_pattern=False),
                    item('dynamic_main_sub_2', 'dynamic_main_sub_2_url', url_as_pattern=False),
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
        ))

        self.sitetree._global_context = get_mock_context(path='/the_same_url/')
        tree_alias, sitetree_items = self.sitetree.get_sitetree('main')
        self.assertEqual(len(sitetree_items), 5)
        self.assertEqual(sitetree_items[3].title, 'dynamic_main_root_1')
        self.assertEqual(sitetree_items[4].title, 'dynamic_main_root_2')
        children = self.sitetree.get_children('main', self.t1_root)
        self.assertEqual(len(children), 2)


        tree_alias, sitetree_items = self.sitetree.get_sitetree('dynamic')
        self.assertEqual(len(sitetree_items), 3)
        children = self.sitetree.get_children('dynamic', sitetree_items[0])
        self.assertEqual(len(children), 1)


class UtilsItemTest(unittest.TestCase):

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

    def test_valid_string_permissions(self):
        perm = Permission.objects.all()[0]
        perm_name = "{}.{}".format(perm.content_type.app_label, perm.codename)

        i1 = item('root', 'url', access_by_perms=perm_name)
        self.assertEqual(i1.permissions, [perm])

    def test_perm_obj_permissions(self):
        perm = Permission.objects.all()[0]

        i1 = item('root', 'url', access_by_perms=perm)
        self.assertEqual(i1.permissions, [perm])

    def test_bad_string_permissions(self):
        self.assertRaises(ValueError, item, 'root', 'url', access_by_perms='bad name')

    def test_access_restricted(self):
        # Test that default is False
        i0 = item('root', 'url', access_by_perms=1)
        self.assertEqual(i0.access_restricted, True)

        # True is respected
        i1 = item('root', 'url')
        self.assertEqual(i1.access_restricted, False)
