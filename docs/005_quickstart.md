# Getting started

1. Add the `sitetree` application to `INSTALLED_APPS` in your settings file (usually `settings.py`).
2. Check that `django.core.context_processors.request` is added to `TEMPLATE_CONTEXT_PROCESSORS` in your settings file.

    !!! note
        For Django 1.8+: it should be defined in `TEMPLATES/OPTIONS/context_processors`.

3. Check that `django.contrib.auth.context_processors.auth` is enabled in `TEMPLATE_CONTEXT_PROCESSORS` too.
4. Run `./manage.py migrate` to install sitetree tables into database.
5. Go to Django Admin site and add some trees and tree items.
6. Add `{% load sitetree %}` tag to the top of a template.


## Making a tree

Taken from [StackOverflow](http://stackoverflow.com/questions/4766807/how-to-use-django-sitetree/4887916#4887916).

In this tutorial we create a sitetree that could handle URI like `/categoryname/entryname`.

---

To create a tree:

!!! note
     Here we create a tree in Django admin. You can also define trees right in your code. See section on dynamic trees.

1. Go to site administration panel;
2. Click `+Add` near `Site Trees`;
3. Enter alias for your sitetree, e.g. `maintree`. You'll address your tree by this alias in template tags;
4. Push `Add Site Tree Item`;
5. Create the first item:

    * `Parent` - As it is root item that would have no parent.
    * `Title` - Let it be `My site`.
    * `URL` - This URL is static, so put here `/`.

6. Create a second item (that one would handle `categoryname` from your `categoryname/entryname`):

    * `Parent` - Choose `My site` item from step 5.
    * `Title` - Put here `Category #{{ category.id }}`.
    * `URL` - Put named URL `category-detailed category.name`.
    
    In `Additional settings`: check `URL as Pattern` checkbox.

7. Create a third item (that one would handle `entryname` from your `categoryname/entryname`):

    * `Parent` - Choose `Category #{{ category.id }}` item from step 6.
    * `Title` - Put here `Entry #{{ entry.id }}`.
    * `URL` - Put named URL `entry-detailed category.name entry.name`.

    In `Additional settings`: check `URL as Pattern` checkbox.

8. Put `{% load sitetree %}` into your template to have access to sitetree tags;
9. Put `{% sitetree_menu from "maintree" include "trunk" %}` into your template to render menu from tree trunk;
10. Put `{% sitetree_breadcrumbs from "maintree" %}` into your template to render breadcrumbs.

---

Steps 6 and 7 clarifications:

 * In titles we use Django template variables, which would be resolved just like they do in your templates.

    E.g.: You made your view for `categoryname` (let's call it 'detailed_category') to pass category object 
    into template as `category` variable. Suppose that category object has `id` property.
 
    In your template you use `{{ category.id }}` to render id. And we do just the same for site tree item in step 6.

* In URLs we use Django's named URL patterns ([documentation](http://docs.djangoproject.com/en/dev/topics/http/urls/#naming-url-patterns)). 
   That is almost identical to the usage of Django [url](http://docs.djangoproject.com/en/dev/ref/templates/builtins/#url) tag in templates. 

    Your urls configuration for steps 6, 7 supposed to include:
   
    ```python
    url(r'^(?P<category_name>\S+)/(?P<entry_name>\S+)/$', 'detailed_entry', name='entry-detailed'),
    url(r'^(?P<category_name>\S+)/$', 'detailed_category', name='category-detailed'),
    ```

    Take a not on `name` argument values.

So, putting `entry-detailed category.name entry.name` in step 7 into URL field we tell sitetree to associate 
that sitetree item with URL named `entry-detailed`, passing to it `category_name` and `entry_name` parameters.

Now you're ready to move to templates and use template tags.
