# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-29 15:34
from __future__ import unicode_literals

from django.db import migrations

ROLES_BY_TYPE = {
    "parl": "UK Parliament elections",
    "nia": "Northern Ireland Assembly elections",
    "naw": "National Assembly for Wales elections",
    "sp": "Scottish Parliament elections",
    "gla": "Greater London Assembly elections",
    "local": "Local elections",
    "pcc": "Police and Crime Commissioner elections",
    "mayor": "Mayoral elections",
}


def update_for_post_role(apps, schema_editor):
    Election = apps.get_model("elections", "Election")
    for election_type, text in ROLES_BY_TYPE.items():
        Election.objects.filter(slug__startswith=election_type).update(
            for_post_role=text
        )


class Migration(migrations.Migration):
    dependencies = [("elections", "0013_remove_area")]

    operations = [
        migrations.RunPython(update_for_post_role, migrations.RunPython.noop)
    ]
