SiteTree Forms and Fields
=========================

Ocasionally you may want to link some site entities (e.g. Polls, Articles) to certain sitetree items (as to categorize
them). You can achieve it with the help of generic forms and fields shipped with SiteTree.



.. _forms:

TreeItemForm
------------

You can inherit from that form to have a dropdown with tree items for a certain tree:

.. code-block:: python

    from sitetree.forms import TreeItemForm


    class MyTreeItemForm(TreeItemForm):
        """We inherit from TreeItemForm to allow user link some title to sitetree item.
        This form besides `title` field will have `tree_item` dropdown.

        """

        title = forms.CharField()

    # We instruct our form to work with `main` aliased sitetree.
    # And we set tree item with ID = 2 as initial.
    my_form = MyTreeItemForm(tree='main', tree_item=2)


You can also use a well known `initial={'tree_item': 2}` approach to set an initial sitetree item.

After that deal with that form just as usual.



.. _fields:

TreeItemChoiceField
-------------------

`TreeItemChoiceField` is what `TreeItemForm` uses internally to represent sitetree items dropdown,
and what used in Admin contrib on sitetree item create/edit pages.

You can inherit from it (and customized it) or use it as it is in your own forms:

.. code-block:: python

    from sitetree.fields import TreeItemChoiceField


    class MyField(TreeItemChoiceField):

        # We override template used to build select choices.
        template = 'my_templates/tree_combo.html'
        # And override root item representation.
        root_title = '-** Root item **-'


