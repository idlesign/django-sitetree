# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sitetree', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='treeitem',
            name='url_params',
            field=models.CharField(help_text='Additional URL parameters (see "Additional settings") for this item.', max_length=200, verbose_name='URL Parameters', db_index=True, blank=True),
        ),
    ]
