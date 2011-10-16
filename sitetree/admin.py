from django import template
from django.forms import ChoiceField
from django.conf.urls.defaults import patterns, url
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.contrib import admin
from django.contrib import messages

from models import Tree, TreeItem
from templatetags.sitetree import sitetree_tree


class TreeItemAdmin(admin.ModelAdmin):
    exclude = ('tree', 'sort_order')
    fieldsets = (
        (_('Basic settings'), {
            'fields': ('parent', 'title', 'url',)
        }),
        (_('Access settings'), {
            'classes': ('collapse',),
            'fields': ('access_loggedin', 'access_restricted', 'access_permissions', 'access_perm_type')
        }),
        (_('Display settings'), {
            'classes': ('collapse',),
            'fields': ('hidden', 'inmenu', 'inbreadcrumbs', 'insitetree')
        }),
        (_('Additional settings'), {
            'classes': ('collapse',),
            'fields': ('hint', 'description', 'alias', 'urlaspattern')
        }),
    )
    filter_horizontal = ('access_permissions',)

    def response_add(self, request, obj, post_url_continue='../item_%s/'):
        """Redirects to the appropriate items' 'continue' page on item add.

        As we administer tree items within tree itself, we
        should make some changes to redirection process.

        """
        return super(TreeItemAdmin, self).response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        """Redirects to the appropriate items' 'add' page on item change.

        As we administer tree items within tree itself, we
        should make some changes to redirection process.

        """
        response = super(TreeItemAdmin, self).response_change(request, obj)
        if '_addanother' in request.POST:
            return HttpResponseRedirect('../item_add/')
        elif '_save' in request.POST:
            return HttpResponseRedirect('../')
        return response

    def get_form(self, request, obj=None, **kwargs):
        """Returns modified form for TreeItem model.
        'Parent' field choices are built by sitetree itself.

        """

        class TreeItemChoiceField(ChoiceField):
            """We use custom ChoiceField as to have a chance to
            resolve TreeItem by ID from dropdown.

            """
            def clean(self, value):
                if value == '':
                    return None

                return TreeItem.objects.get(pk=value)

        # We build choices dropdown using 'sitetree_tree' tag
        tree_token = u'sitetree_tree from "%s" template "admin/sitetree/tree/tree_combo.html"' % self.tree.alias
        my_context = template.RequestContext(request, current_app='admin')
        choices_str = sitetree_tree(template.Parser(None),
                                    template.Token(token_type=template.TOKEN_BLOCK, contents=tree_token)).render(my_context)

        tree_choices = [('', '---------')]
        for line in choices_str.splitlines():
            if line.strip() != '':
                splitted = line.split(':::')
                tree_choices.append((splitted[0], mark_safe(splitted[1])))

        if obj is not None and obj.parent is not None:
            self.previous_parent = obj.parent
            previous_parent_id = self.previous_parent.id
        else:
            previous_parent_id = None

        my_choice_field = TreeItemChoiceField(choices=tree_choices, initial=previous_parent_id)
        form = super(TreeItemAdmin, self).get_form(request, obj, **kwargs)
        my_choice_field.label = form.base_fields['parent'].label
        my_choice_field.help_text = form.base_fields['parent'].help_text
        # Replace 'parent' TreeItem field with new appropriate one
        form.base_fields['parent'] = my_choice_field
        return form

    def get_tree(self, tree_id):
        """Fetches Tree for current TreeItem."""
        self.tree = Tree._default_manager.get(pk=tree_id)
        return self.tree

    def item_add(self, request, tree_id):
        tree = self.get_tree(tree_id)
        return self.add_view(request)

    def item_edit(self, request, tree_id, item_id):
        tree = self.get_tree(tree_id)
        return self.change_view(request, item_id, extra_context={'tree': tree})

    def item_delete(self, request, tree_id, item_id):
        tree = self.get_tree(tree_id)
        return self.delete_view(request, item_id)

    def item_history(self, request, tree_id, item_id):
        tree = self.get_tree(tree_id)
        return self.history_view(request, item_id)

    def item_move(self, request, tree_id, item_id, direction):
        """Moves item up or down by swapping 'sort_order' field values of neighboring items."""
        current_item = TreeItem._default_manager.get(pk=item_id)
        if direction == 'up':
            sort_order = 'sort_order'
        else:
            sort_order = '-sort_order'
        siblings = TreeItem._default_manager.filter(parent=current_item.parent).order_by(sort_order)

        previous_item = None
        for item in siblings:
            if item != current_item:
                previous_item = item
            else:
                break

        if previous_item is not None:
            current_item_sort_order = current_item.sort_order
            previous_item_sort_order = previous_item.sort_order

            current_item.sort_order = previous_item_sort_order
            previous_item.sort_order = current_item_sort_order

            current_item.save()
            previous_item.save()

        return HttpResponseRedirect('../../')

    def save_model(self, request, obj, form, change):
        """Saves TreeItem model under certain Tree.
        Handles item's parent assignment exception.

        """
        if change:
            # No, you're not allowed to make item parent of itself
            if obj.parent is not None and obj.parent.id == obj.id:
                obj.parent = self.previous_parent
                messages.warning(request, _("Item's parent left unchanged. Item couldn't be parent to itself."), '', True)
        obj.tree = self.tree
        obj.save()


def redirects_handler(*args, **kwargs):
    """Fixes Admin contrib redirects compatibility problems
    introduced in Django 1.4 by url handling changes.

    """
    referer = args[0].META['HTTP_REFERER']
    shift = '../'

    if 'delete' in referer:
        # Weird enough 'delete' is not handled by TreeItemAdmin::response_change().
        shift += '../'
    elif 'history' in referer:
        if 'item_id' not in kwargs:
            # Encountered request from history page to return to tree layout page.
            shift += '../'

    return HttpResponseRedirect(referer + shift)


class TreeAdmin(admin.ModelAdmin):
    list_display = ('alias',)
    search_fields = ['alias']
    ordering = ['alias']
    actions = None

    tree_admin = TreeItemAdmin(TreeItem, admin.site)

    def get_urls(self):
        """Manages not only TreeAdmin URLs but also TreeItemAdmin URLs."""
        urls = super(TreeAdmin, self).get_urls()

        sitetree_urls = patterns('',
            # Django 1.4 Admin contrib new url handling workarounds below.
            # Sitetree item redirect on 'save' and breadcrumbs fix.
            url(r'^p_tree/$', redirects_handler, name='sitetree_treeitem_changelist'),
            # Sitetree item history breadcrumbs fix.
            url(r'^p_tree/(?P<item_id>\d+)', redirects_handler),
            # Sitetree item redirect on 'save and add another' fix.
            # Note that this is a stab, as actual redirect happens in TreeItemAdmin::response_change().
            url(r'^dummy_another$', lambda x: x, name='sitetree_treeitem_add'),

            (r'^(?P<tree_id>\d+)/item_add/$', self.admin_site.admin_view(self.tree_admin.item_add)),
            (r'^(?P<tree_id>\d+)/item_(?P<item_id>\d+)/$', self.admin_site.admin_view(self.tree_admin.item_edit)),
            (r'^(?P<tree_id>\d+)/item_(?P<item_id>\d+)/history/$', self.admin_site.admin_view(self.tree_admin.item_history)),
            (r'^(?P<tree_id>\d+)/item_(?P<item_id>\d+)/delete/$', self.admin_site.admin_view(self.tree_admin.item_delete)),
            (r'^(?P<tree_id>\d+)/item_(?P<item_id>\d+)/move_(?P<direction>(up|down))/$', self.admin_site.admin_view(self.tree_admin.item_move)),
        )
        return sitetree_urls + urls


admin.site.register(Tree, TreeAdmin)
