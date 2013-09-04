Shipping sitetrees with your apps
=================================

SiteTree allows you to define sitetrees within your apps.


Defining a sitetree
-------------------

Let's suppose you have `books` application and want do define a sitetree for it.

* First create `sitetree.py` in the directory of `books` app.

* Then define a sitetree with the help of `tree` and `item` functions from `sitetree.utils` module
  and assign it to `sitetrees` module attribute::


      from sitetree.utils import tree, item

      # Be sure you defined `sitetrees` in your module.
      sitetrees = (
          # Define a tree with `tree` function.
          tree('books', items=[
              # Then define items and their children with `item` function.
              item('Books', 'books-listing', children=[
                  item('Book named "{{ book.title }}"', 'books-details', in_menu=False, in_sitetree=False),
                  item('Add a book', 'books-add'),
                  item('Edit "{{ book.title }}"', 'books-edit', in_menu=False, in_sitetree=False)
              ])
          ]),
          # ... You can define more than one tree for your app.
      )


  Please consider `tree` and `item` signatures for possible options.


Export sitetree to DB
---------------------

Now when your app has a defined sitetree you can use `sitetree_resync_apps` management command
to instantly move sitetrees from every (or certain) applications into DB::

  python manage.py sitetree_resync_apps


Or solely for `books` application::

  python manage.py sitetree_resync_apps books

