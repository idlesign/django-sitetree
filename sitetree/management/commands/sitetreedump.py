from optparse import make_option

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS

from sitetree.models import Tree, TreeItem


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--indent', default=None, dest='indent', type='int',
            help='Specifies the indent level to use when pretty-printing output.'),
        make_option('--items_only', action='store_true', dest='items_only', default=False,
            help='Export tree items only.'),
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a specific database to export fixtures from. '
                    'Defaults to the "default" database.'),
        )
    help = 'Output sitetrees from database as a fixture in JSON format.'
    args = '[tree_alias tree_alias ...]'

    def handle(self, *aliases, **options):

        indent = options.get('indent', None)
        using = options.get('database', DEFAULT_DB_ALIAS)
        items_only = options.get('items_only', False)

        objects = []

        if aliases:
            trees = Tree._default_manager.using(using).filter(alias__in=aliases)
        else:
            trees = Tree._default_manager.using(using).all()

        if not items_only:
            objects.extend(trees)

        for tree in trees:
            objects.extend(TreeItem._default_manager.using(using).filter(tree=tree).order_by('parent'))

        try:
            return serializers.serialize('json', objects, indent=indent)
        except Exception, e:
            raise CommandError('Unable to serialize sitetree(s): %s' % e)
