SiteTree template tags
======================

To use template tags available in SiteTree you should add **{% load sitetree %}** tag to the top of chosen template.

Tree tag argument (part in double quotes, following '**from**' word) of SiteTree tags should containt tree alias.

**Hints:**

  + Tree tag argument could be a template variable (do not use quotes for those).
  + Optional **template** argument could be supplied to all SitetTree tags except *sitetree_page_title* to render using different templates.
    It should contain path to template file.

    Examples::

    {% sitetree_menu from "mytree" include "trunk,topmenu" template "mytrees/mymenu.html" %}
    {% sitetree_breadcrumbs from "mytree" template "mytrees/mybreadcrumbs.html" %}



.. _tag-menu:

sitetree_menu
-------------

This tag renders menu based on sitetree.

Usage example::

{% sitetree_menu from "mytree" include "trunk,topmenu" %}

This command renders as a menu sitetree items from tree named 'mytree', including items **under** 'trunk' and 'topmenu' aliased items.
That means that 'trunk' and 'topmenu' themselves won't appear in a menu, but rather all their ancestors. If you need item filtering behaviour
please use :ref:`tree hooks <tree-hooks>`.

  Aliases are given to items through Django's admin site.

  `Note that there are some reserved aliases`. To illustrate how do they work, take a look at the sample tree::

      Home
      |-- Users
      |   |-- Moderators
      |   |-- Ordinary
      |
      |-- Articles
      |   |-- About cats
      |   |     |-- Good
      |   |     |-- Bad
      |   |     |-- Ugly
      |   |
      |   |-- About dogs
      |   |-- About mice
      |
      |-- Contacts
      |   |-- Russia
      |   |     |-- Web
      |   |     |     |-- Public
      |   |     |     |-- Private
      |   |     |
      |   |     |-- Postal
      |   |
      |   |-- Australia
      |   |-- China
      Exit


  .. note::

        As it mentioned above, basic built-in templates won't limit the depth of rendered tree, if you need to render
        the limited number of levels, you ought to :ref:`override the built-in templates <overriding-built-in-templates>`.
        For brevity rendering examples below will show only top level rendered for each alias.

  + **trunk** - get hierarchy under trunk, i.e. root item(s) - items without parents:

    Renders::

      Home
      Exit

  + **this-children** - get items under item resolved as current for the current page;

    Considering that we are now at `Articles` renders::

      About cats
      About dogs
      About mice

  + **this-siblings** - get items under parent of item resolved as current for the current page (current item included);

    Considering that we are now at `Bad` renders::

      Good
      Bad
      Ugly

  + **this-parent-siblings** - items under parent item for the item resolved as current for the current page.

    Considering that we are now at `Public` renders::

      Web
      Postal

  + **this-ancestor-children** - items under grandparent item (closest to root) for the item resolved as current for the current page.

    Considering that we are now at `Public` renders all items under `Home` (which is closest to the root).

  Thus in the template tag example above `trunk` is reserved alias, and `topmenu` alias is given to an item through
  admin site.

Sitetree items could be addressed not only by aliases but also by IDs::

  {% sitetree_menu from "mytree" include "10" %}



.. _tag-breadcrumbs:

sitetree_breadcrumbs
--------------------

This tag renders breadcrumbs path (from tree root to current page) based on sitetree.

Usage example::

  {% sitetree_breadcrumbs from "mytree" %}

This command renders breadcrumbs from tree named 'mytree'.



.. _tag-tree:

sitetree_tree
-------------

This tag renders entire site tree.

Usage example::

  {% sitetree_tree from "mytree" %}

This command renders sitetree from tree named 'mytree'.



.. _tag-page-title:

sitetree_page_title
-------------------

This tag renders current page title resolved against definite sitetree. Title is taken from a sitetree item title resolved as current for the current page.

Usage example::

  {% sitetree_page_title from "mytree" %}

This command renders current page title from tree named 'mytree'.



.. _tag-page-description:

sitetree_page_description
-------------------------

This tag renders current page description resolved against definite sitetree. Description is taken from a sitetree item description resolved as current for the current page.

That can be useful for meta description for an HTML page.

Usage example::

  {% sitetree_page_description from "mytree" %}

This command renders current page description from tree named 'mytree'.


.. _tag-page-hint:

sitetree_page_hint
------------------

This tag is similar to `sitetree_page_description`, but it uses data from  tree item `hint` field instead of a `description` fields.

Usage example::

  {% sitetree_page_hint from "mytree" %}



.. _tag-ignore-errors:

SITETREE_RAISE_ITEMS_ERRORS_ON_DEBUG
------------------------------------

DEFAULT: True

There are some rare occasions when you want to turn off errors that are thrown by sitetree even during debug.

Setting SITETREE_RAISE_ITEMS_ERRORS_ON_DEBUG = False will turn them off.