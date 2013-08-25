from django import template
from django.forms import ChoiceField
from django.utils.safestring import mark_safe

from .templatetags.sitetree import sitetree_tree
from .utils import get_tree_model, get_tree_item_model


MODEL_TREE_CLASS = get_tree_model()
MODEL_TREE_ITEM_CLASS = get_tree_item_model()


class TreeItemChoiceField(ChoiceField):
    """Generic sitetree item field.
    Customized ChoiceField with TreeItems of a certain tree.

    Accepts the `tree` kwarg - tree model or alias.
    Use `initial` kwarg to set initial sitetree item by its ID.

    """

    template = 'admin/sitetree/tree/tree_combo.html'
    root_title = '---------'

    def __init__(self, tree, required=True, widget=None, label=None, initial=None, help_text=None, *args, **kwargs):
        super(TreeItemChoiceField, self).__init__(required=required, widget=widget, label=label, initial=initial,
                                                  help_text=help_text, *args, **kwargs)
        if isinstance(tree, MODEL_TREE_CLASS):
            tree = tree.alias
        self.tree = tree
        self.choices = self._build_choices()

    def _build_choices(self):
        """Build choices list runtime using 'sitetree_tree' tag"""
        tree_token = u'sitetree_tree from "%s" template "%s"' % (self.tree, self.template)
        choices_str = sitetree_tree(template.Parser(None),
                                    template.Token(token_type=template.TOKEN_BLOCK,
                                                   contents=tree_token)).render(template.Context(current_app='admin'))
        tree_choices = [('', self.root_title)]
        for line in choices_str.splitlines():
            if line.strip():
                splitted = line.split(':::')
                tree_choices.append((splitted[0], mark_safe(splitted[1])))
        return tree_choices

    def clean(self, value):
        if not value:
            return None
        return MODEL_TREE_ITEM_CLASS.objects.get(pk=value)
