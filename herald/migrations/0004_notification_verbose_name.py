# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-29 17:19
from __future__ import unicode_literals

import re

from django.db import migrations, models


def populate_verbose_name(apps, schema_editor):
    Notification = apps.get_model('herald', 'Notification')
    for notification in Notification.objects.all():
        notification.verbose_name = re.sub(
            r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))',
            r' \1',
            notification.notification_class
        )
        notification.save()


class Migration(migrations.Migration):
    dependencies = [
        ('herald', '0003_auto_20161021_1448'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='verbose_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.RunPython(populate_verbose_name),
    ]