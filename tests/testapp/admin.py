from sitetree.admin import TreeItemAdmin, TreeAdmin, override_tree_admin, override_item_admin


class CustomTreeAdmin(TreeAdmin):
    pass


class CustomTreeItemAdmin(TreeItemAdmin):
    pass


override_tree_admin(CustomTreeAdmin)
override_item_admin(CustomTreeItemAdmin)
