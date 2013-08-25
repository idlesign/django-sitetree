from django import VERSION
from django.db.models import get_model
from django.core.exceptions import ImproperlyConfigured

import settings

DJANGO_VERSION_INT = int('%s%s%s' % VERSION[:3])


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
