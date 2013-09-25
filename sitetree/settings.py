from django.conf import settings


MODEL_TREE = getattr(settings, 'SITETREE_MODEL_TREE', 'sitetree.Tree')
MODEL_TREE_ITEM = getattr(settings, 'SITETREE_MODEL_TREE_ITEM', 'sitetree.TreeItem')

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
