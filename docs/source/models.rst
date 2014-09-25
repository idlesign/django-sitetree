SiteTree Models
===============

SiteTree comes with Tree and Tree item built-in models to store sitetree data.


.. _models_customization:

Models customization
--------------------

Now let's pretend you are not satisfied with SiteTree built-in models and want to customize them.

1. First thing you should do is to define your own `tree` and `tree item` models inherited from `TreeBase`
and `TreeItemBase` classes respectively:

.. code-block:: python

    # Suppose you have `myapp` application.
    # In its `models.py` you define your customized models.
    from sitetree.models import TreeItemBase, TreeBase


    class MyTree(TreeBase):
        """This is your custom tree model.
        And here you add `my_tree_field` to all fields existing in `TreeBase`.

        """
        my_tree_field = models.CharField('My tree field', max_length=50, null=True, blank=True)


    class MyTreeItem(TreeItemBase):
        """And that's a tree item model with additional `css_class` field."""
        css_class = models.IntegerField('Tree item CSS class', default=50)



2. Now when `models.py` in your `myapp` application has the definitions of custom sitetree models, you need
to instruct Django to use them for your project instead of built-in ones:

.. code-block:: python

    # Somewhere in your settings.py do the following.
    # Here `myapp` is the name of your application, `MyTree` and `MyTreeItem`
    # are the names of your customized models.

    SITETREE_MODEL_TREE = 'myapp.MyTree'
    SITETREE_MODEL_TREE_ITEM = 'myapp.MyTreeItem'


3. Run `manage.py syncdb` to install your customized models into DB.


.. note::

    As you've added new fields to your models, you'll probably need to tune their Django Admin representation.
    See :ref:`Overriding SiteTree Admin representation <admin-ext>` for more information.




.. _models_referencing:

Models referencing
------------------

You can reference sitetree models (including customized) from other models, with the help
of `MODEL_TREE`, `MODEL_TREE_ITEM` settings:


.. code-block:: python

    from sitetree.settings import MODEL_TREE, MODEL_TREE_ITEM

    # As taken from the above given examples
    # MODEL_TREE will contain `myapp.MyTree`, MODEL_TREE_ITEM - `myapp.MyTreeItem`



If you need to get current `tree` or `tree item` classes use `get_tree_model` and `get_tree_item_model` functions:

.. code-block:: python

    from sitetree.utils import get_tree_model, get_tree_item_model

    current_tree_class = get_tree_model()  # MyTree from myapp.models (from the example above)
    current_tree_item_class = get_tree_item_model()  # MyTreeItem from myapp.models (from the example above)

