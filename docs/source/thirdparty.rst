Thirdparty applications support
===============================

Here belongs some notes on thirdparty Django applications support in SiteTree.



django-smuggler
---------------

https://pypi.python.org/pypi/django-smuggler/

`Smuggler` dump and load buttons will be available on trees listing page if this app is installed
allowing to dump and load site trees and items right from your browser.



django-modeltranslation
-----------------------

https://pypi.python.org/pypi/django-modeltranslation/

If you do not want to use the built-in `sitetree` Internationalization machinery, with `modeltranslation` you can
localize your tree items into different languages. This requires some work though.

1. Create a custom sitetree item model:


.. code-block:: python

    # models.py of some of your apps (e.g. myapp).
    from sitetree.models import TreeItemBase


    class MyTranslatableTreeItem(TreeItemBase):
        """This model will be used by modeltranslation."""


2. Instruct Django to use your custom model:

.. code-block:: python

    # setting.py of your project.
    SITETREE_MODEL_TREE_ITEM = 'myapp.MyTreeItem'


3. Tune up Admin contrib to handle translatable tree items:

.. code-block:: python

    # admin.py of your application with translatable tree item model.
    from modeltranslation.admin import TranslationAdmin
    from sitetree.admin import TreeItemAdmin, override_item_admin


    class CustomTreeItemAdmin(TreeItemAdmin, TranslationAdmin):
        """This allows admin contrib to support translations for tree items."""

    override_item_admin(CustomTreeItemAdmin)


4. Instruct `modeltranslation` how to handle your tree item model:

.. code-block:: python

    # translation.py of your application.
    from modeltranslation.translator import translator, TranslationOptions

    from .models import MyTranslatableTreeItem


    class TreeItemTranslationOptions(TranslationOptions):

        # These fields are for translation.
        fields = ('title', 'hint', 'description')


    translator.register(MyTreeItem, TreeItemTranslationOptions)


That's how you made `sitetree` work with `modeltranslation`.

Read `django-modeltranslation` documentation for more information on tuning.
