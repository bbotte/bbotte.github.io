from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Reporter(models.Model):
    full_name = models.CharField(max_length=70)
    def __str__(self):
        return self.full_name

class Artical(models.Model):
    pub_date = models.DateField()
    headline = models.CharField(max_length=200)
    content = models.TextField()
    reporter = models.ForeignKey(Reporter)
    def __str__(self):
        return self.headline
