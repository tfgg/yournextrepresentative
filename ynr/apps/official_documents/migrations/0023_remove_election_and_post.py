# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-06 08:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("official_documents", "0022_python_3_changes")]

    operations = [
        migrations.RemoveField(model_name="officialdocument", name="election"),
        migrations.RemoveField(model_name="officialdocument", name="post"),
    ]
