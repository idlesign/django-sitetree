from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from sitetree.utils import get_tree_model, get_tree_item_model, import_sitetrees


MODEL_TREE_CLASS = get_tree_model()


class Command(BaseCommand):

    help = 'Places sitetrees of the project applications (defined in `app_name.sitetree.py`) into DB, replacing old ones if any.'
    args = '[app_name app_name ...]'
    option_list = BaseCommand.option_list + (
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a specific database to place trees and items into. Defaults to the "default" database.'),
        )

    def handle(self, *apps, **options):
        using = options.get('database', DEFAULT_DB_ALIAS)

        trees_modules = import_sitetrees()
        for module in trees_modules:
            sitetrees = getattr(module, 'sitetrees', None)
            app = module.__dict__['__package__']
            if not apps or (apps and app in apps):
                if sitetrees is not None:
                    self.stdout.write('Sitetrees found in `%s` app ...\n' % app)
                    for tree in sitetrees:
                        self.stdout.write('  Processing `%s` tree ...\n' % tree.alias)
                        # Delete trees with the same name beforehand.
                        MODEL_TREE_CLASS.objects.filter(alias=tree.alias).using(using).delete()
                        tree.id = None
                        tree.save(using=using)
                        for item in tree.dynamic_items:
                            self.stdout.write('    Adding `%s` tree item ...\n' % item.title)
                            item.tree = tree
                            item.save(using=using)
