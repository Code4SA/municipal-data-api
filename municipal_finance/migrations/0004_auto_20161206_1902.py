# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-12-06 17:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('municipal_finance', '0003_demarcationchanges'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demarcationchanges',
            name='new_code',
            field=models.TextField(db_index=True),
        ),
        migrations.AlterField(
            model_name='demarcationchanges',
            name='new_code_transition',
            field=models.TextField(db_index=True),
        ),
        migrations.AlterField(
            model_name='demarcationchanges',
            name='old_code',
            field=models.TextField(db_index=True),
        ),
        migrations.AlterField(
            model_name='demarcationchanges',
            name='old_code_transition',
            field=models.TextField(db_index=True),
        ),
    ]