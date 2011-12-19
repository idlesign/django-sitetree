from django import template
from django import VERSION
from django.templatetags.static import PrefixNode

from ..sitetreeapp import SiteTree

register = template.Library()

# All utility methods are implemented in SiteTree class
sitetree = SiteTree()

DJANGO_VERSION_INT = int('%s%s%s' % VERSION[:3])


@register.tag
def sitetree_tree(parser, token):
    """Parses sitetree tag parameters.

    Two notation types are possible:
        1. Two arguments:
           {% sitetree_tree from "mytree" %}
           Used to render tree for "mytree" site tree.

        2. Four arguments:
           {% sitetree_tree from "mytree" template "sitetree/mytree.html" %}
           Used to render tree for "mytree" site tree using specific
           template "sitetree/mytree.html"

    """
    tokens = token.split_contents()
    use_template = detect_clause(parser, 'template', tokens)
    tokens_num = len(tokens)

    if tokens_num in (3, 5):
        tree_alias = parser.compile_filter(tokens[2])
        return sitetree_treeNode(tree_alias, use_template)
    else:
        raise template.TemplateSyntaxError, "%r tag requires two arguments. E.g. {%% sitetree_tree from \"mytree\" %%}." % tokens[0]


@register.tag
def sitetree_children(parser, token):
    """Parses sitetree_children tag parameters.

       Six arguments:
           {% sitetree_children of someitem for menu template "sitetree/mychildren.html" %}
           Used to render child items of specific site tree 'someitem'
           using template "sitetree/mychildren.html" for menu navigation.

           Basically template argument should contain path to current template itself.

           Allowed navigation types: 1) menu; 2) sitetree.

    """
    tokens = token.split_contents()
    use_template = detect_clause(parser, 'template', tokens)
    tokens_num = len(tokens)

    if tokens_num == 5 and tokens[1] == 'of' and tokens[3] == 'for' and tokens[4] in ('menu', 'sitetree') and use_template is not None:
        tree_item = tokens[2]
        navigation_type = tokens[4]
        return sitetree_childrenNode(tree_item, navigation_type, use_template)
    else:
        raise template.TemplateSyntaxError, "%r tag requires six arguments. E.g. {%% sitetree_children of someitem for menu template \"sitetree/mychildren.html\" %%}." % tokens[0]


@register.tag
def sitetree_breadcrumbs(parser, token):
    """Parses sitetree_breadcrumbs tag parameters.

    Two notation types are possible:
        1. Two arguments:
           {% sitetree_breadcrumbs from "mytree" %}
           Used to render breadcrumb path for "mytree" site tree.

        2. Four arguments:
           {% sitetree_breadcrumbs from "mytree" template "sitetree/mycrumb.html" %}
           Used to render breadcrumb path for "mytree" site tree using specific
           template "sitetree/mycrumb.html"

    """
    tokens = token.split_contents()
    use_template = detect_clause(parser, 'template', tokens)
    tokens_num = len(tokens)

    if tokens_num == 3:
        tree_alias = parser.compile_filter(tokens[2])
        return sitetree_breadcrumbsNode(tree_alias, use_template)
    else:
        raise template.TemplateSyntaxError, "%r tag requires two arguments. E.g. {%% sitetree_breadcrumbs from \"mytree\" %%}." % tokens[0]


@register.tag
def sitetree_menu(parser, token):
    """Parses sitetree_menu tag parameters.

        {% sitetree_menu from "mytree" include "trunk,1,level3" %}
        Used to render trunk, branch with id 1 and branch aliased 'level3'
        elements from "mytree" site tree as a menu.

        These are reserved aliases:
            * 'trunk' - items without parents
            * 'this-children' - items under item resolved as current for the current page
            * 'this-siblings' - items under parent of item resolved as current for
              the current page (current item included)
            * 'this-ancestor-children' - items under grandparent item (closest to root)
              for the item resolved as current for the current page

        {% sitetree_menu from "mytree" include "trunk,1,level3" template "sitetree/mymenu.html" %}

    """
    tokens = token.split_contents()
    use_template = detect_clause(parser, 'template', tokens)
    tokens_num = len(tokens)

    if tokens_num == 5 and tokens[3] == 'include':
        tree_alias = parser.compile_filter(tokens[2])
        tree_branches = parser.compile_filter(tokens[4])
        return sitetree_menuNode(tree_alias, tree_branches, use_template)
    else:
        raise template.TemplateSyntaxError, "%r tag requires four arguments. E.g. {%% sitetree_menu from \"mytree\" include \"trunk,1,level3\" %%}." % tokens[0]


@register.tag
def sitetree_url(parser, token):
    """This tag is much the same as Django built-in 'url' tag.
    The difference is that after 'for' it should get TreeItem object.
    And, yes, you can pass some arguments after that TreeItem object.

    """
    tokens = token.contents.split()
    tokens_num = len(tokens)

    if tokens_num >= 3 and tokens[1] == 'for':
        sitetree_item = parser.compile_filter(tokens[2])
        tag_arguments = map(parser.compile_filter, tokens[3:])
        return sitetree_urlNode(sitetree_item, tag_arguments)
    else:
        raise template.TemplateSyntaxError, "%r tag should look like {%% sitetree_url for someitem params %%}." % tokens[0]


@register.tag
def sitetree_page_title(parser, token):
    """Renders title for current page, resolved against sitetree item
    representing current URL.

    """
    tokens = token.split_contents()

    if len(tokens) == 3:
        tree_alias = parser.compile_filter(tokens[2])
        return sitetree_page_titleNode(tree_alias)
    else:
        raise template.TemplateSyntaxError, "%r tag requires two arguments. E.g. {%% sitetree_page_title from \"mytree\" %%}." % tokens[0]


@register.simple_tag
def sitetree_admin_img_url_prefix():
    """Returns static admin images URL prefix. """
    if DJANGO_VERSION_INT >= 140:
        return '%sadmin/img' % PrefixNode.handle_simple('STATIC_URL')

    return '%simg/admin' % PrefixNode.handle_simple('ADMIN_MEDIA_PREFIX')


class sitetree_treeNode(template.Node):
    """Renders tree items from specified site tree."""

    def __init__(self, tree_alias, use_template):
        self.use_template = use_template
        self.tree_alias = tree_alias

    def render(self, context):
        tree_items = sitetree.tree(self.tree_alias, context)
        return render(context, tree_items, self.use_template or 'sitetree/tree.html')


class sitetree_childrenNode(template.Node):
    """Renders tree items under specified parent site tree item."""

    def __init__(self, tree_item, navigation_type, use_template):
        self.use_template = use_template
        self.tree_item = tree_item
        self.navigation_type = navigation_type

    def render(self, context):
        return sitetree.children(self.tree_item, self.navigation_type, self.use_template.resolve(context), context)


class sitetree_breadcrumbsNode(template.Node):
    """Renders breadcrumb trail items from specified site tree."""

    def __init__(self, tree_alias, use_template):
        self.use_template = use_template
        self.tree_alias = tree_alias

    def render(self, context):
        tree_items = sitetree.breadcrumbs(self.tree_alias, context)
        return render(context, tree_items, self.use_template or 'sitetree/breadcrumbs.html')


class sitetree_menuNode(template.Node):
    """Renders specified site tree menu items."""

    def __init__(self, tree_alias, tree_branches, use_template):
        self.use_template = use_template
        self.tree_alias = tree_alias
        self.tree_branches = tree_branches

    def render(self, context):
        tree_items = sitetree.menu(self.tree_alias, self.tree_branches, context)
        return render(context, tree_items, self.use_template or 'sitetree/menu.html')


class sitetree_urlNode(template.Node):
    """Resolves and renders specified url."""

    def __init__(self, sitetree_item, tag_arguments):
        self.sitetree_item = sitetree_item
        self.tag_arguments = tag_arguments

    def render(self, context):
        resolved_url = sitetree.url(self.sitetree_item, self.tag_arguments, context)
        return resolved_url


class sitetree_page_titleNode(template.Node):
    """Renders page title from specified site tree."""

    def __init__(self, tree_alias):
        self.tree_alias = tree_alias

    def render(self, context):
        return sitetree.get_current_page_title(self.tree_alias, context)


def detect_clause(parser, clause_name, tokens):
    """Helper function detects a certain clause in tag tokens list.
    Returns its value.

    """
    if clause_name in tokens:
        t_index = tokens.index(clause_name)
        clause_value = parser.compile_filter(tokens[t_index + 1])
        del tokens[t_index:t_index + 2]
    else:
        clause_value = None
    return clause_value


def render(context, tree_items, use_template):
    """Render helper is used by template node functions
    to render given template with given tree items in context.

    """
    context.push()
    context['sitetree_items'] = tree_items

    if isinstance(use_template, template.FilterExpression):
        use_template = use_template.resolve(context)

    content = template.loader.get_template(use_template).render(context)
    context.pop()

    return content
