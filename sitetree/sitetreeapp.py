from collections import defaultdict
from copy import copy

from django.conf import settings
from django import template
from django.core.cache import cache
from django.db.models import signals
from django.utils.http import urlquote
from django.utils.translation import get_language
from django.template.defaulttags import url as url_tag

from models import Tree, TreeItem

# Sitetree objects are stored in Django cache for a year (60 * 60 * 24 * 365 = 31536000 sec).
# Cache is only invalidated on sitetree or sitetree item change.
CACHE_TIMEOUT = 31536000

# Holds tree items processor callable or None.
_ITEMS_PROCESSOR = None
# Holds aliases of trees that support internationalization.
_I18N_TREES = []


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


class SiteTree(object):

    def __init__(self):
        self.cache = None
        # This points to global sitetree context.
        self.global_context = None
        # Listen for signals from the models.
        signals.post_save.connect(self.cache_empty, sender=Tree)
        signals.post_save.connect(self.cache_empty, sender=TreeItem)
        signals.post_delete.connect(self.cache_empty, sender=TreeItem)
        # Listen to the changes in item permissions table.
        signals.m2m_changed.connect(self.cache_empty, sender=TreeItem.access_permissions)

    def cache_init(self):
        """Initializes local cache from Django cache."""
        cache_ = cache.get('sitetrees')
        if cache_ is None:
            # Init cache dictionary with predefined enties.
            cache_ = {'sitetrees': {}, 'urls': {}, 'parents': {}, 'items_by_ids': {}, 'tree_aliases': {}}
        self.cache = cache_

    def cache_save(self):
        """Saves sitetree data to Django cache."""
        cache.set('sitetrees', self.cache, CACHE_TIMEOUT)

    def cache_empty(self, **kwargs):
        """Empties cached sitetree data."""
        self.cache = False
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

    def set_global_context(self, context):
        """Saves context as global context if not already set or if changed.
        Almost all variables are resolved against global context.

        """
        if not self.global_context or hash(context) != hash(self.global_context):
            self.global_context = context

    def resolve_tree_i18_alias(self, alias):
        """Resolves internationalized tree alias.
        Verifies whether a separate sitetree is available for currently active language.
        If so, returns i18n alias. If not, returns the initial alias.
        """
        if alias in _I18N_TREES:
            current_language_code = get_language().replace('_', '-').split('-')[0]
            i18n_tree_alias = '%s_%s' % (alias, current_language_code)
            trees_count = self.get_cache_entry('tree_aliases', i18n_tree_alias)
            if trees_count is False:
                trees_count = Tree.objects.filter(alias=i18n_tree_alias).count()
                self.set_cache_entry('tree_aliases', i18n_tree_alias, trees_count)
            if trees_count:
                alias = i18n_tree_alias
        return alias

    def get_sitetree(self, alias):
        """Gets site tree items from the given site tree.
        Caches result to dictionary.
        Returns items.

        """
        self.cache_init()
        sitetree_needs_caching = False
        alias = self.resolve_tree_i18_alias(alias)
        sitetree = self.get_cache_entry('sitetrees', alias)
        if not sitetree:
            sitetree = TreeItem.objects.select_related('parent', 'tree').\
                   filter(tree__alias__exact=alias).order_by('parent', 'sort_order')
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
            item.title_resolved = item.title
            item.is_current = False
            item.in_current_branch = False

        # Get current item for the given sitetree.
        self.get_tree_current_item(alias)
        # Parse titles.
        self.parse_titles(sitetree)

        # Save sitetree data into cache if needed.
        if sitetree_needs_caching:
            self.cache_save()

        return sitetree

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
        current_item = None

        if 'request' not in self.global_context and self.global_context.current_app != 'admin':
            raise SiteTreeError('Sitetree needs "django.core.context_processors.request" to be in TEMPLATE_CONTEXT_PROCESSORS in your settings file. If it is, check that your view pushes request data into the template.')
        else:
            # urlquote is a try to support non-ascii in url.
            current_url = urlquote(self.global_context['request'].path)
            urls_cache = self.get_cache_entry('urls', tree_alias)
            if urls_cache:
                for url_item in urls_cache:
                    urls_cache[url_item][1].is_current = False
                    if urls_cache[url_item][0] == current_url:
                        current_item = urls_cache[url_item][1]

        if current_item is not None:
            current_item.is_current = True

        return current_item

    def url(self, sitetree_item, tag_arguments=[], context=None):
        """Resolves item's URL.

        'sitetree_item' points to TreeItem object, 'url' property of which
            is processed as URL pattern or simple URL.

        'tag_arguments' is a list of additional arguments passed to
            'sitetree_url' in template.

        """
        if context is None:
            context = self.global_context

        if not isinstance(sitetree_item, TreeItem):
            sitetree_item = self.resolve_var(sitetree_item, context)

        # Resolve only if item's URL is marked as pattern.
        if sitetree_item.urlaspattern:
            resolved_var = self.resolve_var(sitetree_item.url, context)
            if isinstance(resolved_var, list):
                raise SiteTreeError('Named URL for "%s" sitetree item clashes with template variable name. Please change either name.' % sitetree_item.title)
            view_path = resolved_var.split(' ')
            # We should try to resolve URL parameters from site tree item.
            view_arguments = []
            for view_argument in view_path[1:]:
                resolved = self.resolve_var(view_argument)
                # In case of non-ascii data we leave variable unresolved.
                if isinstance(resolved, unicode):
                    if resolved.encode('ascii', 'ignore').decode('ascii') != resolved:
                        resolved = view_argument

                view_arguments.append(resolved)

            # URL parameters from site tree item should be concatenated with
            # those from template.
            arguments_couled = tag_arguments + view_arguments
            view_arguments = []

            for argument in arguments_couled:
                argument = str(argument)
                # To be able to process slug-like strings (strings with "-"'s and "_"'s)
                # we enclose those in double quotes.
                if '-' in argument or '_':
                    argument = '"%s"' % argument
                view_arguments.append(argument)

            view_arguments = ' '.join(view_arguments).strip()
            view_path = view_path[0]
            url_pattern = u'%s %s' % (view_path, view_arguments)
        else:
            url_pattern = u'%s' % sitetree_item.url

        url_pattern = url_pattern.strip()

        # Create 'cache_urls' for this tree.
        tree_alias = sitetree_item.tree.alias

        entry_from_cache = self.get_cache_entry('urls', tree_alias)
        if not entry_from_cache:
            entry_from_cache = {}
            self.set_cache_entry('urls', tree_alias, {})

        if url_pattern in entry_from_cache:
            resolved_url = entry_from_cache[url_pattern][0]
        else:
            if sitetree_item.urlaspattern:
                # Form token to pass to Django 'url' tag.
                url_token = u'url %s as item.url_resolved' % url_pattern
                url_tag(template.Parser(None),
                        template.Token(token_type=template.TOKEN_BLOCK, contents=url_token)).render(context)

                # We make an anchor link from an unresolved URL as a reminder.
                if context['item.url_resolved'] == '':
                    resolved_url = u'#unresolved'
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
        sitetree_items = self.get_sitetree(tree_alias)
        # No items in tree, fail silently.
        if not sitetree_items:
            return False, False
        return tree_alias, sitetree_items

    def get_current_page_title(self, tree_alias, context):
        """Returns resolved from sitetree title for current page."""
        tree_alias, sitetree_items = self.init_tree(tree_alias, context)
        current_item = self.get_tree_current_item(tree_alias)
        # Current item unresolved, fail silently.
        if current_item is None:
            if settings.DEBUG:
                raise SiteTreeError('Unable to resolve title for current page using sitetree_page_title tag. Check whether there is an appropriate sitetree item defined for current URL.')
            return ''
        return current_item.title_resolved

    def menu(self, tree_alias, tree_branches, context):
        """Builds and returns menu structure for 'sitetree_menu' tag."""
        tree_alias, sitetree_items = self.init_tree(tree_alias, context)
        # No items in tree, fail silently.
        if not sitetree_items:
            return ''
        tree_branches = self.resolve_var(tree_branches)

        # Support item addressing both through identifiers and aliases.
        parent_isnull = False
        parent_ids = []
        parent_aliases = []

        current_item = self.get_tree_current_item(tree_alias)
        self.tree_climber(tree_alias, current_item)

        for branch_id in tree_branches.split(','):
            branch_id = branch_id.strip()
            if branch_id == 'trunk':
                parent_isnull = True
            elif branch_id == 'this-children' and current_item is not None:
                branch_id = current_item.id
                parent_ids.append(branch_id)
            elif branch_id == 'this-ancestor-children' and current_item is not None:
                branch_id = self.get_ancestor_item(tree_alias, current_item).id
                parent_ids.append(branch_id)
            elif branch_id == 'this-siblings' and current_item is not None:
                branch_id = current_item.parent.id
                parent_ids.append(branch_id)
            elif branch_id.isdigit():
                parent_ids.append(branch_id)
            else:
                parent_aliases.append(branch_id)

        menu_items = []
        for item in sitetree_items:
            if item.inmenu and item.hidden == False:
                if self.check_access(item, context):
                    if item.parent is None:
                        if parent_isnull:
                            menu_items.append(item)
                    else:
                        if item.parent.id in parent_ids or item.parent.alias in parent_aliases:
                            menu_items.append(item)

        # Parse titles for variables.
        menu_items = self.parse_titles(menu_items, context)
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
        """Checks whether user have access to certain item."""

        if item.access_loggedin and not self.global_context['request'].user.is_authenticated():
            return False

        if item.access_restricted:
            user_perms = set(context['user'].get_all_permissions())
            if item.access_perm_type == TreeItem.PERM_TYPE_ALL:
                if len(item.perms) != len(item.perms.intersection(user_perms)):
                    return False
            else:
                if len(item.perms.intersection(user_perms)) == 0:
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
        self.get_sitetree(tree_alias)
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
        tree_alias = self.resolve_tree_i18_alias(tree_alias)
        return self.get_cache_entry('parents', tree_alias)[item]

    def update_has_children(self, tree_alias, tree_items, navigation_type):
        """Updates 'has_children' attribute for tree items."""
        items = []
        for tree_item in tree_items:
            children = self.get_children(tree_alias, tree_item)
            children = self.filter_items(children, navigation_type)
            children = self.apply_hook(children, '%s.has_children' % navigation_type)
            tree_item.has_children = len(children)>0
            items.append(tree_item)
        return items

    def filter_items(self, items, navigation_type=None):
        """Filters site tree item's children if hidden and by navigation type.
        NB: We do not apply any filters to sitetree in admin app.
        """
        items_out = copy(items)
        if self.global_context.current_app != 'admin':
            for item in items:
                no_access = not self.check_access(item, self.global_context)
                hidden_for_nav_type = navigation_type is not None and getattr(item, 'in' + navigation_type, False) != True
                if item.hidden == True or no_access or hidden_for_nav_type:
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
                                                                                         self.global_context):
            self.cache_breadcrumbs.append(start_from)
        if hasattr(start_from, 'parent') and start_from.parent is not None:
            self.breadcrumbs_climber(tree_alias, self.get_item_by_id(tree_alias, start_from.parent.id))

    def resolve_var(self, varname, context=None):
        """Tries to resolve name as a variable in a given context.
        If no context specified 'global_context' is considered
        as context.

        """
        if context is None:
            context = self.global_context

        if isinstance(varname, template.FilterExpression):
            varname = varname.resolve(context)
        else:
            varname = varname.strip()

            try:
                varname = template.Variable(varname).resolve(context)
            except template.VariableDoesNotExist:
                varname = varname

        return varname

    def parse_titles(self, items, context=None):
        """Walks through the list of items, and resolves any variable found
        in a title of an item.

        We deliberately strip down template tokens that are not text or variable.
        There is definitely no need nor purpose in blocks or comments in a title.
        Why to think otherwise, if only you're a villain. Joke here.

        Returns the list with resolved titles.

        """
        if context is None:
            context = self.global_context

        for item in items:
            if item.title.find(template.VARIABLE_TAG_START) != -1:
                my_lexer = template.Lexer(item.title, template.UNKNOWN_SOURCE)
                my_tokens = my_lexer.tokenize()

                for my_token in my_tokens:
                    if my_token.token_type not in (template.TOKEN_TEXT, template.TOKEN_VAR):
                        my_tokens.remove(my_token)

                my_parser = template.Parser(my_tokens)
                item.title_resolved = my_parser.parse().render(context)

        return items


class SiteTreeError(Exception):
    """Exception class for sitetree application."""
    pass
