from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from django.utils.module_loading import module_has_submodule

try:
    from importlib import import_module
except ImportError:  # Python < 2.7
    from django.utils.importlib import import_module

try:
    from django.apps import apps
    apps_get_model = apps.get_model
except ImportError:  # Django < 1.7
    from django.db.models import get_model
    apps_get_model = None


from sitetree import settings


def generate_id_for(obj):
    """Generates and returns a unique identifier for the given object."""
    return id(obj)


def tree(alias, title='', items=None):
    """Dynamically creates and returns a sitetree.

    :param str|unicode alias:
    :param str|unicode title:
    :param iterable items: dynamic sitetree items objects created by `item` function.
    :rtype: TreeBase
    """
    tree_obj = get_tree_model()(alias=alias, title=title)
    tree_obj.id = generate_id_for(tree_obj)
    tree_obj.is_dynamic = True

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


def item(title, url, children=None, url_as_pattern=True, hint='', alias='', description='',
         in_menu=True, in_breadcrumbs=True, in_sitetree=True,
         access_loggedin=False, access_guest=False,
         access_by_perms=None, perms_mode_all=True, **kwargs):
    """Dynamically creates and returns a sitetree item object.

    :param str|unicode title:
    :param str|unicode url:
    :param list, set children: a list of children for tree item. Children should also be created by `item` function.
    :param bool url_as_pattern: consider URL as a name of a named URL
    :param str|unicode hint: hints are usually shown to users
    :param str|unicode alias: item name to address it from templates
    :param str|unicode description: additional information on item (usually is not shown to users)
    :param bool in_menu: show this item in menus
    :param bool in_breadcrumbs: show this item in breadcrumbs
    :param bool in_sitetree: show this item in sitetrees
    :param bool access_loggedin: show item to logged in users only
    :param bool access_guest: show item to guest users only
    :param list|str||unicode|int, Permission access_by_perms: restrict access to users with these permissions
    :param bool perms_mode_all: permissions set interpretation rule:
                True - user should have all the permissions;
                False - user should have any of chosen permissions.
    :rtype: TreeItemBase
    """
    item_obj = get_tree_item_model()(title=title, url=url, urlaspattern=url_as_pattern,
                                   hint=hint, alias=alias, description=description, inmenu=in_menu,
                                   insitetree=in_sitetree, inbreadcrumbs=in_breadcrumbs,
                                   access_loggedin=access_loggedin, access_guest=access_guest, **kwargs)

    item_obj.id = generate_id_for(item_obj)
    item_obj.is_dynamic = True
    item_obj.dynamic_children = []

    cleaned_permissions = []
    if access_by_perms:
        # Make permissions a list if currently a single object
        if not isinstance(access_by_perms, list):
            access_by_perms = [access_by_perms]

        for perm in access_by_perms:
            if isinstance(perm, six.string_types):
                # Get permission object from string
                try:
                    app, codename = perm.split('.')
                except ValueError:
                    raise ValueError(
                        'Wrong permission string format: supplied - `%s`; '
                        'expected - `<app_name>.<permission_name>`.' % perm)

                try:
                    perm = Permission.objects.get(codename=codename, content_type__app_label=app)
                except Permission.DoesNotExist:
                    raise ValueError('Permission `%s.%s` does not exist.' % (app, codename))

            elif not isinstance(perm, (int, Permission)):
                raise ValueError('Permissions must be given as strings, ints, or `Permission` instances.')

            cleaned_permissions.append(perm)

    item_obj.permissions = cleaned_permissions or []
    item_obj.access_perm_type = item_obj.PERM_TYPE_ALL if perms_mode_all else item_obj.PERM_TYPE_ANY

    if item_obj.permissions:
        item_obj.access_restricted = True

    if children is not None:
        for child in children:
            child.parent = item_obj
            item_obj.dynamic_children.append(child)

    return item_obj


def import_app_sitetree_module(app):
    """Imports sitetree module from a given app.

    :param str|unicode app: Application name
    :return: module|None
    """
    module_name = settings.APP_MODULE_NAME
    module = import_module(app)
    try:
        sub_module = import_module('%s.%s' % (app, module_name))
        return sub_module
    except ImportError:
        if module_has_submodule(module, module_name):
            raise
        return None


def import_project_sitetree_modules():
    """Imports sitetrees modules from packages (apps).
    Returns a list of submodules.

    :rtype: list
    """
    from django.conf import settings as django_settings
    submodules = []
    for app in django_settings.INSTALLED_APPS:
        module = import_app_sitetree_module(app)
        if module is not None:
            submodules.append(module)
    return submodules


def get_app_n_model(settings_entry_name):
    """Returns tuple with application and tree[item] model class names.

    :param str|unicode settings_entry_name:
    :rtype: tuple
    """
    try:
        app_name, model_name = getattr(settings, settings_entry_name).split('.')
    except ValueError:
        raise ImproperlyConfigured(
            '`SITETREE_%s` must have the following format: `app_name.model_name`.' % settings_entry_name)
    return app_name, model_name


def get_model_class(settings_entry_name):
    """Returns a certain sitetree model as defined in the project settings.

    :param str|unicode settings_entry_name:
    :rtype: TreeItemBase|TreeBase
    """
    app_name, model_name = get_app_n_model(settings_entry_name)
    if apps_get_model is None:
        model = get_model(app_name, model_name)
    else:
        try:
            model = apps_get_model(app_name, model_name)
        except (LookupError, ValueError):
            model = None

    if model is None:
        raise ImproperlyConfigured(
            '`SITETREE_%s` refers to model `%s` that has not been installed.' % (settings_entry_name, model_name))

    return model


def get_tree_model():
    """Returns the Tree model, set for the project.

    :rtype: TreeBase
    """
    return get_model_class('MODEL_TREE')


def get_tree_item_model():
    """Returns the TreeItem model, set for the project.

    :rtype: TreeItemBase
    """
    return get_model_class('MODEL_TREE_ITEM')
