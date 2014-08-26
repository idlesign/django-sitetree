from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

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
    `items` - dynamic sitetree items objects created by `item` function.

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


def item(title, url, children=None, url_as_pattern=True, hint='', alias='', description='', in_menu=True, in_breadcrumbs=True, in_sitetree=True, access_loggedin=False, access_guest=False, permissions=None, perm_any=True, access_restricted=False):
    """Dynamically creates and returns a sitetree item object.
    `children` - a list of children for tree item. Children should also be created by `item` function.

    """
    item_obj = get_tree_item_model()(title=title, url=url, urlaspattern=url_as_pattern,
                                   hint=hint, alias=alias, description=description, inmenu=in_menu,
                                   insitetree=in_sitetree, inbreadcrumbs=in_breadcrumbs,
                                   access_loggedin=access_loggedin, access_guest=access_guest)
    item_obj.id = generate_id_for(item_obj)
    item_obj.is_dynamic = True
    item_obj.dynamic_children = []

    # Clean the permissions (convert strings to Permission objects), and
    # save to item_obj.permissions.
    # `management.commands.sitetree_resync_apps` will copy
    # item_obj.permissions to item_obj.access_permissions once item_obj
    # has been saved
    cleaned_permissions = []
    if permissions:
        # Make permissions a list if currently a single object
        if type(permissions) != list:
            permissions = [permissions]
        for perm in permissions:
            if type(perm) == str or type(perm) == unicode:
                # Get permission object from string
                perm_split = perm.split(".")
                if len(perm_split) != 2:
                    raise ValueError(
                        "Permission string must be in format"
                        "`<app label>.<permission codename>`, was instead {}"\
                            .format(perm))
                app_label = perm_split[0]
                codename = perm_split[1]
                try:
                    perm = Permission.objects.get(
                        codename=codename, content_type__app_label=app_label)
                except Permission.DoesNotExist:
                    raise ValueError(
                        "Permission `{0}.{1}` does not exist"
                            .format(app_label, codename))
            elif type(perm) not in [int, Permission]:
                raise ValueError(
                    "Permissions must be given as strings, ints, or Permission"
                    " instances")
            cleaned_permissions.append(perm)
    item_obj.permissions = cleaned_permissions or []

    # access_restricted may be True, False or None. If T/F, the field is
    # to that value. If None, the field is set to True if permissions
    # have been specified, and other False.
    if type(access_restricted) == bool:
        item_obj.access_restricted = access_restricted
    elif access_restricted is None:
        item_obj.access_restricted = bool(cleaned_permissions)
    else:
        raise ValueError("access_restricted must be True, False or None")

    # Set access_perm_type based on perm_any
    item_obj.access_perm_type = item_obj.PERM_TYPE_ANY if perm_any else \
        item_obj.PERM_TYPE_ALL

    if children is not None:
        for child in children:
            child.parent = item_obj
            item_obj.dynamic_children.append(child)
    return item_obj


def import_app_sitetree_module(app):
    """Imports sitetree module from a given app."""
    module_name = settings.APP_MODULE_NAME
    module = import_module(app)
    try:
        sub_module = import_module('%s.%s' % (app, module_name))
        return sub_module
    except:
        if module_has_submodule(module, module_name):
            raise
        return None


def import_project_sitetree_modules():
    """Imports sitetrees modules from packages (apps)."""
    from django.conf import settings as django_settings
    submodules = []
    for app in django_settings.INSTALLED_APPS:
        module = import_app_sitetree_module(app)
        if module is not None:
            submodules.append(module)
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
    if apps_get_model is None:
        model = get_model(app_name, model_name)
    else:
        try:
            model = apps_get_model(app_name, model_name)
        except (LookupError, ValueError):
            model = None

    if model is None:
        raise ImproperlyConfigured('`SITETREE_%s` refers to model `%s` that has not been installed.' % (settings_entry_name, model_name))

    return model


def get_tree_model():
    """Returns the Tree model, set for the project."""
    return get_model_class('MODEL_TREE')


def get_tree_item_model():
    """Returns the TreeItem model, set for the project."""
    return get_model_class('MODEL_TREE_ITEM')
