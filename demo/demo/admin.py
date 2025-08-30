
from django.contrib import admin

from .models import Article

admin.site.register(Article)


customized_sitetree_admin = False

if customized_sitetree_admin:

    from sitetree.admin import TreeAdmin, TreeItemAdmin, override_item_admin, override_tree_admin

    class CustomTreeItemAdmin(TreeItemAdmin):

        fieldsets = None


    class CustomTreeAdmin(TreeAdmin):

        exclude = ('title',)

    override_item_admin(CustomTreeItemAdmin)
    override_tree_admin(CustomTreeAdmin)
