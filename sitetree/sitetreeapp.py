from __future__ import unicode_literals

import warnings

from collections import defaultdict
from copy import copy, deepcopy

from django.conf import settings
from django import VERSION
from django import template
from django.core.cache import cache
from django.db.models import signals
from django.utils import six
from django.utils.http import urlquote
from django.utils.translation import get_language
from django.utils.encoding import python_2_unicode_compatible
from django.template import Context
from django.template.defaulttags import url as url_tag

from .utils import get_tree_model, get_tree_item_model, import_app_sitetree_module, generate_id_for
from .settings import ALIAS_TRUNK, ALIAS_THIS_CHILDREN, ALIAS_THIS_SIBLINGS, ALIAS_THIS_PARENT_SIBLINGS, ALIAS_THIS_ANCESTOR_CHILDREN, UNRESOLVED_ITEM_MARKER


MODEL_TREE_CLASS = get_tree_model()
MODEL_TREE_ITEM_CLASS = get_tree_item_model()


# Sitetree objects are stored in Django cache for a year (60 * 60 * 24 * 365 = 31536000 sec).
# Cache is only invalidated on sitetree or sitetree item change.
CACHE_TIMEOUT = 31536000

# Holds tree items processor callable or None.
_ITEMS_PROCESSOR = None
# Holds aliases of trees that support internationalization.
_I18N_TREES = []
# Holds trees dynamically loaded from project apps.
_DYNAMIC_TREES = {}
# Dictionary index in `_DYNAMIC_TREES` for orphaned trees list.
_IDX_ORPHAN_TREES = 'orphans'
# Dictinary index name template in `_DYNAMIC_TREES`.
_IDX_TPL = '%s|:|%s'
# SiteTree app-wise object.
_SITETREE = None


def get_sitetree():
    """Returns SiteTree [singleton] object, implementing utility methods.

    :return: SiteTree
    """
    global _SITETREE
    if _SITETREE is None:
        _SITETREE = SiteTree()
    return _SITETREE


def register_items_hook(callable):
    """Registers a hook callable to process tree items right before they are passed to templates.

    Callable should be able to:

        a) handle ``tree_items`` and ``tree_sender`` key params.
            ``tree_items`` will contain a list of extended TreeItem objects ready to pass to template.
            ``tree_sender`` will contain navigation type identifier
                (e.g.: `menu`, `sitetree`, `breadcrumbs`, `menu.children`, `sitetree.children`)

        b) return a list of extended TreeItems objects to pass to template.


    Example::

        # Put the following code somewhere where it'd be triggered as expected. E.g. in app view.py.

        # First import the register function.
        from sitetree.sitetreeapp import register_items_hook

        # The following function will be used as items processor.
        def my_items_processor(tree_items, tree_sender):
            # Suppose we want to process only menu child items.
            if tree_sender == 'menu.children':
                # Lets add 'Hooked: ' to resolved titles of every item.
                for item in tree_items:
                    item.title_resolved = 'Hooked: %s' % item.title_resolved
            # Return items list mutated or not.
            return tree_items

        # And we register items processor.
        register_items_hook(my_items_processor)

    """
    global _ITEMS_PROCESSOR
    _ITEMS_PROCESSOR = callable


def register_i18n_trees(aliases):
    """Registers aliases of internationalized sitetrees.
    Internationalized sitetrees are those, which are dubbed by other trees having
    locale identifying suffixes in their aliases.

    Lets suppose ``my_tree`` is the alias of a generic tree. This tree is the one
    that we call by its alias in templates, and it is the one which is used
    if no i18n version of that tree is found.

    Given that ``my_tree_en``, ``my_tree_ru`` and other ``my_tree_{locale-id}``-like
    trees are considered internationalization sitetrees. These are used (if available)
    in accordance with current locale used by project.

    Example::

        # Put the following code somewhere where it'd be triggered as expected. E.g. in main urls.py.

        # First import the register function.
        from sitetree.sitetreeapp import register_i18n_trees

        # At last we register i18n trees.
        register_i18n_trees(['my_tree', 'my_another_tree'])

    """
    global _I18N_TREES
    _I18N_TREES = aliases


def register_dynamic_trees(trees, *args, **kwargs):
    """Registers dynamic trees to be available for `sitetree` runtime.
    Expects `trees` to be an iterable with structures created with `compose_dynamic_tree()`.

    Example::

        register_dynamic_trees(

            # Get all the trees from `my_app`.
            compose_dynamic_tree('my_app'),

            # Get all the trees from `my_app` and attach them to `main` tree root.
            compose_dynamic_tree('my_app', target_tree_alias='main'),

            # Get all the trees from `my_app` and attach them to `has_dynamic` aliased item in `main` tree.
            compose_dynamic_tree('articles', target_tree_alias='main', parent_tree_item_alias='has_dynamic'),

            # Define a tree right on the registration.
            compose_dynamic_tree((
                tree('dynamic', items=(
                    item('dynamic_1', 'dynamic_1_url', children=(
                        item('dynamic_1_sub_1', 'dynamic_1_sub_1_url'),
                    )),
                    item('dynamic_2', 'dynamic_2_url'),
                )),
            )),
        )

    Accepted kwargs:

    :param bool reset_cache: Resets tree cache, to introduce all changes made to a tree immediately.
    """

    global _DYNAMIC_TREES

    if _IDX_ORPHAN_TREES not in _DYNAMIC_TREES:
        _DYNAMIC_TREES[_IDX_ORPHAN_TREES] = {}

    if isinstance(trees, dict):  # New `less-brackets` style registration.
        trees = [trees]
        trees.extend(args)

    for tree in trees:
        if tree is not None and tree['sitetrees'] is not None:
            if tree['tree'] is None:
                # Register trees as they are defined in app.
                for st in tree['sitetrees']:
                    if st.alias not in _DYNAMIC_TREES[_IDX_ORPHAN_TREES]:
                        _DYNAMIC_TREES[_IDX_ORPHAN_TREES][st.alias] = []
                    _DYNAMIC_TREES[_IDX_ORPHAN_TREES][st.alias].append(st)
            else:
                # Register tree items as parts of existing trees.
                index = _IDX_TPL % (tree['tree'], tree['parent_item'])
                if index not in _DYNAMIC_TREES:
                    _DYNAMIC_TREES[index] = []
                _DYNAMIC_TREES[index].extend(tree['sitetrees'])

    reset_cache = kwargs.get('reset_cache', False)
    if reset_cache:
        get_sitetree().cache_empty()


def get_dynamic_trees():
    """Returns a dictionary with currently registered dynamic trees."""
    return _DYNAMIC_TREES


def compose_dynamic_tree(src, target_tree_alias=None, parent_tree_item_alias=None, include_trees=None):
    """Returns a structure describing a dynamic sitetree.utils
    The structure can be built from various sources,

    Thus, if a string is passed to `src`, it'll be treated as the name of an app,
    from where one want to import sitetrees definitions.

    On the other hand, `src` can be an iterable of trees definitions
    (see `sitetree.utils.tree()` and `item()` functions).


    `target_tree_alias` - expects a static tree alias to attach items from dynamic trees to.
    `parent_tree_item_alias` - expects a tree item alias from a static tree to attach items from dynamic trees to.
    `include_trees` - expects a list of sitetree aliases to filter `src`.


    """

    def result(sitetrees=src):
        if include_trees is not None:
            sitetrees = [tree for tree in sitetrees if tree.alias in include_trees]
        return {'app': src, 'sitetrees': sitetrees, 'tree': target_tree_alias, 'parent_item': parent_tree_item_alias}

    if isinstance(src, six.string_types):
        # Considered an application name.
        try:
            module = import_app_sitetree_module(src)
            if module is None:
                return None
            return result(getattr(module, 'sitetrees', None))
        except ImportError as e:
            if settings.DEBUG:
                warnings.warn('Unable to register dynamic sitetree(s) for `%s` application: %s. ' % (src, e))
    else:
        return result()
    return None


@python_2_unicode_compatible
class LazyTitle(object):
    """Lazily resolves any variable found in a title of an item.
    Produces resolved title as unicode representation."""

    def __init__(self, title):
        self.title = title

    def __str__(self):
        my_lexer = template.Lexer(self.title, template.UNKNOWN_SOURCE)
        my_tokens = my_lexer.tokenize()

        # Deliberately strip off template tokens that are not text or variable.
        for my_token in my_tokens:
            if my_token.token_type not in (template.TOKEN_TEXT, template.TOKEN_VAR):
                my_tokens.remove(my_token)

        my_parser = template.Parser(my_tokens)
        return my_parser.parse().render(SiteTree.get_global_context())

    def __eq__(self, other):
        return self.__str__() == other


class SiteTree(object):

    _global_context = Context()

    def __init__(self):
        self.cache = None
        # Listen for signals from the models.
        signals.post_save.connect(self.cache_empty, sender=MODEL_TREE_CLASS)
        signals.post_save.connect(self.cache_empty, sender=MODEL_TREE_ITEM_CLASS)
        signals.post_delete.connect(self.cache_empty, sender=MODEL_TREE_ITEM_CLASS)
        # Listen to the changes in item permissions table.
        signals.m2m_changed.connect(self.cache_empty, sender=MODEL_TREE_ITEM_CLASS.access_permissions)

    def cache_init(self):
        """Initializes local cache from Django cache."""
        cache_ = cache.get('sitetrees')
        if cache_ is None:
            # Init cache dictionary with predefined entries.
            cache_ = {'sitetrees': {}, 'urls': {}, 'parents': {}, 'items_by_ids': {}, 'tree_aliases': {}}
        self.cache = cache_

    def cache_save(self):
        """Saves sitetree data to Django cache."""
        cache.set('sitetrees', self.cache, CACHE_TIMEOUT)

    def cache_empty(self, **kwargs):
        """Empties cached sitetree data."""
        self.cache = None
        cache.delete('sitetrees')
        cache.delete('tree_aliases')

    def get_cache_entry(self, entry_name, key):
        """Returns cache entry parameter value by its name."""
        return self.cache[entry_name].get(key, False)

    def update_cache_entry_value(self, entry_name, key, value):
        """Updates cache entry parameter with new data."""
        if key not in self.cache[entry_name]:
            self.cache[entry_name][key] = {}
        self.cache[entry_name][key].update(value)

    def set_cache_entry(self, entry_name, key, value):
        """Replaces entire cache entry parameter data by its name with new data."""
        self.cache[entry_name][key] = value

    @classmethod
    def set_global_context(cls, context):
        """Saves context as global context if not already set or if changed.
        Almost all variables are resolved against global context.

        """
        if not cls._global_context or id(context) != id(cls._global_context):
            cls._global_context = context

    @classmethod
    def get_global_context(cls):
        """Returns current sitetree global context."""
        return cls._global_context

    def resolve_tree_i18n_alias(self, alias):
        """Resolves internationalized tree alias.
        Verifies whether a separate sitetree is available for currently active language.
        If so, returns i18n alias. If not, returns the initial alias.
        """
        if alias in _I18N_TREES:
            current_language_code = get_language().replace('_', '-').split('-')[0]
            i18n_tree_alias = '%s_%s' % (alias, current_language_code)
            trees_count = self.get_cache_entry('tree_aliases', i18n_tree_alias)
            if trees_count is False:
                trees_count = MODEL_TREE_CLASS.objects.filter(alias=i18n_tree_alias).count()
                self.set_cache_entry('tree_aliases', i18n_tree_alias, trees_count)
            if trees_count:
                alias = i18n_tree_alias
        return alias

    @staticmethod
    def attach_dynamic_tree_items(tree_alias, src_tree_items):
        """Attaches dynamic sitetrees items registered with `register_dynamic_trees()`
        to an initial (source) items list.

        """
        if not _DYNAMIC_TREES:
            return src_tree_items

        # This guarantees that a dynamic source stays intact,
        # no matter how dynamic sitetrees are attached.
        TREES = deepcopy(_DYNAMIC_TREES)

        items = []
        if not src_tree_items:
            if _IDX_ORPHAN_TREES in TREES and tree_alias in TREES[_IDX_ORPHAN_TREES]:
                for tree in TREES[_IDX_ORPHAN_TREES][tree_alias]:
                    items.extend(tree.dynamic_items)
        else:

            # TODO Seems to be underoptimized %)

            # Tree item attachment by alias.
            for static_item in list(src_tree_items):
                items.append(static_item)
                if static_item.alias:
                    idx = _IDX_TPL % (tree_alias, static_item.alias)
                    if idx in TREES:
                        for tree in TREES[idx]:
                            tree.alias = tree_alias
                            for dyn_item in tree.dynamic_items:
                                if dyn_item.parent is None:
                                    dyn_item.parent = static_item
                                # Unique IDs are required for the same trees attached
                                # to different parents.
                                dyn_item.id = generate_id_for(dyn_item)
                                items.append(dyn_item)

            # Tree root attachment.
            idx = _IDX_TPL % (tree_alias, None)
            if idx in _DYNAMIC_TREES:
                TREES = deepcopy(_DYNAMIC_TREES)
                for tree in TREES[idx]:
                    tree.alias = tree_alias
                    items.extend(tree.dynamic_items)

        return items

    def get_sitetree(self, alias):
        """Gets site tree items from the given site tree.
        Caches result to dictionary.
        Returns (tree alias, tree items) tuple.

        """
        self.cache_init()
        sitetree_needs_caching = False
        if self._global_context.current_app != 'admin':
            # We do not need i18n for a tree rendered in Admin dropdown.
            alias = self.resolve_tree_i18n_alias(alias)
        sitetree = self.get_cache_entry('sitetrees', alias)
        if not sitetree:
            sitetree = MODEL_TREE_ITEM_CLASS.objects.select_related('parent', 'tree').\
                   filter(tree__alias__exact=alias).order_by('parent__sort_order', 'sort_order')
            sitetree = self.attach_dynamic_tree_items(alias, sitetree)
            self.set_cache_entry('sitetrees', alias, sitetree)
            sitetree_needs_caching = True

        parents = self.get_cache_entry('parents', alias)
        if not parents:
            parents = defaultdict(list)
            for item in sitetree:
                parent = getattr(item, 'parent')
                parents[parent].append(item)
            self.set_cache_entry('parents', alias, parents)

        # Prepare items by ids cache if needed.
        if sitetree_needs_caching:
            # We need this extra pass to avoid future problems on items depth calculation.
            for item in sitetree:
                self.update_cache_entry_value('items_by_ids', alias, {item.id: item})

        for item in sitetree:
            if sitetree_needs_caching:
                item.has_children = False

                if not hasattr(item, 'depth'):
                    item.depth = self.calculate_item_depth(alias, item.id)
                item.depth_range = range(item.depth)

                # Resolve item permissions.
                if item.access_restricted:
                    item.perms = set([u'%s.%s' % (perm.content_type.app_label, perm.codename) for perm in
                                               item.access_permissions.select_related()])
            # Contextual properties.
            item.url_resolved = self.url(item)
            if template.VARIABLE_TAG_START in item.title:
                item.title_resolved = LazyTitle(item.title)
            else:
                item.title_resolved = item.title
            item.is_current = False
            item.in_current_branch = False

        # Get current item for the given sitetree.
        self.get_tree_current_item(alias)

        # Save sitetree data into cache if needed.
        if sitetree_needs_caching:
            self.cache_save()

        return alias, sitetree

    def calculate_item_depth(self, tree_alias, item_id, depth=0):
        """Calculates depth of the item in the tree."""
        item = self.get_item_by_id(tree_alias, item_id)
        if not hasattr(item, 'depth'):
            if item.parent is not None:
                depth = self.calculate_item_depth(tree_alias, item.parent.id, depth + 1)
        else:
            depth = item.depth + depth
        return depth

    def get_item_by_id(self, tree_alias, item_id):
        """Get the item from the tree by its ID."""
        return self.get_cache_entry('items_by_ids', tree_alias)[item_id]

    def get_tree_current_item(self, tree_alias):
        """Resolves current tree item of 'tree_alias' tree matching current
        request path against URL of given tree item.

        """
        if self._global_context.current_app == 'admin':
            return None

        current_item = None

        if 'request' not in self._global_context:
            if settings.DEBUG:
                raise SiteTreeError('Sitetree needs "django.core.context_processors.request" to be in TEMPLATE_CONTEXT_PROCESSORS in your settings file. If it is, check that your view pushes request data into the template.')
        else:
            # urlquote is an attempt to support non-ascii in url.
            current_url = urlquote(self._global_context['request'].path)
            urls_cache = self.get_cache_entry('urls', tree_alias)
            if urls_cache:
                for url_item in urls_cache:
                    urls_cache[url_item][1].is_current = False
                    if urls_cache[url_item][0] == current_url:
                        current_item = urls_cache[url_item][1]

        if current_item is not None:
            current_item.is_current = True

        return current_item

    def url(self, sitetree_item, context=None):
        """Resolves item's URL.

        'sitetree_item' points to TreeItem object, 'url' property of which
            is processed as URL pattern or simple URL.

        """

        if context is None:
            context = self._global_context

        if not isinstance(sitetree_item, MODEL_TREE_ITEM_CLASS):
            sitetree_item = self.resolve_var(sitetree_item, context)

        # Resolve only if item's URL is marked as pattern.
        if sitetree_item.urlaspattern:
            url = sitetree_item.url
            view_path = url
            all_arguments = []

            if ' ' in url:
                view_path = url.split(' ')
                # We should try to resolve URL parameters from site tree item.
                for view_argument in view_path[1:]:
                    resolved = self.resolve_var(view_argument)
                    # In case of non-ascii data we leave variable unresolved.
                    if isinstance(resolved, six.text_type):
                        if resolved.encode('ascii', 'ignore').decode('ascii') != resolved:
                            resolved = view_argument
                        # URL parameters from site tree item should be concatenated with those from template.
                    all_arguments.append('"%s"' % str(resolved))  # We enclose arg in double quotes as already resolved.
                view_path = view_path[0].strip('"\' ')

            if VERSION >= (1, 5, 0):  # "new-style" url tag - consider sitetree named urls literals.
                view_path = "'%s'" % view_path

            url_pattern = u'%s %s' % (view_path, ' '.join(all_arguments))
        else:
            url_pattern = str(sitetree_item.url)

        tree_alias = sitetree_item.tree.alias

        entry_from_cache = self.get_cache_entry('urls', tree_alias)
        if not entry_from_cache:
            # Create 'cache_urls' for this tree.
            entry_from_cache = {}
            self.set_cache_entry('urls', tree_alias, {})

        if url_pattern in entry_from_cache:
            resolved_url = entry_from_cache[url_pattern][0]
        else:
            if sitetree_item.urlaspattern:
                # Form token to pass to Django 'url' tag.
                url_token = u'url %s as item.url_resolved' % url_pattern
                url_tag(template.Parser(None), template.Token(token_type=template.TOKEN_BLOCK, contents=url_token)).render(context)

                # We make an anchor link from an unresolved URL as a reminder.
                if not context['item.url_resolved']:
                    resolved_url = UNRESOLVED_ITEM_MARKER
                else:
                    resolved_url = context['item.url_resolved']
            else:
                resolved_url = url_pattern

            self.update_cache_entry_value('urls', tree_alias, {url_pattern: (resolved_url, sitetree_item)})

        return resolved_url

    def init_tree(self, tree_alias, context):
        """Tries to initialize sitetree in memory.
        Returns tuple with resolved tree alias and items on success.
        On fail returns False.

        """
        # Current context we will consider global.
        self.set_global_context(context)
        # Resolve tree_alias from the context.
        tree_alias = self.resolve_var(tree_alias)
        # Get tree.
        tree_alias, sitetree_items = self.get_sitetree(tree_alias)
        # No items in tree, fail silently.
        if not sitetree_items:
            return False, False
        return tree_alias, sitetree_items

    def get_current_page_title(self, tree_alias, context):
        """Returns resolved from sitetree title for current page."""
        return self.get_current_page_attr('title_resolved', tree_alias, context)

    def get_current_page_attr(self, attr_name, tree_alias, context):
        """Returns an arbitrary attribute of a sitetree item resolved as current for current page."""
        tree_alias, sitetree_items = self.init_tree(tree_alias, context)
        current_item = self.get_tree_current_item(tree_alias)
        # Current item is unresolved, fail silently.
        if current_item is None:
            if settings.DEBUG:
                raise SiteTreeError('Unable to resolve current sitetree item to get a `%s` for current page. Check whether there is an appropriate sitetree item defined for current URL.' % attr_name)
            return ''
        return getattr(current_item, attr_name, '')

    def get_ancestor_level(self, current_item, deep=1):
        """Returns ancestor of level `deep` recursively"""
        if current_item.parent is not None:
            if deep <= 1:
                return current_item.parent
            else:
                return self.get_ancestor_level(current_item.parent, deep=deep-1)
        else:
            return current_item

    def menu(self, tree_alias, tree_branches, context):
        """Builds and returns menu structure for 'sitetree_menu' tag."""
        tree_alias, sitetree_items = self.init_tree(tree_alias, context)
        # No items in tree, fail silently.
        if not sitetree_items:
            return ''
        tree_branches = self.resolve_var(tree_branches)

        parent_isnull = False
        parent_ids = []
        parent_aliases = []

        current_item = self.get_tree_current_item(tree_alias)
        self.tree_climber(tree_alias, current_item)

        # Support item addressing both through identifiers and aliases.
        for branch_id in tree_branches.split(','):
            branch_id = branch_id.strip()
            if branch_id == ALIAS_TRUNK:
                parent_isnull = True
            elif branch_id == ALIAS_THIS_CHILDREN and current_item is not None:
                branch_id = current_item.id
                parent_ids.append(branch_id)
            elif branch_id == ALIAS_THIS_ANCESTOR_CHILDREN and current_item is not None:
                branch_id = self.get_ancestor_item(tree_alias, current_item).id
                parent_ids.append(branch_id)
            elif branch_id == ALIAS_THIS_SIBLINGS and current_item is not None and current_item.parent is not None:
                branch_id = current_item.parent.id
                parent_ids.append(branch_id)
            elif branch_id == ALIAS_THIS_PARENT_SIBLINGS and current_item is not None:
                branch_id = self.get_ancestor_level(current_item, deep=2).id
                parent_ids.append(branch_id)
            elif branch_id.isdigit():
                parent_ids.append(int(branch_id))
            else:
                parent_aliases.append(branch_id)

        menu_items = []
        for item in sitetree_items:
            if not item.hidden and item.inmenu and self.check_access(item, context):
                if item.parent is None:
                    if parent_isnull:
                        menu_items.append(item)
                else:
                    if item.parent.id in parent_ids or item.parent.alias in parent_aliases:
                        menu_items.append(item)

        # Parse titles for variables.
        menu_items = self.apply_hook(menu_items, 'menu')
        menu_items = self.update_has_children(tree_alias, menu_items, 'menu')
        return menu_items

    def apply_hook(self, items, sender):
        """Applies item processing hook, registered with ``register_item_hook()``
        to items supplied, and returns processed list.
        Returns initial items list if no hook is registered.

        """
        if _ITEMS_PROCESSOR is None:
            return items
        return _ITEMS_PROCESSOR(tree_items=items, tree_sender=sender)

    def check_access(self, item, context):
        """Checks whether a current user has an access to a certain item."""

        authenticated = self._global_context['request'].user.is_authenticated()

        if item.access_loggedin and not authenticated:
            return False

        if item.access_guest and authenticated:
            return False

        if item.access_restricted:
            user_perms = set(context['user'].get_all_permissions())
            if item.access_perm_type == MODEL_TREE_ITEM_CLASS.PERM_TYPE_ALL:
                if len(item.perms) != len(item.perms.intersection(user_perms)):
                    return False
            else:
                if not len(item.perms.intersection(user_perms)):
                    return False
        return True

    def breadcrumbs(self, tree_alias, context):
        """Builds and returns breadcrumb trail structure for 'sitetree_breadcrumbs' tag."""
        tree_alias, sitetree_items = self.init_tree(tree_alias, context)
        # No items in tree, fail silently.
        if not sitetree_items:
            return ''
        current_item = self.get_tree_current_item(tree_alias)

        self.cache_breadcrumbs = []
        if current_item is not None:
            self.breadcrumbs_climber(tree_alias, current_item)
            self.cache_breadcrumbs.reverse()
        items = self.apply_hook(self.cache_breadcrumbs, 'breadcrumbs')
        items = self.update_has_children(tree_alias, items, 'breadcrumbs')
        return items

    def tree(self, tree_alias, context):
        """Builds and returns tree structure for 'sitetree_tree' tag."""
        tree_alias, sitetree_items = self.init_tree(tree_alias, context)
        # No items in tree, fail silently.
        if not sitetree_items:
            return ''
        tree_items = self.filter_items(self.get_children(tree_alias, None), 'sitetree')
        tree_items = self.apply_hook(tree_items, 'sitetree')
        tree_items = self.update_has_children(tree_alias, tree_items, 'sitetree')
        return tree_items

    def children(self, parent_item, navigation_type, use_template, context):
        """Builds and returns site tree item children structure
        for 'sitetree_children' tag.

        """
        # Resolve parent item and current tree alias.
        parent_item = self.resolve_var(parent_item, context)
        tree_alias = parent_item.tree.alias
        # Resolve tree_alias from the context.
        tree_alias = self.resolve_var(tree_alias)
        # Get tree.
        tree_alias, tree_items = self.get_sitetree(tree_alias)
        # Mark path to current item.
        self.tree_climber(tree_alias, self.get_tree_current_item(tree_alias))

        tree_items = self.get_children(tree_alias, parent_item)
        tree_items = self.filter_items(tree_items, navigation_type)
        tree_items = self.apply_hook(tree_items, '%s.children' % navigation_type)
        tree_items = self.update_has_children(tree_alias, tree_items, navigation_type)

        my_template = template.loader.get_template(use_template)
        context.update({'sitetree_items': tree_items})
        return my_template.render(context)

    def get_children(self, tree_alias, item):
        if self._global_context.current_app != 'admin':
            # We do not need i18n for a tree rendered in Admin dropdown.
            tree_alias = self.resolve_tree_i18n_alias(tree_alias)
        return self.get_cache_entry('parents', tree_alias)[item]

    def update_has_children(self, tree_alias, tree_items, navigation_type):
        """Updates 'has_children' attribute for tree items."""
        items = []
        for tree_item in tree_items:
            children = self.get_children(tree_alias, tree_item)
            children = self.filter_items(children, navigation_type)
            children = self.apply_hook(children, '%s.has_children' % navigation_type)
            tree_item.has_children = len(children) > 0
            items.append(tree_item)
        return items

    def filter_items(self, items, navigation_type=None):
        """Filters site tree item's children if hidden and by navigation type.
        NB: We do not apply any filters to sitetree in admin app.
        """
        items_out = copy(items)
        if self._global_context.current_app != 'admin':
            for item in items:
                no_access = not self.check_access(item, self._global_context)
                hidden_for_nav_type = navigation_type is not None and not getattr(item, 'in' + navigation_type, False)
                if item.hidden or no_access or hidden_for_nav_type:
                    items_out.remove(item)
        return items_out

    def get_ancestor_item(self, tree_alias, start_from):
        """Climbs up the site tree to resolve root item for chosen one."""
        parent = None

        if hasattr(start_from, 'parent') and start_from.parent is not None:
            parent = self.get_ancestor_item(tree_alias, self.get_item_by_id(tree_alias, start_from.parent.id))

        if parent is None:
            return start_from

        return parent

    def tree_climber(self, tree_alias, start_from):
        """Climbs up the site tree to mark items of current branch."""
        if start_from is not None:
            start_from.in_current_branch = True
            if hasattr(start_from, 'parent') and start_from.parent is not None:
                self.tree_climber(tree_alias, self.get_item_by_id(tree_alias, start_from.parent.id))

    def breadcrumbs_climber(self, tree_alias, start_from):
        """Climbs up the site tree to build breadcrumb path."""
        if start_from.inbreadcrumbs and start_from.hidden == False and self.check_access(start_from,
                                                                                         self._global_context):
            self.cache_breadcrumbs.append(start_from)
        if hasattr(start_from, 'parent') and start_from.parent is not None:
            self.breadcrumbs_climber(tree_alias, self.get_item_by_id(tree_alias, start_from.parent.id))

    def resolve_var(self, varname, context=None):
        """Tries to resolve name as a variable in a given context.
        If no context specified 'global_context' is considered
        as context.

        """
        if context is None:
            context = self._global_context

        if isinstance(varname, template.FilterExpression):
            varname = varname.resolve(context)
        else:
            varname = varname.strip()

            try:
                varname = template.Variable(varname).resolve(context)
            except template.VariableDoesNotExist:
                varname = varname

        return varname


class SiteTreeError(Exception):
    """Exception class for sitetree application."""
    pass
