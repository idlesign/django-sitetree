from django.contrib.admin.sites import site


def get_item_admin():
    from sitetree.models import TreeItem
    from sitetree.admin import TreeItemAdmin
    admin = TreeItemAdmin(TreeItem, site)
    return admin


def test_parent_choices(request_client, build_tree, user_create, template_strip_tags):

    out = build_tree(
        {'alias': 'tree1'},
        [{
            'title': 'one', 'url': '/one/', 'children': [
                {'title': 'subone', 'url': '/subone/'}
            ]
        }]
    )

    build_tree(
        {'alias': 'tree2'},
        [{
            'title': 'some', 'url': '/some/', 'children': [
                {'title': 'other', 'url': '/other/'}
            ]
        }]
    )
    subone = out['/subone/']
    client = request_client(user=user_create(superuser=True))
    result = client.get(('admin:sitetree_treeitem_change', dict(item_id=subone.id, tree_id=subone.tree_id)))
    stripped = template_strip_tags(result.content.decode())
    print(result.content.decode())
    assert '|---------|one|&nbsp;&nbsp;&nbsp;&nbsp;|- subone' in stripped
    assert '|---------|some|&nbsp;&nbsp;&nbsp;&nbsp;|- other' not in stripped


def test_admin_tree_item_basic(request_get, common_tree):

    admin = get_item_admin()
    admin.tree = common_tree['']
    form = admin.get_form(request_get())

    known_url_names = form.known_url_names
    assert set(known_url_names) == {'contacts_china', 'devices_grp', 'contacts_australia', 'raiser'}


def test_admin_tree_item_move(common_tree):
    from sitetree.models import TreeItem, Tree

    main_tree = Tree(alias='main')
    main_tree.save()

    new_item_1 = TreeItem(title='title_1', sort_order=1, tree_id=main_tree.pk)
    new_item_1.save()

    new_item_2 = TreeItem(title='title_2', sort_order=2, tree_id=main_tree.pk)
    new_item_2.save()

    new_item_3 = TreeItem(title='title_3', sort_order=3, tree_id=main_tree.pk)
    new_item_3.save()

    admin = get_item_admin()

    admin.item_move(None, None, new_item_2.id, 'up')

    assert TreeItem.objects.get(pk=new_item_1.id).sort_order == 2
    assert TreeItem.objects.get(pk=new_item_2.id).sort_order == 1
    assert TreeItem.objects.get(pk=new_item_3.id).sort_order == 3

    admin.item_move(None, None, new_item_1.id, 'down')

    assert TreeItem.objects.get(pk=new_item_1.id).sort_order == 3
    assert TreeItem.objects.get(pk=new_item_2.id).sort_order == 1
    assert TreeItem.objects.get(pk=new_item_3.id).sort_order == 2


def test_admin_tree_item_get_tree(request_get, common_tree):
    home = common_tree['']
    tree = home.tree

    admin = get_item_admin()

    assert admin.get_tree(request_get(), tree.pk) == tree
    assert admin.get_tree(request_get(), None, home.pk) == tree


def test_admin_tree_item_save_model(request_get, common_tree):
    users = common_tree['/users/']
    tree = users.tree

    admin = get_item_admin()

    # Simulate bogus
    admin.previous_parent = users.parent
    users.parent = users

    admin.tree = tree
    admin.save_model(request_get(), users, None, change=True)

    assert users.tree == admin.tree
    assert users.parent == admin.previous_parent


def test_admin_tree():
    from sitetree.admin import TreeAdmin
    from sitetree.models import Tree

    admin = TreeAdmin(Tree, site)
    urls = admin.get_urls()

    assert len(urls) > 0


def test_redirects_handler(request_get):
    from sitetree.admin import redirects_handler

    def get_handler(referer, item_id=None):

        req = request_get(referer)
        req.META['HTTP_REFERER'] = referer

        args = [req]
        kwargs = {}
        if item_id is not None:
            kwargs['item_id'] = item_id

        return redirects_handler(*args, **kwargs)

    handler = get_handler('/')
    assert handler._headers['location'][1] == '/../'

    handler = get_handler('/delete/')
    assert handler._headers['location'][1] == '/delete/../../'

    handler = get_handler('/history/')
    assert handler._headers['location'][1] == '/history/../../'

    handler = get_handler('/history/', 42)
    assert handler._headers['location'][1] == '/history/../'
