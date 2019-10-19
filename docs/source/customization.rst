Tree handler customization
==========================

What to do if a time comes and you need some fancy stuff done to tree items that
*django-sitetree* does not support?

.. _tree-custom:

It might be that you need some special tree items ordering in a menu, or you want to render
a huge site tree with all articles titles that are described by one tree item in Django admin,
or god knows what else.

*django-sitetree* can facilitate on that as it allows tree handler customization
with the help of `SITETREE_CLS` setting.

1. Subclass ``sitetreeapp.SiteTree`` and place that class into a separate module for convenience.
2. You may now override ``.apply_hook()`` to manipulate tree items before render, or any other method to customize handler to your exact needs.
3. Define ``SITETREE_CLS`` in ``settings.py`` of your project, showing it a dotted path to the subclass.


Example:

.. code-block:: python

    # myapp/mysitetree.py
    from sitetree.sitetreeapp import SiteTree


    class MySiteTree(SiteTree):
        """Custom tree handler to test deep customization abilities."""

        def apply_hook(self, items, sender):
            # Suppose we want to process only menu child items.
            if tree_sender == 'menu.children':
                # Lets add 'Hooked: ' to resolved titles of every item.
                for item in tree_items:
                    item.title_resolved = 'Hooked: %s' % item.title_resolved
            # Return items list mutated or not.
            return tree_items

    # pyproject/settings.py
    ...

    SITETREE_CLS = 'myapp.mysitetree.MySiteTree'

    ...



.. note::

    You might also be interested in the notes on :ref:`Overriding SiteTree Admin representation <admin-ext>`.
