# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-09-20 15:41
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("candidates", "0049_cleanup_post_extra"),
        ("popolo", "0022_populate_person_image_from_image"),
        ("results", "0023_migrate_winner_party_to_party_model"),
    ]

    operations = [
        migrations.RemoveField(model_name="organizationextra", name="base"),
        migrations.DeleteModel(name="OrganizationExtra"),
    ]
