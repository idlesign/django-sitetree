SiteTree template tags
======================

To use template tags available in SiteTree you should add **{% load sitetree %}** tag to the top of chosen template.

Tree tag argument (part in double quotes, following '**from**' word) of SiteTree tags should containt tree alias.

**Hints:**

  + **NB:** Double quotes shown in tags examples below are nessesary.
  + Tree tag argument could be a template variable.
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

This command renders as a menu sitetree items from tree named 'mytree', including items under 'trunk' and 'topmenu' aliased items.

  Aliases are given to items through Django's admin site. Note that there are some reserved aliases.

  + **trunk** - get items without parents (root items);
  + **this-children** - get items under item resolved as current for the current page;
  + **this-siblings** - get items under parent of item resolved as current for the current page (current item included);
  + **this-ancestor-children** - items under grandparent item (closest to root) for the item resolved as current for the current page.

  Thus in the example above 'trunk' is reserved alias, and 'topmenu' alias is given to an item through admin site.

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

