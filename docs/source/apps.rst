Shipping sitetrees with your apps
=================================

SiteTree allows you to define sitetrees within your apps.


Defining a sitetree
-------------------

Let's suppose you have `books` application and want do define a sitetree for it.

* First create `sitetrees.py` in the directory of `books` app.

* Then define a sitetree with the help of `tree` and `item` functions from `sitetree.utils` module
  and assign it to `sitetrees` module attribute

.. code-block:: python

    from sitetree.utils import tree, item

    # Be sure you defined `sitetrees` in your module.
    sitetrees = (
      # Define a tree with `tree` function.
      tree('books', items=[
          # Then define items and their children with `item` function.
          item('Books', 'books-listing', children=[
              item('Book named "{{ book.title }}"', 'books-details', in_menu=False, in_sitetree=False),
              item('Add a book', 'books-add', access_by_perms=['booksapp.allow_add']),
              item('Edit "{{ book.title }}"', 'books-edit', in_menu=False, in_sitetree=False)
          ])
      ]),
      # ... You can define more than one tree for your app.
    )


Please see `tree` and `item` signatures for possible options.

.. note::

    If you added extra fields to the Tree and TreeItem models,
    then you can specify their values when instantiating `item` see :ref:`custom-model-sitetree`


Export sitetree to DB
---------------------

Now when your app has a defined sitetree you can use `sitetree_resync_apps` management command
to instantly move sitetrees from every (or certain) applications into DB::

  python manage.py sitetree_resync_apps


Or solely for `books` application::

  python manage.py sitetree_resync_apps books




Dynamic sitetree structuring
----------------------------

Optionally you can structure app-defined sitetrees into existing or new trees runtime.

Basically one should compose a dynamic tree with ``compose_dynamic_tree()`` and register it with ``register_dynamic_trees()``.

Let's suppose the following code somewhere where app registry is already created, e.g. ``config.ready()`` or even
in ``urls.py`` of your project.


.. code-block:: python

    from sitetree.sitetreeapp import register_dynamic_trees, compose_dynamic_tree
    from sitetree.utils import tree, item


    register_dynamic_trees(

        # Gather all the trees from `books`,
        compose_dynamic_tree('books'),

        # or gather all the trees from `books` and attach them to `main` tree root,
        compose_dynamic_tree('books', target_tree_alias='main'),

        # or gather all the trees from `books` and attach them to `for_books` aliased item in `main` tree,
        compose_dynamic_tree('books', target_tree_alias='main', parent_tree_item_alias='for_books'),

        # or even define a tree right at the process of registration.
        compose_dynamic_tree((
            tree('dynamic', items=(
                item('dynamic_1', 'dynamic_1_url', children=(
                    item('dynamic_1_sub_1', 'dynamic_1_sub_1_url'),
                )),
                item('dynamic_2', 'dynamic_2_url'),
            )),
        )),

        # Line below tells sitetree to drop and recreate cache, so that all newly registered
        # dynamic trees are rendered immediately.
        reset_cache=True
    )


.. note:: If you use only dynamic trees you can set ``SITETREE_DYNAMIC_ONLY = True`` to prevent the application
    from querying trees and items stored in DB.

