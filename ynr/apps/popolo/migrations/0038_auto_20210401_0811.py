# Generated by Django 2.2.16 on 2021-04-01 07:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("popolo", "0037_data_migration_add_party_name")]

    operations = [
        migrations.AlterModelOptions(
            name="othername", options={"ordering": ("name",)}
        )
    ]