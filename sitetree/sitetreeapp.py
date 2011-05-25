from collections import defaultdict
from copy import copy

from django.conf import settings
from django import template
from django.db.models import signals
from django.utils.http import urlquote
from django.template.defaulttags import url as url_tag

from models import Tree, TreeItem


class SiteTree():

    def __init__(self):
        # This points to global sitetree context.
        self.global_context = None
        # Cache. This stores all requested sitetrees with items.
        self.cache_sitetrees = {}
        # Cache. Current tree item - tree item resolved for current page.
        self.cache_current_item = {}
        # Cache. Relations between item title and its rendered name.
        self.cache_titles = {}
        # Cache. Relations between item url and its resolved form.
        self.cache_urls = {}
        # Cache. Breadcrumb path.
        self.cache_breadcrumbs = {}
        # Cache. Tree structures as lists.
        self.cache_treestruct = {}
        # Cache. Parents mappings.
        self.cache_parents = {}
        # Cache. Utility dictionary with site tree items indexed by IDs.
        self.cache_items_by_ids = {}
        # Listen for signals from the models.
        signals.post_save.connect(self.cache_flush_tree, sender=Tree)
        signals.post_save.connect(self.cache_flush_tree, sender=TreeItem)
        signals.post_delete.connect(self.cache_flush_tree, sender=TreeItem)
        # Listen to the changes in item permissions table.
        signals.m2m_changed.connect(self.cache_flush_tree, sender=TreeItem.access_permissions)

    def set_global_context(self, context):
        """Saves context as global context if not already set or if changed.
        Almost all variables are resolved against global context.

        """
        if not self.global_context or hash(context) != hash(self.global_context):
            self.global_context = context
            self.cache_flush_contextual_data()

    def get_sitetree(self, alias):
        """Gets site tree items from the given site tree.
        Caches result to dictionary.
        Returns items.

        """
        if alias in self.cache_sitetrees:
            sitetree = self.cache_sitetrees[alias]
        else:
            sitetree = self.cache_sitetrees[alias] = TreeItem.objects.select_related('parent', 'tree').filter(
                tree__alias__exact=alias).order_by('parent', 'sort_order')

        # Create shortcuts dictionary.
        self.link_items_to_ids(alias)

        for sitetree_item in sitetree:
            if not hasattr(sitetree_item, 'depth'):
                sitetree_item.depth = self.calculate_item_depth(alias, sitetree_item.id)
            sitetree_item.depth_range = range(sitetree_item.depth)
            # Resolve item's URL.
            sitetree_item.url_resolved = self.url(sitetree_item)
            # Resolve item permissions.
            sitetree_item.perms = set([u'%s.%s' % (perm.content_type.app_label, perm.codename) for perm in
                                       sitetree_item.access_permissions.select_related()])

        # Generate parents mappings.
        self.get_parents(alias)
        # Get current item for the given sitetree.
        self.get_tree_current_item(alias)
        # Parse titles.
        self.parse_titles(sitetree)

        return sitetree

    def calculate_item_depth(self, tree_alias, item_id, depth=0):
        """Calculates depth of the item in the tree."""
        item = self.get_item_by_id(tree_alias, item_id)
        if not hasattr(item, 'depth'):
            if item.parent is not None:
                depth = self.calculate_item_depth(tree_alias, item.parent.id, depth + 1)
        else:
            depth = item.depth + 1
        return depth

    def link_items_to_ids(self, tree_alias):
        """Creates utility shortcuts dictionary where tree items indexed by IDs."""
        if tree_alias not in self.cache_items_by_ids:
            self.cache_items_by_ids[tree_alias] = {}
            for item in self.cache_sitetrees[tree_alias]:
                self.cache_items_by_ids[tree_alias][item.id] = item

    def get_item_by_id(self, tree_alias, item_id):
        """Get the item from the tree by its ID."""
        return self.cache_items_by_ids[tree_alias][item_id]

    def get_parents(self, tree_alias):
        """Creates parents mappings."""
        if tree_alias not in self.cache_parents:
            # Group items under parents
            parents = defaultdict(list)

            for item in self.cache_sitetrees[tree_alias]:
                item.has_children = False
                parent = getattr(item, 'parent')
                parents[parent].append(item)
            self.cache_parents[tree_alias] = parents

            for item in self.cache_sitetrees[tree_alias]:
                if item in parents:
                    item.has_children = True

        else:
            parents = self.cache_parents[tree_alias]

        return parents

    def get_tree_current_item(self, tree_alias):
        """Resolves current tree item of 'tree_alias' tree matching current
        request path against URL of given tree item.

        """
        current_item = None

        if tree_alias in self.cache_current_item:
            current_item = self.cache_current_item[tree_alias]
        else:
            if 'request' not in self.global_context and self.global_context.current_app != 'admin':
                raise SiteTreeError('Sitetree needs "django.core.context_processors.request" template processor to be enabled. Please add it to TEMPLATE_CONTEXT_PROCESSORS in your settings file.')
            else:
                # urlquote is a try to support non-ascii in url.
                current_url = urlquote(self.global_context['request'].path)
                if tree_alias in self.cache_urls:
                    for url_item in self.cache_urls[tree_alias]:
                        self.cache_urls[tree_alias][url_item][1].is_current = False
                        if self.cache_urls[tree_alias][url_item][0] == current_url:
                            current_item = self.cache_urls[tree_alias][url_item][1]

            self.cache_current_item[tree_alias] = current_item

        if current_item is not None:
            current_item.is_current = True

        return current_item

    def url(self, sitetree_item, tag_arguments=[], context=None):
        """Resolves item's URL.

        'sitetree_item' points to TreeItem object, 'url' property of which
            is processed as URL pattern or simple URL.

        'tag_arguments' id a list of additional arguments passed to
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
                    if resolved.encode("ascii", "ignore").decode("ascii") != resolved:
                        resolved = view_argument

                view_arguments.append(resolved)

            # URL parameters from site tree item should be concatenated with
            # those from template.
            view_arguments = tag_arguments + view_arguments
            view_arguments = [str(view_argument) for view_argument in view_arguments]
            view_arguments = ' '.join(view_arguments).strip()
            view_path = view_path[0]
            url_pattern = u'%s %s' % (view_path, view_arguments)
        else:
            url_pattern = u'%s' % sitetree_item.url

        url_pattern = url_pattern.strip()

        # Create 'cache_urls' for this tree.
        tree_alias = sitetree_item.tree.alias
        if tree_alias not in self.cache_urls:
            self.cache_urls[tree_alias] = {}

        if url_pattern in self.cache_urls[tree_alias]:
            resolved_url = self.cache_urls[tree_alias][url_pattern][0]
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

            self.cache_urls[tree_alias][url_pattern] = (resolved_url, sitetree_item)
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

        for branch_id in tree_branches.split(','):
            branch_id = branch_id.strip()
            if branch_id == 'trunk':
                parent_isnull = True
            elif branch_id == 'this-children' and current_item is not None:
                branch_id = current_item.id
                parent_ids.append(branch_id)
            elif branch_id == 'this-siblings' and current_item is not None:
                branch_id = current_item.parent.id
                parent_ids.append(branch_id)
            elif branch_id.isdigit():
                parent_ids.append(branch_id)
            elif branch_id.isalnum():
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
        return menu_items

    def check_access(self, item, context):
        """Checks whether user have access to certain item."""
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
        trail_items = []
        if current_item is not None:
            trail_items = self.get_breadcrumbs(tree_alias, current_item)
        return trail_items

    def tree(self, tree_alias, context):
        """Builds and returns tree structure for 'sitetree_tree' tag."""
        tree_alias, sitetree_items = self.init_tree(tree_alias, context)
        # No items in tree, fail silently.
        if not sitetree_items:
            return ''
        tree_items = self.get_children(tree_alias, None)
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
        tree_items = self.get_children(tree_alias, parent_item)
        tree_items = self.filter_items(tree_items, navigation_type)
        my_template = template.loader.get_template(use_template)
        my_context = template.Context({'sitetree_items': tree_items, 'user': context['user']})
        return my_template.render(my_context)

    def get_children(self, tree_alias, item):
        return self.cache_parents[tree_alias][item]

    def filter_items(self, items, navigation_type=None):
        """Filters site tree item's children if hidden and by navigation type.
        NB: We do not apply any filters to sitetree in admin app.

        """
        items = copy(items)
        if self.global_context.current_app != 'admin':
            for item in items:
                if item.hidden == True ^ (not self.check_access(item, self.global_context)) ^ (
                navigation_type is not None and getattr(item, 'in' + navigation_type) != True):
                    items.remove(item)
        return items

    def get_breadcrumbs(self, tree_alias, start_item):
        """Returns breadcrumb path to the given 'start_item' site tree item."""
        if tree_alias not in self.cache_breadcrumbs:
            self.cache_breadcrumbs[tree_alias] = []

        if self.cache_breadcrumbs[tree_alias]:
            breadcrumbs = self.cache_breadcrumbs[tree_alias]
        else:
            self.tree_climber(tree_alias, start_item)
            self.cache_breadcrumbs[tree_alias].reverse()
            breadcrumbs = self.cache_breadcrumbs[tree_alias]

        return breadcrumbs

    def tree_climber(self, tree_alias, start_from):
        """Climbs up the site tree to build breadcrumb path."""
        if start_from.inbreadcrumbs and start_from.hidden == False and self.check_access(start_from,
                                                                                         self.global_context):
            self.cache_breadcrumbs[tree_alias].append(start_from)
        if hasattr(start_from, 'parent') and start_from.parent is not None:
            self.tree_climber(tree_alias, self.get_item_by_id(tree_alias, start_from.parent.id))

    def resolve_var(self, varname, context=None):
        """Tries to resolve name as a variable in a given context.
        If no context specified 'global_context' is considered
        as context.

        """
        if context is None:
            context = self.global_context

        # Variable names are not empty do not allow commas and spaces.
        varname = varname.strip()
        if varname != ''  and varname.find(' ') == -1 and ',' not in varname:
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
            if not hasattr(item, 'title_resolved'):
                item.title_resolved = item.title

            if item.title in self.cache_titles:
                item.title_resolved = self.cache_titles[item.title]
            else:
                if item.title.find(template.VARIABLE_TAG_START) != -1:
                    my_lexer = template.Lexer(item.title, template.UNKNOWN_SOURCE)
                    my_tokens = my_lexer.tokenize()

                    for my_token in my_tokens:
                        if my_token.token_type not in (template.TOKEN_TEXT, template.TOKEN_VAR):
                            my_tokens.remove(my_token)

                    my_parser = template.Parser(my_tokens)
                    item.title_resolved = my_parser.parse().render(context)
                self.cache_titles[item.title] = item.title_resolved
        return items

    def cache_flush_contextual_data(self, **kwargs):
        """Flushes cached site tree items titles data."""
        self.cache_current_item = {}
        self.cache_titles = {}
        self.cache_breadcrumbs = {}

    def cache_flush_tree(self, **kwargs):
        """Flushes cached site tree data."""
        self.cache_sitetrees = {}
        self.cache_current_item = {}
        self.cache_titles = {}
        self.cache_breadcrumbs = {}
        self.cache_urls = {}
        self.cache_parents = {}
        self.cache_items_by_ids = {}


class SiteTreeError(Exception):
    """Exception class for sitetree application."""
    pass
