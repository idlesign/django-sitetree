Getting started
===============

1. Add the **sitetree** application to INSTALLED_APPS in your settings file (usually 'settings.py').
2. Check that *django.core.context_processors.request* is enabled in TEMPLATE_CONTEXT_PROCESSORS in your settings file.
3. Check that *django.contrib.auth.context_processors.auth* is enabled in TEMPLATE_CONTEXT_PROCESSORS too.
4. Run './manage.py syncdb' to install sitetree tables into database.
5. Go to Django Admin site and add some trees and tree items (see :ref:`Making tree <making-tree>` section).
6. Add *{% load sitetree %}* tag to the top of a template.

Now you can use the following template tags:
  + :ref:`sitetree_menu <tag-menu>` - to render menu based on sitetree;
  + :ref:`sitetree_breadcrumbs <tag-breadcrumbs>` - to render breadcrumbs path based on sitetree;
  + :ref:`sitetree_tree <tag-tree>` - to render site tree;
  + :ref:`sitetree_page_title <tag-page-title>` - to render current page title resolved against definite sitetree.


Upgrade hint
------------

When switching from older version of SiteTree to newer do not forget to upgrade your database schema.

That could be done with the following command issued in your Django project directory::

./manage.py migrate

Note that the command **requires** `South <http://south.aeracode.org/>`_.



.. _making-tree:

Making tree
-----------

Taken from `StackOverflow <http://stackoverflow.com/questions/4766807/how-to-use-django-sitetree/4887916#4887916>`_.

In this tutoral we create sitetree that could handle URI like */categoryname/entryname*.

------------

To create a tree:

1. Go to site administration panel;
2. Click +Add near 'Site Trees';
3. Enter alias for your sitetree, e.g. 'maintree'. You'll address your tree by this alias in template tags;
4. Push 'Add Site Tree Item';
5. Create first item::

    Parent - As it is root item that would have no parent.
    Title - Let it be 'My site'.
    URL - This URL is static, so put here '/'.

6. Create second item (that one would handle 'categoryname' from your 'categoryname/entryname')::

    Parent - Choose 'My site' item from step 5.
    Title - Put here 'Category #{{ category.id }}'.
    URL - Put named URL 'category-detailed category.name'.
    
    In 'Additional settings': check 'URL as Pattern' checkbox.

7. Create third item (that one would handle 'entryname' from your 'categoryname/entryname')::

    Parent - Choose 'Category #{{ category.id }}' item from step 6.
    Title - Put here 'Entry #{{ entry.id }}'.
    URL - Put named URL 'entry-detailed category.name entry.name'.

    In 'Additional settings': check 'URL as Pattern' checkbox.

8. Put '{% load sitetree %}' into yor template to have access to sitetree tags.
9. Put '{% sitetree_menu from "maintree" %}' into your template to render menu.
10. Put '{% sitetree_breadcrumbs from "maintree" %}' into your template to render breadcrumbs.

------------

Steps 6 and 7 clarifications:

 * In titles we use Django template variables, which would be resolved just like they do in your templates.

   E.g.: You made your view for 'categoryname' (let's call it 'detailed_category') to pass category object into template as 'category' variable. Suppose that category object has 'id' property.
   In your template you use '{{ category.id }}' to render id. And we do just the same for site tree item in step 6.

 * In URLs we use Django's named URL patterns (`documentation <http://docs.djangoproject.com/en/dev/topics/http/urls/#naming-url-patterns>`_). That is almost idential to usage of Django '`url <http://docs.djangoproject.com/en/dev/ref/templates/builtins/#url>`_' tag in templates.

   Your urls configuration for steps 6, 7 supposed to include::

    url(r'^(?P<category_name>\S+)/(?P<entry_name>\S+)/$', 'detailed_entry', name='entry-detailed'),
    url(r'^(?P<category_name>\S+)/$', 'detailed_category', name='category-detailed'),

   Consider 'name' argument values of 'url' function.

   So, putting 'entry-detailed category.name entry.name' in step 7 into URL field we tell sitetree to associate that sitetree item with URL named 'entry-detailed', passing to it category_name and entry_name parameters.
