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
            name='placeholder',
            field=models.BooleanField(help_text='Whether to show this item without a link, making it a non-clickable placeholder.', verbose_name='Show as placeholder', default=False),
            preserve_default=True,
        ),
    ]
