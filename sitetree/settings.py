from django.conf import settings


MODEL_TREE = getattr(settings, 'SITETREE_MODEL_TREE', 'sitetree.Tree')
"""Path to a tree model (app.class)."""

MODEL_TREE_ITEM = getattr(settings, 'SITETREE_MODEL_TREE_ITEM', 'sitetree.TreeItem')
"""Path to a tree item model (app.class)."""

APP_MODULE_NAME = getattr(settings, 'SITETREE_APP_MODULE_NAME', 'sitetrees')
"""Module name where applications store trees shipped with them."""

UNRESOLVED_ITEM_MARKER = getattr(settings, 'SITETREE_UNRESOLVED_ITEM_MARKER', u'#unresolved')
"""This string is place instead of item URL if actual URL cannot be resolved."""

RAISE_ITEMS_ERRORS_ON_DEBUG = getattr(settings, 'SITETREE_RAISE_ITEMS_ERRORS_ON_DEBUG', True)

ITEMS_FIELD_ROOT_ID = getattr(settings, 'SITETREE_ITEMS_FIELD_ROOT_ID', '')
"""Item ID to be used for root item in TreeItemChoiceField.
This is adjustable to be able to workaround client-side field validation issues in thirdparties.

"""

CACHE_TIMEOUT = getattr(settings, 'SITETREE_CACHE_TIMEOUT', 31536000)
"""Sitetree objects are stored in Django cache for a year (60 * 60 * 24 * 365 = 31536000 sec).
Cache is only invalidated on sitetree or sitetree item change.

"""

# Reserved tree items aliases.
ALIAS_TRUNK = 'trunk'
ALIAS_THIS_CHILDREN = 'this-children'
ALIAS_THIS_SIBLINGS = 'this-siblings'
ALIAS_THIS_ANCESTOR_CHILDREN = 'this-ancestor-children'
ALIAS_THIS_PARENT_SIBLINGS = 'this-parent-siblings'

TREE_ITEMS_ALIASES = [
    ALIAS_TRUNK,
    ALIAS_THIS_CHILDREN,
    ALIAS_THIS_SIBLINGS,
    ALIAS_THIS_ANCESTOR_CHILDREN,
    ALIAS_THIS_PARENT_SIBLINGS
]
