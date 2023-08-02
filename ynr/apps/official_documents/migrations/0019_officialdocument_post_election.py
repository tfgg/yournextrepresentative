# Generated by Django 1.9.13 on 2018-04-06 10:22


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("candidates", "0041_auto_20180323_1400"),
        ("official_documents", "0018_make_source_url_required"),
    ]

    operations = [
        migrations.AddField(
            model_name="officialdocument",
            name="post_election",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="candidates.PostExtraElection",
            ),
        )
    ]
