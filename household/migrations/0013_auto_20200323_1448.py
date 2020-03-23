# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-03-23 12:48
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scorecard', '0003_geography_population'),
        ('household', '0012_auto_20200323_1420'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='householdbilltotal',
            unique_together=set([('geography', 'financial_year', 'budget_phase', 'household_class', 'total')]),
        ),
    ]