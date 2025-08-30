# django-sitetree changelog

### v1.18.0 [2023-12-24]
* ++ Dynamic trees: add 'dynamic_attrs' parameter support for item() (closes #313).
* ++ Dynamic trees: add support for user-defined tree item access checks (closes #314).
* ** Add missing migrations, check them during testing.
* ** Add QA for Python 3.11 and Django 5.0. Dropped QA for Python 3.6

### v1.17.3 [2022-09-06]
* ** Defined 'default_auto_field' in 'SiteTreeConfig'.

### v1.17.2 [2022-04-12]
* ** Fixed LazyTitle issues in Django 4.

### v1.17.1 [2021-12-18]
* ** Django 4.0 compatibility improved.

### v1.17.0 [2021-08-06]
* ++ Add 'extra_class_ul' variable to Bootstrap and Foundation templates.
* ++ Add Bootstrap 5 templates.
* ** Fixed 'sitetreedump' command (see #295).
* ** Fixed app config handling in INSTALLED_APPS (see #292).
* ** Permissions in dynamic item are now lazy evaluated (see #302).

### v1.16.0 [2020-10-12]
* ++ Introduced 'SITETREE_CACHE_NAME' setting.
* ** Fixed tree item resolution for URLs having special chars (see #288).
* ** Improved URL resolution performance.

### v1.15.2 [2020-08-05]
* ** Made Django 3.1 compatible.

### v1.15.1 [2020-06-27]
* ** Fix regression preventing LazyTitle to be restored from cache.

### v1.15.0 [2020-06-20]
* !! Dropped support for Django<2.0.
* !! Dropped support for Python 2 and 3.5.
* ** Updated German translation.

### v1.14.0 [2019-12-05]
* ++ Add Django 3.0 compatibility. Effectively deprecates Py2 support.

### v1.13.2 [2019-11-23]
* ** Fixed a regression in Admin not filtering Parent item choices (see #266).

### v1.13.1 [2019-10-19]
* ** Fixed customized exception handling template using sitetree masking initial exception.

### v1.13.0
* !! Deprecated 'register_items_hook()' function.
* !! Dropped QA for Django 1.7.
* !! Dropped QA for Python 2.
* !! Dropped QA for Python 3.4.
* ++ Added 'SITETREE_CLS' setting support for deep tree handler customizations.

### v1.12.0
* ++ 'register_items_hook()' can handle functions accepting 'context' argument.
* ++ Added SITETREE_ADMIN_APP_NAME setting support for custom admin apps.
* ++ Allow custom widget for parent field in admin.
* ++ Dynamic tree() function now accepts custom keyword arguments.
* ++ Improved suppport for national characters in URIs.
* ** Admin: fixed redirect on new item save (closes #231).

### v1.11.0
* ++ Improved Django 2.1 compatiblity.

### v1.10.0
* ++ Added Bootstrap 3 deep menu template (with nested dropdowns).
* ++ Added SITETREE_DYNAMIC_ONLY setting.
* ++ Japanese translation.

### v1.9.0
* ++ Added Bootstrap 4 templates.
* ** Dropped support for Python 2.6 and 3.3.
* ** Dropped Django<1.7 related code.
* ++ Added basic Django 2.0 compatibility.
* ++ Added French translation.
* ** Reduced number of SQL queries on item admin page (see #237)

### v1.8.0
* ++ IMPORTANT: i18n trees now support full lang names (e.g. de-ch, pt-br), update your i18n trees aliases.
* ++ Django 1.11 compatibility improvements.

### v1.7.0
* ** IMPORTANT: Caching reworked.
* ** IMPORTANT: Dropped Django 1.5, 1.6 support (will not be tested anymore).
* ++ Added `ITEMS_FIELD_ROOT_ID` setting (see #205).
* ** Reduced DB hits for trees with lots of permissions (see #213).
* ** Improved `sitetreeload` command py3 compatibility (see #209).
* ** Fixed `sitetreeload` unable to load some twisted tree structures (see #209).
* ** Fixed `sitetree_resync_apps` run without args.
* ** Fixed package distribution (see #222).

### v1.6.0
* ++ Prevent TreeItems from being their own parents (see #200).
* ++ Added `toolbox` module as API single entry point.
* ++ Added `exceptions` module.
* ** Django 1.10 compatibility improvements.
* ** Cache.reset() misbehavior fixed (closes #191).
* ** Fixed broken delete operation in admin for custom TreeItem (see #190).
* ** Reduced number of cache calls (see #194).

### v1.5.1
* ** Django 1.9 compatibility improvements.

### v1.5.0
* ++ Added Norwegian translation.
* ++ Added SITETREE_RAISE_ITEMS_ERRORS_ON_DEBUG setting (see #157).
* ++ Exposed SITETREE_CACHE_TIMEOUT setting.
* ++ Added `as` clause support for `sitetree_page_title`, `sitetree_page_description` and `sitetree_page_hint` template tags.
* ** Fixed cache problems when using sitetree_resync_apps  (see #135, #166).
* ** Fixed disappearing tree items for guests in Admin contrib (Django 1.8) (see #164).
* ** Fix deprecation warning in Django 1.8 (see #178).
* ** Fixed permissions check for dynamic tree items (see #165).

### v1.4.0
* ++ Introduced Django 1.8 support (see #152).
* ** Fixed extra spaces issue in breadcrumbs (closes #150).

### v1.3.0
* ++ Implemented `django-smuggler` thirdparty support.
* ++ Implemented `i18n_patterns` compatibility (closes #148).
* ** Fixed menu alias clash with context variable (closes #117).

### v1.2.1
* ** `{{ STATIC_URL }}` is replaced with `{% static %}` admin templates.
* ** Fixed `sitetreeload` management command compatibility with py3.
* ** Fixed `sitetreeload` management command compatibility with Django 1.7.

### v1.2.0
* ++ Added support for both South and Django 1.7 migrations.
* ++ `register_dynamic_trees()` now accepts `reset_cache` kwarg.

### v1.1.0
* ++ Django 1.7 ready.
* ++ `item()` now accepts `access_by_perms` and `perms_mode_all`.
* ** Fixed `SiteTreeError` for `TEMPLATE_CONTEXT_PROCESSORS` when not `DEBUG`.
* ** Fixed `this-siblings` item alias behavior.
* ** `register_dynamic_trees()` refactored to a less-brackets style.
* ** `LazyTitle` objects made py3 compatible.
* ** Fixed "Save and continue editing" on Tree Item yields "does not exist" error.
* ** Global context is change is now tested with `id()`.

### v1.0.0
* ++ Added `breadcrumbs-title` template.
* ++ `UNRESOLVED_ITEM_MARKER` introduced to settings.
* ++ Added Django 1.6 test rules.
* ** Fixed django 1.4.10 issue (see #116).
* -- Dropped deprecated `sitetree_url` tag arguments.
* -- Dropped deprecated template var support in sitetree item URL field.

### v0.12.1
* ++ Fixed bug when running sitetree with django version 1.4.10

### v0.12.0
* ++ Implemented runtime defined (dynamic) trees (see #105).
* ++ Added Foundation breadcrumbs template.
* ++ Added Semantic UI templates.
* ** Fixed `DatabaseError: integer out of range` generated on `sitetree_resync_apps` (see #105).
* ** Sitetree for apps module name made adjustable and defaults to `sitetrees` to prevent module name clashes.

### v0.11.0
* ++ Implemented helpers for dynamic tree structuring (see #105)
* ++ Added experimental support for app-defined trees (see #105).
* ++ Implemented tree item access restriction "for guests only" (closes #108)
* ++ Added Bootstrap 3 templates (closes #100).

### v0.10.0
* ++ Added experimental support for user-defined sitetree models (see #64).
* ++ Implemented `sitetree_page_hint` template tag (closes #103).
* ++ Added Spanish translation (closes #101).

### v0.9.5
* ++ Added `sitetree_page_description` template tag.
* ++ Tree item dropdown experimentally exposed (see #84).
* ++ Added `this-ancestor-siblings` alias support (see #99).
* ** Fixed 'map' object has no attribute 'append' on Py3 (see #94).
* ** Fixed sort order changing for top level tree items (see #98).

### v0.9.4
* ++ Added Django 1.5 url tag syntax support for URL field.
* ** Fixed args quoting in url tag call causing #unresolved links (closes #95).

### v0.9.3
* ++ Added Python 3 support (see #93).
* ++ Added persian translation.
* ** Fixed quotes around slug-like arguments in url() (#90).
* ** Added deprecation warnings workarounds (#89).
* -- Dropped Django 1.3 support.

### v0.9.2
* ++ Django 1.3+ set as required minimum.
* ++ Added Django 1.5 support (see #87).
* ++ Added namespaces support for known urls hint (closes #83).
* ++ Added 'as' clause for sitetree_url tag (see #81).
* ++ Introduced Tree.get_title().
* ** Humble performance improvements for large trees (see #49).
* ** Template variables in URL feature marked deprecated (fixes #74).

### v0.9.1
* ++ Added experimental URL pattern name hinting at tree item create/edit page (see #67).
* ** Fixed tree current item detection failures with i18n trees (see #66).

### v0.9.0
* ++ Added support for tree and tree item admin models overriding (see #43).
* ++ Added Foundation CSS Framework menu basic templates (see #41).
* ++ Added Bootstrap CSS Framework menu and breadcrumbs basic templates (see #41).
* ** Fixed sorting tree items by parent ID instead of parent sort order (see #55).
* ** Fixed crashes when using sitetreeload command with colored terminal (fixes #61).

### v0.8.0
* ++ Added 'title' field for Tree models.
* ++ Added German translation.
* ** Fixed management directory missing from dist (closes #50).

### v0.7.0
* ++ Added 'sitetreedump' and 'sitetreeload' management commands (fixes #36).
* ++ Added tests runner 'runtests.py'. Unit tests are now self-contained (see #42).
* ++ Now 'sitetree_menu' tag accepts any string as target branch alias. Related to dashed strings (see #38).
* ++ Now 'has_children' tree item attribute stands for visible children (see #38).
* ++ Now global template context is passed down all sitetree-related templates (see #39, see #40).
* ** Fixed template tags params clashes with context variables (see #42).

### v0.6.0
* ++ Added i18n trees support (see #27).
* ++ Added tree items processing hook support (see #26).
* ** Fixed various tree items filtering issues (see #34, #35).

### v0.5.2
* ** Fix for yes/no icons not shown in tree admin when non-eng LANGUAGE_CODE is used (closes #31).
* ** Fixed item's depth calculation (closes #29).
* ** Fixed misleading tree rendering bug in admin interface.
* ** Improved Django 1.4 compatibility (fixes #33).

### v0.5.1
* ++ Added Django 1.4 static files compatibility for Admin contrib.
* ++ Added support for slug-like IDs as item lookup params (see #24).
* ** Added None check in "tree_climber" method (fixes #22).
* ** Minor optimizations in tree.html template.

### v0.5.0
* ++ Now sitetree uses native Django cache framework (see #16).
* ++ Added "in_current_branch" item attribute (see #14, #18), and "current_branch" css class.
* ** South migrations are now shipped within application package (see #19).
* ** Current menu item now preserves "a" tag, and marked with "current_item" css class.
* ** Request object passing forced to "menu" method (fixes #15 ).
* ** Fixed "save & continue" wrong redirect on item's add page.
* ** Minor fixes.

### v0.4.0
* ++ Added permissions calculation optimization to "get_sitetree" method (see #9).
* ++ Added item access restriction for authenticated uses only.
* ++ Added "this-ancestor-children" alias support (see #14).
* ** Minor fixes.

### v0.3.1
* ** Invalid return fix in "init_tree" method (fixes #6).
* ** Added missing translation files.

### v0.3.0
* ++ New template tag "sitetree_page_title".
* ++ Added ukranian translation.
* ++ Added human-friendly debug messages.
* ++ Added permissions support (see #3).
* ++ Added South migrations.
* ++ Added "url_resolved" attribute to items.
* ++ Added basic unit tests (see # 4).
* ++ Added .rst documentation (fixed #5).
* ** Admin menu links normalized (fixes #2).
* ** Fixed variable names clashes in template tags file.
* ** Missing "has_children" attribute fix.

### v0.2.1
* ++ Added PyPi compatibility.
* ** Modules import fixes.
* ** README now in .rst.

### v0.2.0
* ++ Added support for non-ascii in urls.

### v0.1.4
* ** setup.py fix.
* ** Django under 1.2 compatibility fix for #1.

### v0.1.3
* ** "this-children" and "this-siblings" behavior fix.

### v0.1.2
* ** Setting items order in admin fix.

### v0.1.1
* ** Minor fixes.

### v0.1.0
* ++ Basic sitetree functionality.
