django-sitetree documentation
===============================

*django-sitetree is a reusable application for Django, introducing site tree, menu and breadcrumbs navigation elements.*

Site structure in django-sitetree is described through Django admin interface in a so called site trees.
Every item of such a tree describes a page or a set of pages through the relation of URI or URL to human-friendly title. Eg. using site tree editor in Django admin::

  URI             Title
    /             - Site Root
    |_users/      - Site Users
      |_users/13/ - Definite User


Alas the example above makes a little sense if you have more than just a few users, that's why django-sitetree supports Django template tags in item titles and Django named URLs in item URIs.

If we define a named URL for user personal page in urls.py, for example, 'users-personal', we could change a scheme in the following way::

  URI                           Title
    /                           - Site Root
    |_users/                    - Site Users
      |_users-personal user.id  - User Called {{ user.first_name }}

After setting up site structure as a sitetree you should be able to use convenient and highly customizable site navigation means (menus, breadcrumbs and full site trees).

User access to certain sitetree items can be restricted to authenticated users or more accurately with the help of Django permissions system (Auth contrib package).


Requirements
------------

1. Django 1.2+
2. Admin site Django contrib package
3. Auth Django contrib package
4. South 0.7.1+ for Django (required for version upgrades)


Table of Contents
-----------------

.. toctree::
    :maxdepth: 2

    quickstart
    tags
    i18n
    management
    templatesmod
    tagsadv
    hooks


Get involved into django-sitetree
---------------------------------

**Submit issues.** If you spotted something weird in application behavior or want to propose a feature you can do that at https://github.com/idlesign/django-sitetree/issues

**Write code.** If you are eager to participate in application development, fork it at https://github.com/idlesign/django-sitetree, write your code, whether it should be a bugfix or a feature implementation, and make a pull request right from the forked project page.

**Translate.** If want to translate the application into your native language use Transifex: https://www.transifex.net/projects/p/django-sitetree/.

**Spread the word.** If you have some tips and tricks or any other words in mind that you think might be of interest for the others — publish it.


The tip
-------

If the application is not what you want for site navigation, you might be interested in considering the other choices — http://djangopackages.com/grids/g/navigation/
