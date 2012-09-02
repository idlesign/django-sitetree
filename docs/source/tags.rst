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
That means that 'trunk' and 'topmenu' themselves won't appear in a menu, but rather their ancestors. If you need item filtering behaviour
please use :ref:`tree hooks <tree-hooks>`.

Aliases are given to items through Django's admin site.

`Note that there are some reserved aliases`. To illustrate how they work, let's take a look at this tree::

  Home
    |-- Users
          |-- Moderators
          |-- Ordinary
    
    |-- Articles
          |-- About cats
                |-- Good
                |-- Bad
                |-- Ugly
          |-- About dogs
          |-- About mice
    
    |-- Contacts
          |-- Russia
                |-- Web
                      |-- Public
                      |-- Private
                |-- Postal
          |-- Australia
          |-- China

+ **trunk** - trunk will render the hierachy under root item. 

  {% sitetree_menu from "mytree" include "trunk" %} renders::

    |-- Users
          |-- Moderators
          |-- Ordinary

    |-- Articles
          |-- About cats
                |-- Good
                |-- Bad
                |-- Ugly
          |-- About dogs
          |-- About mice
    
    |-- Contacts
          |-- Russia
                |-- Web
                      |-- Public
                      |-- Private
                |-- Postal
          |-- Australia
          |-- China

  If you want to render n levels, you ought to :ref:`override the built-in template <overriding-built-in-templates>`.


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

+ **this-ancestor-children** - items under grandparent item (closest to root) for the item resolved as current for the current page.

  Considering that we are now at `Public` renders::

    Web
    Postal

Thus in the template tag example above 'trunk' is reserved alias, and 'topmenu' alias is given to an item through
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

This tag renders current page title resolved against definite sitetree. Title is taken from sitetree item title resolved for current page.

Usage example::

{% sitetree_page_title from "mytree" %}

This command renders current page title from tree named 'mytree'.

