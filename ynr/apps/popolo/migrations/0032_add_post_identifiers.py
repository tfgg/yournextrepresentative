# Generated by Django 2.2.4 on 2020-01-15 13:06

import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("popolo", "0031_other_names_unique_constraint")]

    operations = [
        migrations.AddField(
            model_name="post",
            name="identifier",
            field=models.CharField(
                help_text="\n        The identifier used in EveryElection for this division. This might\n        change over time, as some divisions don't have official IDs at the\n        point we create them.\n        ",
                max_length=100,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="post",
            name="territory_code",
            field=models.CharField(
                blank=True,
                help_text="\n        The territory within Great Britain that this post is in.\n        One of SCT, WLS, ENG, NIR\n        ",
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name="PostIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("identifier", models.CharField(max_length=256)),
                ("label", models.CharField(blank=True, max_length=255)),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="popolo.Post",
                    ),
                ),
            ],
            options={"abstract": False},
        ),
    ]
