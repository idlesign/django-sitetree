Overriding SiteTree Admin representation
========================================

SiteTree allows you to override tree and tree item representation in Django Admin interface.

That could be used not only for the purpose of enhancement of visual design but also
for integration with other applications, using admin inlines.

.. _admin-ext:


The following functions from `sitetree.admin` could be used to override tree and tree item representation:

    * `override_tree_admin()` is used to customize tree representation.
    * `override_item_admin()` is used to customize tree item representation.


Example::

    # Supposing we are in admin.py of your own application.

    # Import two helper functions and two admin models to inherit our custom model from.
    from sitetree.admin import TreeItemAdmin, TreeAdmin, override_tree_admin, override_item_admin

    # This is our custom tree admin model.
    class CustomTreeAdmin(TreeAdmin):
        exclude = ('title',)  # Here we exclude `title` field from form.

    # And our custom tree item admin model.
    class CustomTreeItemAdmin(TreeItemAdmin):
        # That will turn a tree item representation from the default variant
        # with collapsible groupings into a flat one.
        fieldsets= None

    # Now we tell the SiteTree to replace generic representations with custom.
    override_tree_admin(CustomTreeAdmin)
    override_item_admin(CustomTreeItemAdmin)
    

.. note::

    You might also be interested in using :ref:`Tree hooks <tree-hooks>`.


Inlines override example
------------------------

In the example below we'll use django-seo application from https://github.com/willhardy/django-seo

According to django-seo documentation it allows an addition of custom metadata fields to your models,
so we use it to connect metadata to sitetree items.

That's how one might render django-seo inline form on sitetree item create and edit pages::

    from rollyourown.seo.admin import get_inline
    from sitetree.admin import TreeItemAdmin, TreeAdmin, override_tree_admin, override_item_admin
    # Let's suppose our application contains seo.py with django-seo metadata class defined.
    from myapp.seo import CustomMeta


    class CustomTreeItemAdmin(TreeItemAdmin):
        inlines = [get_inline(CustomMeta)]

    override_item_admin(CustomTreeItemAdmin)

