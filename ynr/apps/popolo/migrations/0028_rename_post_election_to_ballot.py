# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-07-15 16:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0014_remove_person_email"),
        ("candidates", "0058_pee_to_ballot"),
        ("popolo", "0027_slug_org_unique_together"),
        ("parties", "0011_add_initial_candidates_counts"),
    ]

    operations = [
        migrations.RenameField(
            model_name="membership", old_name="post_election", new_name="ballot"
        ),
        migrations.AlterUniqueTogether(
            name="membership", unique_together={("person", "ballot")}
        ),
    ]
