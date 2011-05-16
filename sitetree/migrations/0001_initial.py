# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Tree'
        db.create_table('sitetree_tree', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('alias', self.gf('django.db.models.fields.CharField')(unique=True, max_length=80, db_index=True)),
        ))
        db.send_create_signal('sitetree', ['Tree'])

        # Adding model 'TreeItem'
        db.create_table('sitetree_treeitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('hint', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('urlaspattern', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('tree', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sitetree.Tree'])),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('alias', self.gf('sitetree.models.CharFieldNullable')(db_index=True, max_length=80, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('inmenu', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('inbreadcrumbs', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('insitetree', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sitetree.TreeItem'], null=True, blank=True)),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
        ))
        db.send_create_signal('sitetree', ['TreeItem'])

        # Adding unique constraint on 'TreeItem', fields ['tree', 'alias']
        db.create_unique('sitetree_treeitem', ['tree_id', 'alias'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'TreeItem', fields ['tree', 'alias']
        db.delete_unique('sitetree_treeitem', ['tree_id', 'alias'])

        # Deleting model 'Tree'
        db.delete_table('sitetree_tree')

        # Deleting model 'TreeItem'
        db.delete_table('sitetree_treeitem')


    models = {
        'sitetree.tree': {
            'Meta': {'object_name': 'Tree'},
            'alias': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'sitetree.treeitem': {
            'Meta': {'unique_together': "(('tree', 'alias'),)", 'object_name': 'TreeItem'},
            'alias': ('sitetree.models.CharFieldNullable', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'hint': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inbreadcrumbs': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'inmenu': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'insitetree': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sitetree.TreeItem']", 'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tree': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sitetree.Tree']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'urlaspattern': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'})
        }
    }

    complete_apps = ['sitetree']
