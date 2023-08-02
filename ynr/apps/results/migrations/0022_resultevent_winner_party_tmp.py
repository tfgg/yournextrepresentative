# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-09-05 19:27
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("results", "0021_resultevent_retraction"),
        ("parties", "0008_unique_ec_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="resultevent",
            name="winner_party_tmp",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="parties.Party",
            ),
        )
    ]
