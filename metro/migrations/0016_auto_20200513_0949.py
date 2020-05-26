# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-05-13 07:49
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('metro', '0015_auto_20200513_0941'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indicator',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]