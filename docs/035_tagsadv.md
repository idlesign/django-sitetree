# Advanced template tags

SiteTree introduces two advanced template tags which you have to deal with in case you override the built-in sitetree templates.


## sitetree_children

Implements down the tree traversal with rendering.

!!! example
    ```html
    {% sitetree_children of someitem for menu template "sitetree/mychildren.html" %}
    ```

Used to render child items of specific sitetree item `someitem` for `menu` navigation type, using template **sitetree/mychildren.html**.

Allowed navigation types:

1. **menu**
2. **sitetree**

Basically template argument should contain path to current template itself.


## sitetree_url

Resolves site tree item's url or url pattern.

!!! example
    ```html
    {% sitetree_url for someitem params %}
    ```

This tag is much the same as Django built-in `url` tag. The difference is that after `for` it should get site tree item object.

It can cast the resolved URL into a context variable when using `as` clause just like `url` tag.
