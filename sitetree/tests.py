from django.utils import unittest
from django import template

from models import Tree, TreeItem
from sitetreeapp import SiteTree, SiteTreeError


class MockRequest(object):

    def __init__(self, path, user_authorized):
        self.path = path
        self.user = MockUser(user_authorized)


class MockUser(object):

    def __init__(self, authorized):
        self.authorized = authorized

    def is_authenticated(self):
        return self.authorized


def get_mock_context(app=None, path=None, user_authorized=False):
    return template.Context({'request': MockRequest(path, user_authorized), 't2_root2_title': 'my_real_title', 'art_id': 10}, current_app=app)


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

        t1_root_child2 = TreeItem(title='child2', tree=t1, parent=t1_root, url='articles_list', urlaspattern=True)
        t1_root_child2.save(force_insert=True)

        t1_root_child2_sub1 = TreeItem(title='subchild1', tree=t1, parent=t1_root_child2, url='articles_detailed art_id', urlaspattern=True)
        t1_root_child2_sub1.save(force_insert=True)

        t1_root_child2_sub2 = TreeItem(title='subchild2', tree=t1, parent=t1_root_child2, url='/not_articles/10/')
        t1_root_child2_sub2.save(force_insert=True)

        t2 = Tree(alias='tree2')
        t2.save(force_insert=True)

        t2_root1 = TreeItem(title='{{ t2_root1_title }}', tree=t2, url='/')
        t2_root1.save(force_insert=True)

        t2_root2 = TreeItem(title='put {{ t2_root2_title }} inside', tree=t2, url='/sub/')
        t2_root2.save(force_insert=True)

        t2_root3 = TreeItem(title='for logged in only', tree=t2, url='/some/', access_loggedin=True)
        t2_root3.save(force_insert=True)

        cls.t1 = t1
        cls.t1_root = t1_root
        cls.t1_root_child1 = t1_root_child1
        cls.t1_root_child2 = t1_root_child2
        cls.t1_root_child2_sub1 = t1_root_child2_sub1
        cls.t1_root_child2_sub2 = t1_root_child2_sub2

        cls.t2 = t2
        cls.t2_root1 = t2_root1
        
        cls.t2_root2 = t2_root2
        cls.t2_root3 = t2_root3

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
        self.assertRaises(SiteTreeError, self.sitetree.menu, 'tree1', 'trunk', context)

    def test_menu(self):
        menu = self.sitetree.menu('tree1', 'trunk', get_mock_context(path='/about/'))
        self.assertEqual(len(menu), 1)
        self.assertEqual(menu[0].id, self.t1_root.id)
        self.assertEqual(menu[0].is_current, False)
        self.assertEqual(menu[0].depth, 0)
        self.assertEqual(menu[0].has_children, True)
        self.assertEqual(menu[0].in_current_branch, True)

        menu = self.sitetree.menu('tree2', 'trunk', get_mock_context(path='/sub/'))
        self.assertEqual(len(menu), 2)
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

    def test_sitetree(self):
        st1 = self.sitetree.tree('tree1', get_mock_context(path='/articles/'))
        self.assertEqual(len(st1), 1)
        self.assertEqual(st1[0].id, self.t1_root.id)
        self.assertEqual(st1[0].is_current, False)
        self.assertEqual(st1[0].depth, 0)
        self.assertEqual(st1[0].has_children, True)

        st2 = self.sitetree.tree('tree2', get_mock_context(path='/'))
        self.assertEqual(len(st2), 3)
        self.assertEqual(st2[0].id, self.t2_root1.id)
        self.assertEqual(st2[1].id, self.t2_root2.id)

        self.assertEqual(self.t2_root1.access_loggedin, False)
        self.assertEqual(self.t2_root2.access_loggedin, False)
        self.assertEqual(self.t2_root3.access_loggedin, True)

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
