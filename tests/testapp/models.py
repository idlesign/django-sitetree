from django.db import models


class MyModel(models.Model):

    afield = models.CharField('my', max_length=20)

    def __str__(self):
        return self.afield
