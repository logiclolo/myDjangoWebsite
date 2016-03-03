# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Camera',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('maintainer', models.CharField(max_length=16)),
                ('macaddr', models.CharField(max_length=16)),
                ('modelname', models.CharField(max_length=16)),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('time', models.DateTimeField(verbose_name=b'date generated')),
                ('content', models.FileField(upload_to=b'')),
                ('camera', models.ForeignKey(to='ynm.Camera')),
            ],
        ),
    ]
