# Generated by Django 2.2.16 on 2021-04-01 07:11

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("wombles", "0002_add_initial_profiles")]

    operations = [
        migrations.AlterModelOptions(
            name="wombletags", options={"ordering": ("label",)}
        )
    ]
