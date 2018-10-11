# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-21 21:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("popolo", "0012_move_post_extra_data_to_base"),
        ("candidates", "0048_move_pee_postextra_to_post"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="postextraelection",
            unique_together=set([("election", "post")]),
        ),
        migrations.RemoveField(model_name="postextra", name="base"),
        migrations.RemoveField(model_name="postextra", name="elections"),
        migrations.RemoveField(model_name="postextra", name="party_set"),
        migrations.RemoveField(
            model_name="postextraelection", name="postextra"
        ),
        migrations.AlterField(
            model_name="postextraelection",
            name="post",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="popolo.Post"
            ),
        ),
        migrations.DeleteModel(name="PostExtra"),
    ]