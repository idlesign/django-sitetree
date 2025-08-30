from sitetree.admin import TreeAdmin, TreeItemAdmin, override_item_admin, override_tree_admin


class CustomTreeAdmin(TreeAdmin):
    pass


class CustomTreeItemAdmin(TreeItemAdmin):
    pass


override_tree_admin(CustomTreeAdmin)
override_item_admin(CustomTreeItemAdmin)
