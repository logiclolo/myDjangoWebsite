# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ynm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='camera',
            name='account',
            field=models.CharField(max_length=16, null=True),
        ),
    ]
