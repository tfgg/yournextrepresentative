# Generated by Django 3.2.4 on 2021-12-07 17:14

from django.db import migrations


def forwards(apps, schema_editor):
    Membership = apps.get_model("popolo", "Membership")

    for candidacy in Membership.objects.filter(party_name=""):
        candidacy.party_name = candidacy.party.name
        candidacy.save()


class Migration(migrations.Migration):
    dependencies = [("popolo", "0044_add_indexes_to_modified")]

    operations = [
        migrations.RunPython(
            code=forwards, reverse_code=migrations.RunPython.noop
        )
    ]
