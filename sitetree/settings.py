from django.conf import settings


MODEL_TREE = getattr(settings, 'SITETREE_MODEL_TREE', 'sitetree.Tree')
MODEL_TREE_ITEM = getattr(settings, 'SITETREE_MODEL_TREE_ITEM', 'sitetree.TreeItem')

APP_MODULE_NAME = getattr(settings, 'SITETREE_APP_MODULE_NAME', 'sitetrees')

UNRESOLVED_ITEM_MARKER = getattr(settings, 'SITETREE_UNRESOLVED_ITEM_MARKER', u'#unresolved')

RAISE_ITEMS_ERRORS_ON_DEBUG = getattr(settings, 'SITETREE_RAISE_ITEMS_ERRORS_ON_DEBUG', True)

# Sitetree objects are stored in Django cache for a year (60 * 60 * 24 * 365 = 31536000 sec).
# Cache is only invalidated on sitetree or sitetree item change.
CACHE_TIMEOUT = getattr(settings, 'SITETREE_CACHE_TIMEOUT', 31536000)

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
