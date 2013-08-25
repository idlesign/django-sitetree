from django.conf import settings


MODEL_TREE = getattr(settings, 'SITETREE_MODEL_TREE', 'sitetree.Tree')
MODEL_TREE_ITEM = getattr(settings, 'SITETREE_MODEL_TREE_ITEM', 'sitetree.TreeItem')
