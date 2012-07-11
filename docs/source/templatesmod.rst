Notes on built-in templates
===========================

Default templates shipped with SiteTree created to have as little markup as possible in a try to fit most common website need.


Styling built-in templates
--------------------------

Use CSS to style default templates for your needs. Templates are deliberately made simple, and only consist of *ul*, *li* and *a* tags.

Nevertheless pay attention that menu template also uses two CSS classes marking tree items:

  * **current_item** — marks item in the tree, corresponding to current page;
  * **current_branch** — marks all ancestors of current item, and current item itself.


Overriding built-in templates
-----------------------------

To customize visual representation of navigation elements you should override the built-in SiteTree templates as follows:

  1. Switch to sitetree folder
  2. Switch further to 'templates/sitetree'
  3. There you'll find the following templates:

    * breadcrumbs.html
    * menu.html
    * tree.html

  4. Copy whichever of them you need into your project templates directory and feel free to customize it.
  5. See :ref:`Advanced SiteTree tags section <tags-advanced>` for clarification on two advanced SiteTree template tags.


Templates for Foundation CSS Framework
--------------------------------------

*Information about Foundation CSS Framework is available at* http://foundation.zurb.com

The following templates are bundled with SiteTree:

 * `sitetree/menu_foundation.html`

   This template can be used to construct Foundation Nav Bar (classic horizontal top menu) from a sitetree.

   .. note::

        The template renders no more than two levels of a tree with hover dropdowns for root items having children.

 * `sitetree/menu_foundation-vertical.html`

   This template can be used to construct a vertical version of Foundation Nav Bar, suitable for sidebar navigation.

   .. note::

        The template renders no more than two levels of a tree with hover dropdowns for root items having children.

 * `sitetree/sitetree/menu_foundation_sidenav.html`

   This template can be used to construct a Foundation Side Nav.

   .. note::

        The template renders only one tree level.

You can take a look at Foundation navigation elements examples at http://foundation.zurb.com/docs/navigation.php


Templates for Bootstrap CSS Framework
-------------------------------------

*Information about Bootstrap CSS Framework is available at* http://twitter.github.com/bootstrap/

The following templates are bundled with SiteTree:

 * `sitetree/breadcrumbs_bootstrap.html`

   This template can be used to construct a breadcrumb navigation from a sitetree.

 * `sitetree/menu_bootstrap.html`

   This template can be used to construct *menu contents* for Boostrap Navbar.

   .. warning::

        To widen the number of possible use-cases for which this template can be applied,
        it renders only menu contents, but not Navbar container itself.

        This means that one should wrap `sitetree_menu` call into the appropriately styled divs
        (i.e. having classes `navbar`, `navbar-inner`, etc.).

        Please see Boostrap Navbar documentation for more information on subject.

   .. note::

        The template renders no more than two levels of a tree with hover dropdowns for root items having children.


 * `sitetree/menu_bootstrap_navlist.html`

   This template can be used to construct a Boostrap Nav list.

   .. note::

        The template renders only one tree level.

You can find Bootstrap navigation elements examples at http://twitter.github.com/bootstrap/components.html#navbar
