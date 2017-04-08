# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Article(models.Model):

    title = models.CharField('Title', max_length=200, blank=False)
    date_created = models.DateTimeField('Created', auto_created=True)
    contents = models.TextField('Contents')

    def __str__(self):
        return self.title


customized_sitetree_models = False

if customized_sitetree_models:

    from sitetree.models import TreeItemBase, TreeBase


    class MyTree(TreeBase):

        custom_field = models.CharField('Custom tree field', max_length=50, null=True, blank=True)


    class MyTreeItem(TreeItemBase):

        custom_field = models.IntegerField('Custom item field', default=42)
