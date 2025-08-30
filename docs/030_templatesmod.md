# Built-in templates

Default templates shipped with SiteTree created to have as little markup as possible in a try to fit most common website need.


### Styling

Use CSS to style default templates for your needs. Templates are deliberately made simple, and only consist of **ul**, **li** and **a** tags.

Nevertheless, pay attention that menu template also uses two CSS classes marking tree items:

* **current_item** — marks item in the tree, corresponding to current page;
* **current_branch** — marks all ancestors of current item, and current item itself.

If needed, you can set extra CSS classes to the **ul** element with `extra_class_ul` variable. For example:
```html
{% with extra_class_ul="flex-wrap flex-row" %}
  {% sitetree_menu from "footer_3" include "trunk,topmenu" template "sitetree/menu_bootstrap5.html" %}
{% endwith %}
```

## Overriding

To customize visual representation of navigation elements you should override the built-in SiteTree templates as follows:

1. Switch to sitetree folder
2. Switch further to `templates/sitetree`
3. There among others you'll find the following templates:

    * `breadcrumbs.html` basic breadcrumbs
    * `breadcrumbs-title.html` breadcrumbs that can be put inside html `title` tag
    * `menu.html` basic menu
    * `tree.html` basic tree

4. Copy whichever of them you need into your project templates directory and feel free to customize it.
5. See section on advanced tags for clarification on two advanced SiteTree template tags.


## Templates for Frameworks

### Foundation

Information about Foundation Framework is available at <https://get.foundation/>

The following templates are bundled with SiteTree:

* `sitetree/breadcrumbs_foundation.html`

    This template can be used to construct a breadcrumb navigation from a sitetree.

* `sitetree/menu_foundation.html`

    This template can be used to construct Foundation Nav Bar (classic horizontal top menu) from a sitetree.

    !!! note
        The template renders no more than two levels of a tree with hover dropdowns for root items having children.

* `sitetree/menu_foundation-vertical.html`

    This template can be used to construct a vertical version of Foundation Nav Bar, suitable for sidebar navigation.

    !!! note
        The template renders no more than two levels of a tree with hover dropdowns for root items having children.

  * `sitetree/sitetree/menu_foundation_sidenav.html`

    This template can be used to construct a Foundation Side Nav.
    !!! note
        The template renders only one tree level.

!!! hint
    You can take a look at Foundation navigation elements examples at <https://get.foundation/sites/docs/menu.html>


### Bootstrap

Information about Bootstrap Framework is available at <https://getbootstrap.com>

The following templates are bundled with SiteTree:

* `sitetree/breadcrumbs_bootstrap.html`

    This template can be used to construct a breadcrumb navigation from a sitetree.

* `sitetree/breadcrumbs_bootstrap3.html`

    The same as above but for Bootstrap version 3.

* `sitetree/breadcrumbs_bootstrap4.html`

    The same as above but for Bootstrap version 4.

* `sitetree/menu_bootstrap.html`
  
    This template can be used to construct *menu contents* for Bootstrap Navbar.
  
    !!! warning
        To widen the number of possible use-cases for which this template can be applied,
        it renders only menu contents, but not Navbar container itself.

        This means that one should wrap `sitetree_menu` call into the appropriately styled divs
        (i.e. having classes `navbar`, `navbar-inner`, etc.).

        ```html
        <div class="navbar">
           <a class="brand" href="/">My Site</a>
           <div class="navbar-inner">
               {% sitetree_menu from "main" include "topmenu" template "sitetree/menu_bootstrap.html" %}
           </div>
        </div>
        ```
        Please see Bootstrap Navbar documentation for more information on subject.

    !!! note
        The template renders no more than two levels of a tree with hover dropdowns for root items having children.

* `sitetree/menu_bootstrap3.html`

    The same as above but for Bootstrap version 3.

* `sitetree/menu_bootstrap4.html`

    The same as above but for Bootstrap version 4.

* `sitetree/menu_bootstrap5.html`

    The same as above but for Bootstrap version 5.

* `sitetree/menu_bootstrap_dropdown.html`

    One level deep dropdown menu.

* `sitetree/menu_bootstrap3_dropdown.html`

    The same as above but for Bootstrap version 3.

* `sitetree/menu_bootstrap4_dropdown.html`

    The same as above but for Bootstrap version 4.

* `sitetree/menu_bootstrap5_dropdown.html`

    The same as above but for Bootstrap version 5.

* `sitetree/menu_bootstrap_navlist.html`

    This template can be used to construct a Bootstrap Nav list.

    !!! note
        The template renders only a single level.

* `sitetree/menu_bootstrap3_navpills.html`

    Constructs nav-pills Bootstrap 3 horizontal navigation.

* `sitetree/menu_bootstrap3_deep.html`

    Constructs Bootstrap 3 menu with infinite submenus.
    Requires adding extra CSS:

    ```html
     <link href="{% static "css/sitetree_bootstrap_submenu.css"%}" type="text/css" rel="stylesheet" media="screen">
    ```

* `sitetree/menu_bootstrap4_navpills.html`

    The same as above but for Bootstrap version 4.

* `sitetree/menu_bootstrap3_navpills-stacked.html`

    Constructs nav-pills Bootstrap 3 vertical navigation similar to navlist from Bootstrap 2.

* `sitetree/menu_bootstrap4_navpills-stacked.html`

    The same as above but for Bootstrap version 4.


You can find Bootstrap navigation elements examples at <https://getbootstrap.com/docs/5.3/components/navbar/>


### Semantic UI

Information about Semantic UI Framework is available at https://semantic-ui.com/

The following templates are bundled with SiteTree:

* `sitetree/breadcrumbs_semantic.html`

    This template can be used to construct a breadcrumb navigation from a sitetree.

* `sitetree/menu_semantic.html`

    This template can be used to construct Semantic Menu (classic horizontal top menu) from a sitetree.

    !!! warning
        To widen the number of possible use-cases for which this template can be applied,
        it renders only menu contents, but not the UI Menu container itself.

        This means that one should wrap `sitetree_menu` call into the appropriately styled divs
        (i.e. having `ui menu` classes).

       
        ```html
        <div class="ui menu">
           <a class="item" href="/">MY SITE</a>
           {% sitetree_menu from "main" include "topmenu" template "sitetree/menu_semantic.html" %}
         </div>
        ```

       Please see Semantic UI Menu documentation for more information on subject.
  
    !!! note
        The template renders no more than two levels of a tree with hover dropdowns for root items having children.


* `sitetree/menu_semantic-vertical.html`

    This template can be used to construct a vertical version of Semantic UI Menu, suitable for sidebar navigation.

    !!! note
        The template renders no more than two levels of a tree with hover dropdowns for root items having children.
