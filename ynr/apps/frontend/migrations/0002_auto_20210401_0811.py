# Generated by Django 2.2.16 on 2021-04-01 07:11

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("frontend", "0001_initial")]

    operations = [
        migrations.AlterModelOptions(
            name="sitebanner", options={"get_latest_by": "modified"}
        )
    ]
