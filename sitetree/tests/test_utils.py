#! -*- encoding: utf-8 -*-
from __future__ import unicode_literals

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

    settings.MODEL_TREE = 'nowhere.Model'

    with pytest.raises(ImproperlyConfigured):
        get_model_class('MODEL_TREE')
