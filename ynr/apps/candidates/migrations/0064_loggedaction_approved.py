# Generated by Django 2.2.4 on 2019-11-16 10:59

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("candidates", "0063_populate_loggedaction_edit_types")]

    operations = [
        migrations.AddField(
            model_name="loggedaction",
            name="approved",
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        )
    ]