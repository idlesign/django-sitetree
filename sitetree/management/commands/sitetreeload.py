import sys
from optparse import make_option
from collections import defaultdict

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connections, router, transaction, DEFAULT_DB_ALIAS
from django.core.exceptions import ObjectDoesNotExist

from sitetree.models import Tree, TreeItem


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a specific database to load fixtures into. '
                    'Defaults to the "default" database.'),
        make_option('--mode', action='store', dest='mode',
            default='append', help='Mode to put data into DB. Variants: `replace`, `append`.'),
        make_option('--items_into_tree', action='store', dest='into_tree',
            default=None, help='Import only tree items data into tree with given alias.'),
        )
    help = 'Loads sitetrees from fixture in JSON format into database.'
    args = '[fixture_file fixture_file ...]'


    def handle(self, *fixture_files, **options):

        using = options.get('database', DEFAULT_DB_ALIAS)
        mode = options.get('mode', 'append')
        items_into_tree = options.get('into_tree', None)

        if items_into_tree is not None:
            try:
                items_into_tree = Tree.objects.get(alias=items_into_tree)
            except ObjectDoesNotExist:
                raise CommandError('Target tree alised by `%s` does not exist. Please create it before import.' %
                                   items_into_tree)
            else:
                mode = 'append'

        connection = connections[using]
        cursor = connection.cursor()

        self.style = no_style()

        transaction.commit_unless_managed(using=using)
        transaction.enter_transaction_management(using=using)
        transaction.managed(True, using=using)

        loaded_object_count = 0

        if mode == 'replace':
            try:
                Tree.objects.all().delete()
                TreeItem.objects.all().delete()
            except ObjectDoesNotExist:
                pass

        for fixture_file in fixture_files:

            self.stdout.write('Loading fixture from `%s` ...\n' % fixture_file)

            fixture = file(fixture_file, 'r')

            try:
                objects = serializers.deserialize('json', fixture, using=using)
            except (SystemExit, KeyboardInterrupt):
                raise

            trees = []
            tree_items = defaultdict(list)
            tree_item_parents = defaultdict(list)
            tree_items_new_indexes = {}

            for obj in objects:
                if router.allow_syncdb(using, obj.object.__class__):
                    if isinstance(obj.object, (Tree, TreeItem)):
                        if isinstance(obj.object, Tree):
                            trees.append(obj.object)
                        else:
                            if items_into_tree is not None:
                                obj.object.tree_id = items_into_tree.id
                            tree_items[obj.object.tree_id].append(obj.object)
                            tree_item_parents[obj.object.parent_id].append(obj.object.id)

            if items_into_tree is not None:
                trees = [items_into_tree,]

            try:

                for tree in trees:

                    self.stdout.write('\nImporting tree `%s` ...\n' % tree.alias)
                    orig_tree_id = tree.id

                    if items_into_tree is None:
                        if mode == 'append':
                            tree.pk = None
                            tree.id = None

                        tree.save(using=using)
                        loaded_object_count += 1

                    parents_ahead = []

                    for tree_item in tree_items[orig_tree_id]:
                        parent_ahead = False
                        self.stdout.write('Importing item `%s` ...\n' % tree_item.title)
                        tree_item.tree_id = tree.id
                        orig_item_id = tree_item.id

                        if mode == 'append':
                            tree_item.pk = None
                            tree_item.id = None

                            if tree_item.id in tree_items_new_indexes:
                                tree_item.pk = tree_item.id = tree_items_new_indexes[tree_item.id]

                            if tree_item.parent_id is not None:
                                if tree_item.parent_id in tree_items_new_indexes:
                                    tree_item.parent_id = tree_items_new_indexes[tree_item.parent_id]
                                else:
                                    parent_ahead = True

                        tree_item.save(using=using)
                        loaded_object_count += 1

                        if mode == 'append':
                            tree_items_new_indexes[orig_item_id] = tree_item.id
                            if parent_ahead:
                                parents_ahead.append(tree_item)

                    # Second pass is necessary for tree items being imported before their parents.
                    for tree_item in parents_ahead:
                        tree_item.parent_id = tree_items_new_indexes[tree_item.parent_id]
                        tree_item.save(using=using)

            except (SystemExit, KeyboardInterrupt):
                raise

            except Exception:
                import traceback
                fixture.close()
                transaction.rollback(using=using)
                transaction.leave_transaction_management(using=using)
                self.stderr.write(
                    self.style.ERROR('Fixture `%s` import error: %s\n' % (fixture_file,
                          ''.join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))))
                )

            fixture.close()

        # Reset DB sequences, for DBMS with sequences support.
        if loaded_object_count > 0:
            sequence_sql = connection.ops.sequence_reset_sql(self.style, [Tree, TreeItem])
            if sequence_sql:
                self.stdout.write('Resetting DB sequences ...\n')
                for line in sequence_sql:
                    cursor.execute(line)

        transaction.commit(using=using)
        transaction.leave_transaction_management(using=using)

        connection.close()
