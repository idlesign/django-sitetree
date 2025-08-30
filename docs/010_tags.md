# Template tags

To use template tags available in SiteTree you should add `{% load sitetree %}` tag to the top of chosen template.

Tree tag argument (part in double quotes, following `from` word) of SiteTree tags should contain the tree alias.

!!! hint

    + Tree tag argument could be a template variable (do not use quotes for those).
     
    + Optional `template` argument could be supplied to all SitetTree tags except *sitetree_page_title* to render using different templates.
    It should contain path to template file.

    !!! example

        ```
        {% sitetree_menu from "mytree" include "trunk,topmenu" template "mytrees/mymenu.html" %}
        {% sitetree_breadcrumbs from "mytree" template "mytrees/mybreadcrumbs.html" %}
        ```

## sitetree_menu

This tag renders menu based on sitetree.

!!! example
    ```
    {% sitetree_menu from "mytree" include "trunk,topmenu" %}
    ```

This command renders as a menu sitetree items from tree named `mytree`, including items **under** `trunk` and `topmenu` aliased items.

That means that `trunk` and `topmenu` themselves won't appear in a menu, but rather all their ancestors.

!!! hint
    If you need item filtering behaviour consider using a customized tree handler.

Aliases are given to items through Django's admin site.

### Reserved aliases

Note that there are some reserved aliases. To illustrate how do they work, take a look at the sample tree:

```
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
```

!!! note
    As it mentioned above, basic built-in templates won't limit the depth of rendered tree, if you need to render
    the limited number of levels, you ought to override the built-in templates.
    For brevity rendering examples below will show only top levels rendered for each alias.

#### trunk 

Get hierarchy under trunk, i.e. root item(s) - items without parents:
```
Home
Exit
```

#### this-children

Get items under item resolved as current for the current page.

Considering that we are now at `Articles` renders:
```
About cats
About dogs
About mice
```

#### this-siblings

Get items under parent of item resolved as current for the current page (current item included).

Considering that we are now at `Bad` renders:
```
Good
Bad
Ugly
```

#### this-parent-siblings

Items under parent item for the item resolved as current for the current page.

Considering that we are now at `Public` renders::
```
Web
Postal
```

#### this-ancestor-children

Items under grandparent item (closest to root) for the item resolved as current for the current page.

Considering that we are now at `Public` renders all items under `Home` (which is closest to the root).
Thus, in the template tag example above `trunk` is reserved alias, and `topmenu` alias is given to an item through the admin site.

!!! note
    Sitetree items could be addressed not only by aliases but also by IDs::

    !!! example
        ```
        {% sitetree_menu from "mytree" include "10" %}
        ```

## sitetree_breadcrumbs

This tag renders breadcrumbs path (from tree root to current page) based on sitetree.

!!! example
    ```
    {% sitetree_breadcrumbs from "mytree" %}
    ```

This command renders breadcrumbs from tree named `mytree`.

## sitetree_tree

This tag renders entire site tree.
 
!!! example
    ```
    {% sitetree_tree from "mytree" %}
    ```
This command renders sitetree from tree named `mytree`.


## sitetree_page_title

This tag renders current page title resolved against definite sitetree. 
The title is taken from a sitetree item title resolved as current for the current page.

!!! example
    ```
    {% sitetree_page_title from "mytree" %}
    ```

This command renders current page title from tree named `mytree`.

## sitetree_page_description

This tag renders current page description resolved against definite sitetree. 
The description is taken from a sitetree item description resolved as current for the current page.

That can be useful for meta description for an HTML page.

!!! example
    ```
    {% sitetree_page_description from "mytree" %}
    ```

This command renders current page description from tree named `mytree`.


## sitetree_page_hint

This tag is similar to `sitetree_page_description`, but it uses data from 
tree item `hint` field instead of a `description` fields.

!!! example
    ```
    {% sitetree_page_hint from "mytree" %}
    ```

## Settings

### SITETREE_RAISE_ITEMS_ERRORS_ON_DEBUG

DEFAULT: `True`

There are some rare occasions when you want to turn off errors that are thrown by sitetree even during debug.

Setting `SITETREE_RAISE_ITEMS_ERRORS_ON_DEBUG = False` will turn them off.
