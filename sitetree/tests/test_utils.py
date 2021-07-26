import pytest
from django.core.exceptions import ImproperlyConfigured


def test_import():

    from sitetree.utils import import_project_sitetree_modules

    modules = import_project_sitetree_modules()

    assert len(modules) == 1
    assert modules[0].sitetrees


def test_get_app_n_model():

    from sitetree.utils import get_app_n_model

    app, model = get_app_n_model('MODEL_TREE')
    assert app == 'sitetree'
    assert model == 'Tree'

    with pytest.raises(ImproperlyConfigured):
        get_app_n_model('ALIAS_TRUNK')


def test_import_app_sitetree_module():

    from sitetree.utils import import_app_sitetree_module

    with pytest.raises(ImportError):
        import_app_sitetree_module('sitetre')


def test_import_project_sitetree_modules():

    from sitetree import settings
    from sitetree.models import Tree
    from sitetree.utils import get_model_class

    cls = get_model_class('MODEL_TREE')

    assert cls is Tree

    model_old = settings.MODEL_TREE
    settings.MODEL_TREE = 'nowhere.Model'

    try:
        with pytest.raises(ImproperlyConfigured):
            get_model_class('MODEL_TREE')

    finally:
        settings.MODEL_TREE = model_old


def get_permission_and_name():
    from django.contrib.auth.models import Permission
    perm = Permission.objects.all()[0]
    perm_name = f'{perm.content_type.app_label}.{perm.codename}'
    return perm, perm_name


class TestPermissions():

    def test_permission_any(self):
        from sitetree.toolbox import item

        i1 = item('root', 'url')
        assert i1.access_perm_type == i1.PERM_TYPE_ALL
        assert i1.permissions == []

        i2 = item('root', 'url', perms_mode_all=True)
        assert i2.access_perm_type == i1.PERM_TYPE_ALL

        i3 = item('root', 'url', perms_mode_all=False)
        assert i3.access_perm_type == i1.PERM_TYPE_ANY

    def test_int_permissions(self):
        from sitetree.toolbox import item

        i1 = item('root', 'url', access_by_perms=[1, 2, 3])
        assert i1.permissions == [1, 2, 3]

    def test_valid_string_permissions(self):
        from sitetree.toolbox import item

        perm, perm_name = get_permission_and_name()

        i1 = item('root', 'url', access_by_perms=perm_name)
        assert i1.permissions == [perm]

    def test_perm_obj_permissions(self):
        from sitetree.toolbox import item

        perm, __ = get_permission_and_name()

        i1 = item('root', 'url', access_by_perms=perm)
        assert i1.permissions == [perm]

    def test_bad_string_permissions(self, template_context, template_render_tag):
        from sitetree.toolbox import register_dynamic_trees, tree, item, compose_dynamic_tree

        register_dynamic_trees(compose_dynamic_tree([tree('bad', items=[
            item('root', 'url', access_by_perms='bad name'),
        ])]), reset_cache=True)

        with pytest.raises(ValueError):
            template_render_tag(
                'sitetree', f'sitetree_page_title from "bad"',
                template_context(request='/'))

    def test_unknown_name_permissions(self, template_context, template_render_tag):
        from sitetree.toolbox import register_dynamic_trees, tree, item, compose_dynamic_tree

        register_dynamic_trees(compose_dynamic_tree([tree('unknown', items=[
            item('root', 'url', access_by_perms='unknown.name'),
        ])]), reset_cache=True)

        with pytest.raises(ValueError):
            template_render_tag(
                'sitetree', f'sitetree_page_title from "unknown"',
                template_context(request='/'))

    def test_float_permissions(self, template_context, template_render_tag):
        from sitetree.toolbox import register_dynamic_trees, tree, item, compose_dynamic_tree

        register_dynamic_trees(compose_dynamic_tree([tree('fortytwodottwo', items=[
            item('root', 'url', access_by_perms=42.2),
        ])]), reset_cache=True)

        with pytest.raises(ValueError) as e:
            template_render_tag(
                'sitetree', f'sitetree_page_title from "fortytwodottwo"',
                template_context(request='/'))

    def test_access_restricted(self):
        from sitetree.toolbox import item

        # Test that default is False
        i0 = item('root', 'url', access_by_perms=1)
        assert i0.access_restricted

        # True is respected
        i1 = item('root', 'url')
        assert not i1.access_restricted
