from __future__ import unicode_literals
import warnings
from collections import defaultdict
from copy import deepcopy
from threading import local
from functools import partial

from django.conf import settings
from django import VERSION
from django.core.cache import cache
from django.db.models import signals
from django.utils import six
from django.utils.http import urlquote
from django.utils.translation import get_language
from django.utils.encoding import python_2_unicode_compatible
from django.template.loader import get_template
from django.template.base import (
    FilterExpression, Lexer, Parser, Token, Variable, VariableDoesNotExist, TOKEN_BLOCK, UNKNOWN_SOURCE, TOKEN_TEXT,
    TOKEN_VAR, VARIABLE_TAG_START)
from django.template.defaulttags import url as url_tag

from .utils import get_tree_model, get_tree_item_model, import_app_sitetree_module, generate_id_for
from .settings import (
    ALIAS_TRUNK, ALIAS_THIS_CHILDREN, ALIAS_THIS_SIBLINGS, ALIAS_THIS_PARENT_SIBLINGS, ALIAS_THIS_ANCESTOR_CHILDREN,
    UNRESOLVED_ITEM_MARKER, RAISE_ITEMS_ERRORS_ON_DEBUG, CACHE_TIMEOUT)
from .exceptions import SiteTreeError


if False:  # For type hinting purposes.
    from django.template import Context
    from .models import TreeItemBase


if VERSION >= (1, 9, 0):
    get_lexer = partial(Lexer)
else:
    get_lexer = partial(Lexer, origin=UNKNOWN_SOURCE)


MODEL_TREE_CLASS = get_tree_model()
MODEL_TREE_ITEM_CLASS = get_tree_item_model()


_ITEMS_PROCESSOR = None
"""Stores tree items processor callable or None."""

_I18N_TREES = []
"""Stores aliases of trees supporting internationalization."""

_DYNAMIC_TREES = {}
"""Holds trees dynamically loaded from project apps."""

_IDX_ORPHAN_TREES = 'orphans'
"""Dictionary index in `_DYNAMIC_TREES` for orphaned trees list."""

_IDX_TPL = '%s|:|%s'
"""Name template used as dictionary index in `_DYNAMIC_TREES`."""

_THREAD_LOCAL = local()
_THREAD_SITETREE = 'sitetree'

_URL_TAG_NEW_STYLE = VERSION >= (1, 5, 0)

_UNSET = set()  # Sentinel


def get_sitetree():
    """Returns SiteTree (thread-singleton) object, implementing utility methods.

    :rtype: SiteTree
    """
    sitetree = getattr(_THREAD_LOCAL, _THREAD_SITETREE, None)

    if sitetree is None:
        sitetree = SiteTree()
        setattr(_THREAD_LOCAL, _THREAD_SITETREE, sitetree)

    return sitetree


def register_items_hook(func):
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

    :param func:
    """
    global _ITEMS_PROCESSOR
    _ITEMS_PROCESSOR = func


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

    :param aliases:
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
        bool reset_cache: Resets tree cache, to introduce all changes made to a tree immediately.

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
        cache_ = get_sitetree().cache
        cache_.empty()
        cache_.reset()


def get_dynamic_trees():
    """Returns a dictionary with currently registered dynamic trees."""
    return _DYNAMIC_TREES


def compose_dynamic_tree(src, target_tree_alias=None, parent_tree_item_alias=None, include_trees=None):
    """Returns a structure describing a dynamic sitetree.utils
    The structure can be built from various sources,

    :param str|iterable src: If a string is passed to `src`, it'll be treated as the name of an app,
        from where one want to import sitetrees definitions. `src` can be an iterable
        of tree definitions (see `sitetree.toolbox.tree()` and `item()` functions).

    :param str|unicode target_tree_alias: Static tree alias to attach items from dynamic trees to.

    :param str|unicode parent_tree_item_alias: Tree item alias from a static tree to attach items from dynamic trees to.

    :param list include_trees: Sitetree aliases to filter `src`.

    :rtype: dict
    """
    def result(sitetrees=src):
        if include_trees is not None:
            sitetrees = [tree for tree in sitetrees if tree.alias in include_trees]

        return {
            'app': src,
            'sitetrees': sitetrees,
            'tree': target_tree_alias,
            'parent_item': parent_tree_item_alias}

    if isinstance(src, six.string_types):
        # Considered to be an application name.
        try:
            module = import_app_sitetree_module(src)
            return None if module is None else result(getattr(module, 'sitetrees', None))

        except ImportError as e:
            if settings.DEBUG:
                warnings.warn('Unable to register dynamic sitetree(s) for `%s` application: %s. ' % (src, e))
            return None

    return result()


@python_2_unicode_compatible
class LazyTitle(object):
    """Lazily resolves any variable found in a title of an item.
    Produces resolved title as unicode representation."""

    def __init__(self, title):
        """
        :param str|unicode title:
        """
        self.title = title

    def __str__(self):
        my_lexer = get_lexer(self.title)
        my_tokens = my_lexer.tokenize()

        # Deliberately strip off template tokens that are not text or variable.
        for my_token in my_tokens:
            if my_token.token_type not in (TOKEN_TEXT, TOKEN_VAR):
                my_tokens.remove(my_token)

        my_parser = Parser(my_tokens)
        return my_parser.parse().render(get_sitetree().current_page_context)

    def __eq__(self, other):
        return self.__str__() == other


class Cache(object):
    """Contains cache-related stuff."""

    def __init__(self):
        self.cache = None

        cache_empty = self.empty
        # Listen for signals from the models.
        signals.post_save.connect(cache_empty, sender=MODEL_TREE_CLASS)
        signals.post_save.connect(cache_empty, sender=MODEL_TREE_ITEM_CLASS)
        signals.post_delete.connect(cache_empty, sender=MODEL_TREE_ITEM_CLASS)
        # Listen to the changes in item permissions table.
        signals.m2m_changed.connect(cache_empty, sender=MODEL_TREE_ITEM_CLASS.access_permissions)
        self.init()

    @classmethod
    def reset(cls):
        """Instructs sitetree to drop and recreate cache.

        Could be used to show up tree changes made in a different process.

        """
        cache.set('sitetrees_reset', True)

    def init(self):
        """Initializes local cache from Django cache."""

        # Drop cache flag set by .reset() method.
        cache.get('sitetrees_reset') and self.empty(init=False)

        self.cache = cache.get(
            'sitetrees', {'sitetrees': {}, 'parents': {}, 'items_by_ids': {}, 'tree_aliases': {}})

    def save(self):
        """Saves sitetree data to Django cache."""
        cache.set('sitetrees', self.cache, CACHE_TIMEOUT)

    def empty(self, **kwargs):
        """Empties cached sitetree data."""
        cache.delete('sitetrees')
        cache.delete('sitetrees_reset')

        kwargs.get('init', True) and self.init()

    def get_entry(self, entry_name, key):
        """Returns cache entry parameter value by its name.

        :param str|unicode entry_name:
        :param key:
        :return:
        """
        return self.cache[entry_name].get(key, False)

    def update_entry_value(self, entry_name, key, value):
        """Updates cache entry parameter with new data.

        :param str|unicode entry_name:
        :param key:
        :param value:
        """
        if key not in self.cache[entry_name]:
            self.cache[entry_name][key] = {}

        self.cache[entry_name][key].update(value)

    def set_entry(self, entry_name, key, value):
        """Replaces entire cache entry parameter data by its name with new data.

        :param str|unicode entry_name:
        :param key:
        :param value:
        """
        self.cache[entry_name][key] = value


class SiteTree(object):
    """Main logic handler."""

    def __init__(self):
        self.init(context=None)

    def init(self, context):
        """Initializes sitetree to handle new request.

        :param Context|None context:
        """
        self.cache = Cache()
        self.current_page_context = context
        self.current_request = context.get('request', None) if context else None
        self.current_lang = get_language()

        self._current_app_is_admin = None
        self._current_user_permissions = _UNSET
        self._items_urls = {}  # Resolved urls are cache for a request.
        self._current_items = {}

    def resolve_tree_i18n_alias(self, alias):
        """Resolves internationalized tree alias.
        Verifies whether a separate sitetree is available for currently active language.
        If so, returns i18n alias. If not, returns the initial alias.

        :param str|unicode alias:
        :rtype: str|unicode
        """
        if alias not in _I18N_TREES:
            return alias

        current_language_code = self.current_lang.replace('_', '-').split('-')[0]
        i18n_tree_alias = '%s_%s' % (alias, current_language_code)
        trees_count = self.cache.get_entry('tree_aliases', i18n_tree_alias)

        if trees_count is False:
            trees_count = MODEL_TREE_CLASS.objects.filter(alias=i18n_tree_alias).count()
            self.cache.set_entry('tree_aliases', i18n_tree_alias, trees_count)

        if trees_count:
            alias = i18n_tree_alias

        return alias

    @staticmethod
    def attach_dynamic_tree_items(tree_alias, src_tree_items):
        """Attaches dynamic sitetrees items registered with `register_dynamic_trees()`
        to an initial (source) items list.

        :param str|unicode tree_alias:
        :param list src_tree_items:
        :rtype: list
        """
        if not _DYNAMIC_TREES:
            return src_tree_items

        # This guarantees that a dynamic source stays intact,
        # no matter how dynamic sitetrees are attached.
        trees = deepcopy(_DYNAMIC_TREES)

        items = []
        if not src_tree_items:
            if _IDX_ORPHAN_TREES in trees and tree_alias in trees[_IDX_ORPHAN_TREES]:
                for tree in trees[_IDX_ORPHAN_TREES][tree_alias]:
                    items.extend(tree.dynamic_items)
        else:

            # TODO Seems to be underoptimized %)

            # Tree item attachment by alias.
            for static_item in list(src_tree_items):
                items.append(static_item)
                if not static_item.alias:
                    continue

                idx = _IDX_TPL % (tree_alias, static_item.alias)
                if idx not in trees:
                    continue

                for tree in trees[idx]:
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
                trees = deepcopy(_DYNAMIC_TREES)
                for tree in trees[idx]:
                    tree.alias = tree_alias
                    items.extend(tree.dynamic_items)

        return items

    def current_app_is_admin(self):
        """Returns boolean whether current application is Admin contrib.

        :rtype: bool
        """
        is_admin = self._current_app_is_admin
        if is_admin is None:
            context = self.current_page_context

            current_app = getattr(
                # Try from request.resolver_match.app_name
                getattr(context.get('request', None), 'resolver_match', None), 'app_name',
                # Try from global context obj.
                getattr(context, 'current_app', None))

            if current_app is None:  # Try from global context dict.
                current_app = context.get('current_app', '')

            is_admin = current_app == 'admin'
            self._current_app_is_admin = is_admin

        return is_admin

    def get_sitetree(self, alias):
        """Gets site tree items from the given site tree.
        Caches result to dictionary.
        Returns (tree alias, tree items) tuple.

        :param str|unicode alias:
        :rtype: tuple
        """
        cache_ = self.cache
        get_cache_entry = cache_.get_entry
        set_cache_entry = cache_.set_entry

        caching_required = False

        if not self.current_app_is_admin():
            # We do not need i18n for a tree rendered in Admin dropdown.
            alias = self.resolve_tree_i18n_alias(alias)

        sitetree = get_cache_entry('sitetrees', alias)

        if not sitetree:
            sitetree = (
                MODEL_TREE_ITEM_CLASS.objects.
                select_related('parent', 'tree').
                prefetch_related('access_permissions__content_type').
                filter(tree__alias__exact=alias).
                order_by('parent__sort_order', 'sort_order'))

            sitetree = self.attach_dynamic_tree_items(alias, sitetree)
            set_cache_entry('sitetrees', alias, sitetree)
            caching_required = True

        parents = get_cache_entry('parents', alias)
        if not parents:
            parents = defaultdict(list)
            for item in sitetree:
                parent = getattr(item, 'parent')
                parents[parent].append(item)
            set_cache_entry('parents', alias, parents)

        # Prepare items by ids cache if needed.
        if caching_required:
            # We need this extra pass to avoid future problems on items depth calculation.
            for item in sitetree:
                cache_.update_entry_value('items_by_ids', alias, {item.id: item})

        for item in sitetree:
            if caching_required:
                item.has_children = False

                if not hasattr(item, 'depth'):
                    item.depth = self.calculate_item_depth(alias, item.id)
                item.depth_range = range(item.depth)

                # Resolve item permissions.
                if item.access_restricted:
                    permissions_src = (
                        item.permissions if getattr(item, 'is_dynamic', False)
                        else item.access_permissions.all())

                    item.perms = set(
                        ['%s.%s' % (perm.content_type.app_label, perm.codename) for perm in permissions_src])

            # Contextual properties.
            item.url_resolved = self.url(item)
            item.title_resolved = LazyTitle(item.title) if VARIABLE_TAG_START in item.title else item.title
            item.is_current = False
            item.in_current_branch = False

        # Get current item for the given sitetree.
        self.get_tree_current_item(alias)

        # Save sitetree data into cache if needed.
        if caching_required:
            cache_.save()

        return alias, sitetree

    def calculate_item_depth(self, tree_alias, item_id, depth=0):
        """Calculates depth of the item in the tree.

        :param str|unicode tree_alias:
        :param int item_id:
        :param int depth:
        :rtype: int
        """
        item = self.get_item_by_id(tree_alias, item_id)

        if hasattr(item, 'depth'):
            depth = item.depth + depth
        else:
            if item.parent is not None:
                depth = self.calculate_item_depth(tree_alias, item.parent.id, depth + 1)

        return depth

    def get_item_by_id(self, tree_alias, item_id):
        """Get the item from the tree by its ID.

        :param str|unicode tree_alias:
        :param int item_id:
        :rtype: TreeItemBase
        """
        return self.cache.get_entry('items_by_ids', tree_alias)[item_id]

    def get_tree_current_item(self, tree_alias):
        """Resolves current tree item of 'tree_alias' tree matching current
        request path against URL of given tree item.

        :param str|unicode tree_alias:
        :rtype: TreeItemBase
        """
        current_item = self._current_items.get(tree_alias, _UNSET)

        if current_item is not _UNSET:

            if current_item is not None:
                current_item.is_current = True  # Could be reset by .get_sitetree()

            return current_item

        current_item = None

        if self.current_app_is_admin():
            self._current_items[tree_alias] = current_item
            return None

        # urlquote is an attempt to support non-ascii in url.
        current_url = urlquote(self.current_request.path)

        for url_item, url in self._items_urls.items():
            # Iterate each as this dict may contains "current" items for various trees.
            if url != current_url:
                continue

            url_item.is_current = True
            if url_item.tree.alias == tree_alias:
                current_item = url_item

        if current_item is not None:
            self._current_items[tree_alias] = current_item

        return current_item

    def url(self, sitetree_item, context=None):
        """Resolves item's URL.

        :param TreeItemBase sitetree_item: TreeItemBase heir object, 'url' property of which
            is processed as URL pattern or simple URL.

        :param Context context:

        :rtype: str|unicode
        """
        context = context or self.current_page_context

        if not isinstance(sitetree_item, MODEL_TREE_ITEM_CLASS):
            sitetree_item = self.resolve_var(sitetree_item, context)

        resolved_url = self._items_urls.get(sitetree_item)
        if resolved_url is not None:
            return resolved_url

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

                    # We enclose arg in double quotes as already resolved.
                    all_arguments.append('"%s"' % resolved)

                view_path = view_path[0].strip('"\' ')

            if _URL_TAG_NEW_STYLE:
                view_path = "'%s'" % view_path

            url_pattern = '%s %s' % (view_path, ' '.join(all_arguments))
        else:
            url_pattern = '%s' % sitetree_item.url

        if sitetree_item.urlaspattern:
            # Form token to pass to Django 'url' tag.
            url_token = 'url %s as item.url_resolved' % url_pattern
            url_tag(
                Parser(None),
                Token(token_type=TOKEN_BLOCK, contents=url_token)
            ).render(context)

            resolved_url = context['item.url_resolved'] or UNRESOLVED_ITEM_MARKER

        else:
            resolved_url = url_pattern

        self._items_urls[sitetree_item] = resolved_url

        return resolved_url

    def init_tree(self, tree_alias, context):
        """Initializes sitetree in memory.

        Returns tuple with resolved tree alias and items on success.

        On fail returns (None, None).

        :param str|unicode tree_alias:
        :param Context context:
        :rtype: tuple
        """
        request = context.get('request', None)

        if request is None:
            raise SiteTreeError(
                'Sitetree requires "django.core.context_processors.request" template context processor to be active. '
                'If it is, check that your view pushes request data into the template.')

        if id(request) != id(self.current_request):
            self.init(context)

        # Resolve tree_alias from the context.
        tree_alias = self.resolve_var(tree_alias)
        tree_alias, sitetree_items = self.get_sitetree(tree_alias)

        if not sitetree_items:
            return None, None

        return tree_alias, sitetree_items

    def get_current_page_title(self, tree_alias, context):
        """Returns resolved from sitetree title for current page.

        :param str|unicode tree_alias:
        :param Context context:
        :rtype: str|unicode
        """
        return self.get_current_page_attr('title_resolved', tree_alias, context)

    def get_current_page_attr(self, attr_name, tree_alias, context):
        """Returns an arbitrary attribute of a sitetree item resolved as current for current page.

        :param str|unicode attr_name:
        :param str|unicode tree_alias:
        :param Context context:
        :rtype: str|unicode
        """
        tree_alias, sitetree_items = self.init_tree(tree_alias, context)
        current_item = self.get_tree_current_item(tree_alias)

        if current_item is None:
            if settings.DEBUG and RAISE_ITEMS_ERRORS_ON_DEBUG:
                raise SiteTreeError(
                    'Unable to resolve current sitetree item to get a `%s` for current page. Check whether '
                    'there is an appropriate sitetree item defined for current URL.' % attr_name)

            return ''

        return getattr(current_item, attr_name, '')

    def get_ancestor_level(self, current_item, depth=1):
        """Returns ancestor of level `deep` recursively

        :param TreeItemBase current_item:
        :param int depth:
        :rtype: TreeItemBase
        """
        if current_item.parent is None:
            return current_item

        if depth <= 1:
            return current_item.parent

        return self.get_ancestor_level(current_item.parent, depth=depth-1)

    def menu(self, tree_alias, tree_branches, context):
        """Builds and returns menu structure for 'sitetree_menu' tag.

        :param str|unicode tree_alias:
        :param str|unicode tree_branches:
        :param Context context:
        :rtype: list|str
        """
        tree_alias, sitetree_items = self.init_tree(tree_alias, context)

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
                branch_id = self.get_ancestor_level(current_item, depth=2).id
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

        menu_items = self.apply_hook(menu_items, 'menu')
        self.update_has_children(tree_alias, menu_items, 'menu')
        return menu_items

    @classmethod
    def apply_hook(cls, items, sender):
        """Applies item processing hook, registered with ``register_item_hook()``
        to items supplied, and returns processed list.

        Returns initial items list if no hook is registered.

        :param list items:
        :param str|unicode sender: menu, breadcrumbs, sitetree, {type}.children, {type}.has_children
        :rtype: list
        """
        if _ITEMS_PROCESSOR is None:
            return items

        return _ITEMS_PROCESSOR(tree_items=items, tree_sender=sender)

    def check_access(self, item, context):
        """Checks whether a current user has an access to a certain item.

        :param TreeItemBase item:
        :param Context context:
        :rtype: bool
        """
        authenticated = self.current_request.user.is_authenticated()

        if item.access_loggedin and not authenticated:
            return False

        if item.access_guest and authenticated:
            return False

        if item.access_restricted:
            user_perms = self._current_user_permissions

            if user_perms is _UNSET:
                user_perms = set(context['user'].get_all_permissions())
                self._current_user_permissions = user_perms

            if item.access_perm_type == MODEL_TREE_ITEM_CLASS.PERM_TYPE_ALL:
                if len(item.perms) != len(item.perms.intersection(user_perms)):
                    return False
            else:
                if not len(item.perms.intersection(user_perms)):
                    return False

        return True

    def breadcrumbs(self, tree_alias, context):
        """Builds and returns breadcrumb trail structure for 'sitetree_breadcrumbs' tag.

        :param str|unicode tree_alias:
        :param Context context:
        :rtype: list|str
        """
        tree_alias, sitetree_items = self.init_tree(tree_alias, context)

        if not sitetree_items:
            return ''

        current_item = self.get_tree_current_item(tree_alias)

        breadcrumbs = []

        if current_item is not None:

            context_ = self.current_page_context
            check_access = self.check_access
            get_item_by_id = self.get_item_by_id

            def climb(base_item):
                """Climbs up the site tree to build breadcrumb path.

                :param TreeItemBase base_item:
                """
                if base_item.inbreadcrumbs and not base_item.hidden and check_access(base_item, context_):
                    breadcrumbs.append(base_item)

                if hasattr(base_item, 'parent') and base_item.parent is not None:
                    climb(get_item_by_id(tree_alias, base_item.parent.id))

            climb(current_item)
            breadcrumbs.reverse()

        items = self.apply_hook(breadcrumbs, 'breadcrumbs')
        self.update_has_children(tree_alias, items, 'breadcrumbs')

        return items

    def tree(self, tree_alias, context):
        """Builds and returns tree structure for 'sitetree_tree' tag.

        :param str|unicode tree_alias:
        :param Context context:
        :rtype: list|str
        """
        tree_alias, sitetree_items = self.init_tree(tree_alias, context)

        if not sitetree_items:
            return ''

        tree_items = self.filter_items(self.get_children(tree_alias, None), 'sitetree')
        tree_items = self.apply_hook(tree_items, 'sitetree')
        self.update_has_children(tree_alias, tree_items, 'sitetree')

        return tree_items

    def children(self, parent_item, navigation_type, use_template, context):
        """Builds and returns site tree item children structure for 'sitetree_children' tag.

        :param TreeItemBase parent_item:
        :param str|unicode navigation_type: menu, sitetree
        :param str|unicode use_template:
        :param Context context:
        :rtype: list
        """
        # Resolve parent item and current tree alias.
        parent_item = self.resolve_var(parent_item, context)
        tree_alias, tree_items = self.get_sitetree(parent_item.tree.alias)

        # Mark path to current item.
        self.tree_climber(tree_alias, self.get_tree_current_item(tree_alias))

        tree_items = self.get_children(tree_alias, parent_item)
        tree_items = self.filter_items(tree_items, navigation_type)
        tree_items = self.apply_hook(tree_items, '%s.children' % navigation_type)
        self.update_has_children(tree_alias, tree_items, navigation_type)

        my_template = get_template(use_template)

        context.push()
        context['sitetree_items'] = tree_items
        rendered = my_template.render(context)
        context.pop()

        return rendered

    def get_children(self, tree_alias, item):
        """Returns item's children.

        :param str|unicode tree_alias:
        :param TreeItemBase|None item:
        :rtype: list
        """
        if not self.current_app_is_admin():
            # We do not need i18n for a tree rendered in Admin dropdown.
            tree_alias = self.resolve_tree_i18n_alias(tree_alias)

        return self.cache.get_entry('parents', tree_alias)[item]

    def update_has_children(self, tree_alias, tree_items, navigation_type):
        """Updates 'has_children' attribute for tree items inplace.

        :param str|unicode tree_alias:
        :param list tree_items:
        :param str|unicode navigation_type: sitetree, breadcrumbs, menu
        """
        for tree_item in tree_items:
            children = self.get_children(tree_alias, tree_item)
            children = self.filter_items(children, navigation_type)
            children = self.apply_hook(children, '%s.has_children' % navigation_type)
            tree_item.has_children = len(children) > 0

    def filter_items(self, items, navigation_type=None):
        """Filters sitetree item's children if hidden and by navigation type.

        NB: We do not apply any filters to sitetree in admin app.

        :param list items:
        :param str|unicode navigation_type: sitetree, breadcrumbs, menu
        :rtype: list
        """
        if self.current_app_is_admin():
            return items

        items_filtered = []

        context = self.current_page_context
        check_access = self.check_access

        for item in items:
            if item.hidden:
                continue

            if not check_access(item, context):
                continue

            if not getattr(item, 'in%s' % navigation_type, True):  # Hidden for current nav type
                continue

            items_filtered.append(item)

        return items_filtered

    def get_ancestor_item(self, tree_alias, base_item):
        """Climbs up the site tree to resolve root item for chosen one.

        :param str|unicode tree_alias:
        :param TreeItemBase base_item:
        :rtype: TreeItemBase
        """
        parent = None

        if hasattr(base_item, 'parent') and base_item.parent is not None:
            parent = self.get_ancestor_item(tree_alias, self.get_item_by_id(tree_alias, base_item.parent.id))

        if parent is None:
            return base_item

        return parent

    def tree_climber(self, tree_alias, base_item):
        """Climbs up the site tree to mark items of current branch.

        :param str|unicode tree_alias:
        :param TreeItemBase base_item:
        """
        if base_item is not None:
            base_item.in_current_branch = True
            if hasattr(base_item, 'parent') and base_item.parent is not None:
                self.tree_climber(tree_alias, self.get_item_by_id(tree_alias, base_item.parent.id))

    def resolve_var(self, varname, context=None):
        """Resolves name as a variable in a given context.

        If no context specified page context' is considered as context.

        :param str|unicode varname:
        :param Context context:
        :return:
        """
        context = context or self.current_page_context

        if isinstance(varname, FilterExpression):
            varname = varname.resolve(context)
        else:
            varname = varname.strip()

            try:
                varname = Variable(varname).resolve(context)
            except VariableDoesNotExist:
                varname = varname

        return varname
