from django import VERSION
from django.db.models import get_model
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

from sitetree import settings

DJANGO_VERSION_INT = int('%s%s%s' % VERSION[:3])


def tree(alias, title='', items=None):
    """Dynamically creates and returns a sitetree.
    `items` - dynamic sitetree items objects created by `item` function.

    """
    tree_obj = get_tree_model()(alias=alias, title=title)
    tree_obj.id = id(tree_obj)

    if items is not None:
        tree_obj.dynamic_items = []
        def traverse(items):
            for item in items:
                item.tree = tree_obj
                tree_obj.dynamic_items.append(item)
                if hasattr(item, 'dynamic_children'):
                    traverse(item.dynamic_children)

        traverse(items)
    return tree_obj


def item(title, url, children=None, url_as_pattern=True, hint='', alias='', description='', in_menu=True, in_breadcrumbs=True, in_sitetree=True, access_loggedin=False, access_guest=False):
    """Dynamically creates and returns a sitetree item object.
    `children` - a list of children for tree item. Children should also be created by `item` function.

    """
    item_obj = get_tree_item_model()(title=title, url=url, urlaspattern=url_as_pattern,
                                   hint=hint, alias=alias, description=description, inmenu=in_menu,
                                   insitetree=in_sitetree, inbreadcrumbs=in_breadcrumbs,
                                   access_loggedin=access_loggedin, access_guest=access_guest)
    item_obj.id = id(item_obj)
    item_obj.dynamic_children = []

    if children is not None:
        for child in children:
            child.parent_id = item_obj.id
            item_obj.dynamic_children.append(child)
    return item_obj


def import_sitetrees():
    """Imports sitetrees modules from packages (apps)."""
    from django.conf import settings
    module_name = 'sitetree'

    submodules = []
    for app in settings.INSTALLED_APPS:
        module = import_module(app)
        try:
            sub_module = import_module('%s.%s' % (app, module_name))
            submodules.append(sub_module)
        except:
            if module_has_submodule(module, module_name):
                raise

    return submodules


def get_app_n_model(settings_entry_name):
    """Returns tuple with application and tree[item] model class names."""
    try:
        app_name, model_name = getattr(settings, settings_entry_name).split('.')
    except ValueError:
        raise ImproperlyConfigured('`SITETREE_%s` must have the following format: `app_name.model_name`.' % settings_entry_name)
    return app_name, model_name


def get_model_class(settings_entry_name):
    """Returns a certain sitetree model as defined in the project settings."""
    app_name, model_name = get_app_n_model(settings_entry_name)
    model = get_model(app_name, model_name)

    if model is None:
        raise ImproperlyConfigured('`SITETREE_%s` refers to model `%s` that has not been installed.' % (settings_entry_name, model_name))

    return model


def get_tree_model():
    """Returns the Tree model, set for the project."""
    return get_model_class('MODEL_TREE')


def get_tree_item_model():
    """Returns the TreeItem model, set for the project."""
    return get_model_class('MODEL_TREE_ITEM')
