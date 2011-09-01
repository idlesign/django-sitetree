Notes on build-in templates
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
