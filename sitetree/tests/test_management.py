from json import loads

import pytest
from django.core.management.base import CommandError
from django.core.serializers.base import DeserializationError


def test_sitetreeload(tmpdir, capsys, command_run):
    from sitetree.models import Tree, TreeItem

    def load(treedump, command_kwargs=None):
        f = tmpdir.join('somefile.json')
        f.write(treedump)
        command_kwargs = command_kwargs or {}
        command_run('sitetreeload', [f'{f}'], command_kwargs)

    treedump = (
        '['
        '{"pk": 2, "fields": {"alias": "tree1", "title": "tree one"}, "model": "sitetree.tree"}, '
        '{"pk": 3, "fields": {"alias": "tree2", "title": "tree two"}, "model": "sitetree.tree"}, '
        '{"pk": 7, "fields": {"access_restricted": false, "inmenu": true, "title": "tree item one",'
        ' "hidden": false, "description": "", "alias": null, "url": "/tree1/item1/", "access_loggedin": false,'
        ' "urlaspattern": false, "access_perm_type": 1, "tree": 2, "hint": "", "inbreadcrumbs": true,'
        ' "access_permissions": [], "sort_order": 7, "access_guest": false, "parent": null, "insitetree": true},'
        ' "model": "sitetree.treeitem"},'
        '{"pk": 8, "model": "sitetree.treeitem", '
        '"fields": {"title": "tree item two", "alias": null, "url": "/", "tree": 2, "sort_order": 8, "parent": 7}}'
        ']'
    )

    with pytest.raises(CommandError):
        load(treedump, dict(items_into_tree='nonexisting'))

    load(treedump)

    assert Tree.objects.filter(title='tree one').exists()
    assert Tree.objects.filter(title='tree two').exists()
    assert TreeItem.objects.get(title='tree item one', tree__alias='tree1')
    assert TreeItem.objects.get(title='tree item two', tree__alias='tree1', parent__title='tree item one')

    load(treedump, dict(items_into_tree='tree2'))
    assert TreeItem.objects.filter(title='tree item one', tree__alias='tree2').exists()

    load(treedump, dict(mode='replace'))
    assert TreeItem.objects.filter(title='tree item one').count() == 1

    with pytest.raises(DeserializationError):
        load(treedump.replace('7}}', '7}},'), dict(mode='replace'))

    load(treedump.replace('7}}', '27}}'), dict(mode='replace'))
    out, err = capsys.readouterr()
    assert 'does not exist.' in err


def test_sitetreedump(capsys, common_tree, command_run):

    command_run('sitetreedump')

    out, _ = capsys.readouterr()
    out = loads(out)

    assert len(out) == len(common_tree)

    command_run('sitetreedump', ['notree'])

    out, _ = capsys.readouterr()
    out = loads(out)

    assert out == []


def test_sitetree_resync_apps(capsys, command_run):
    from sitetree.models import TreeItem

    command_run('sitetree_resync_apps', ['sitetree.tests.testapp'])
    out, _ = capsys.readouterr()

    assert 'Sitetrees found in' in out
    assert len(TreeItem.objects.all()) == 2
