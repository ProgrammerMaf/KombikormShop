# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-01-07 07:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AnimalFeed', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photos',
            name='picture',
            field=models.ImageField(upload_to='pictures'),
        ),
    ]
