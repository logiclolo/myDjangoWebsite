# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ynm', '0002_camera_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='camera',
            name='ip',
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='camera',
            name='passwd',
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='camera',
            name='platform',
            field=models.IntegerField(null=True),
        ),
    ]
