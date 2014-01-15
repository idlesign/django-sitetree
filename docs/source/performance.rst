Performance notes
=================


To avoid performance hits on large sitetrees try to simplify them, and/or reduce number of sitetree items:

* Restructure (unify) sitetree items where appropriate. E.g.::

      Home
      |-- Category "Photo"
      |   |-- Item "{{ item.title  }}"
      |
      |-- Category "Audio"
      |   |-- Item "{{ item.title  }}"
      |
      |-- etc.


  could be restructured into::

      Home
      |-- Category "{{ category.title }}"
      |   |-- Item "{{ item.title  }}"
      |
      |-- etc.


* Do not use ``URL as Pattern`` sitetree item option. Instead you may use hardcoded URLs.

* Do not use access permissions restrictions (access rights) where not required.

* Use Django templates caching machinery.
