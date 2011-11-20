Tree hooks
==========

What to do if a time comes and you need some fancy stuff done to tree items that
django-sitetree does not support?

It might be that you need some special tree items ordering in a menu, or you want to render
in a huge site tree with all articles titles that are described by one tree item in Django admin,
or god knowns what else.

django-sitetree can facilitate on that as it comes with ``register_items_hook(callable)``
function which registers a hook callable to process tree items right before they are passed
to templates.

Note that callable should be able to:

    a) handle ``tree_items`` and ``tree_sender`` key params.
        ``tree_items`` will contain a list of extended TreeItem objects ready to pass to template.

        ``tree_sender`` will contain navigation type identifier (e.g.: `menu`, `sitetree`, `breadcrumbs`, `menu.children`, `sitetree.children`)

    b) return a list of extended TreeItems objects to pass to template.


Example::

    # First import the register function.
    from sitetree.sitetreeapp import register_items_hook

    # The following function will be used as items processor.
    def my_items_processor(tree_items, tree_sender):
        # Suppose we want to process only menu child items.
        if tree_sender == 'menu.children':
            # Lets add 'Hooked: ' to resolved titles of every item.
            for item in tree_items:
                item.title_resolved = 'Hooked: %s' % item.title_resolved
        # Return items list mutated or not.
        return tree_items

    # And we register items processor.
    register_items_hook(my_items_processor)
    
