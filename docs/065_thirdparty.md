# Thirdparties

Here belongs some notes on thirdparty Django applications support in SiteTree.

## django-smuggler

<https://pypi.python.org/pypi/django-smuggler/>

`Smuggler` dump and load buttons will be available on trees listing page if this app is installed
allowing to dump and load site trees and items right from your browser.


## django-modeltranslation

<https://pypi.python.org/pypi/django-modeltranslation/>

If you do not want to use the built-in `sitetree` Internationalization machinery, with `modeltranslation` you can
localize your tree items into different languages. This requires some work though.

1. Create a custom sitetree item model:

    ```python title="myapp/models.py"
    from sitetree.models import TreeItemBase
    
    
    class MyTranslatableTreeItem(TreeItemBase):
        """This model will be used by modeltranslation."""
    ```

2. Instruct Django to use your custom model:

    ```python title="settings.py"
    SITETREE_MODEL_TREE_ITEM = 'myapp.MyTreeItem'
    ```

3. Tune up Admin contrib to handle translatable tree items:

    ```python title="admin.py"
    from modeltranslation.admin import TranslationAdmin
    from sitetree.admin import TreeItemAdmin, override_item_admin


    class CustomTreeItemAdmin(TreeItemAdmin, TranslationAdmin):
        """This allows admin contrib to support translations for tree items."""

    override_item_admin(CustomTreeItemAdmin)
    ```

4. Instruct `modeltranslation` how to handle your tree item model:

    ```python title="myapp/translation.py"
    from modeltranslation.translator import translator, TranslationOptions

    from .models import MyTranslatableTreeItem


    class TreeItemTranslationOptions(TranslationOptions):

        # These fields are for translation.
        fields = ('title', 'hint', 'description')


    translator.register(MyTreeItem, TreeItemTranslationOptions)
    ```

That's how you made `sitetree` work with `modeltranslation`.

Read `django-modeltranslation` documentation for more information on tuning.


## django-tenants

<https://pypi.python.org/pypi/django-tenants/>

You should use a custom cache config to make it work, configure something like this on the django cache.

```python title="settings.py"

CACHES = {
    ...
    "sitetree_cache": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        "KEY_FUNCTION": "django_tenants.cache.make_key",
        "REVERSE_KEY_FUNCTION": "django_tenants.cache.reverse_key",
    },
}

SITETREE_CACHE_NAME = "sitetree_cache"
```

