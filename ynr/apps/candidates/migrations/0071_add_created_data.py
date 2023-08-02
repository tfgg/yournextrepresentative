# Generated by Django 2.2.20 on 2021-06-17 14:08

from django.db import migrations
from elections.helpers import four_weeks_before_election_date


def add_created_date(apps, schema_editor):
    Ballot = apps.get_model("candidates", "Ballot")
    for ballot in Ballot.objects.select_related("election").iterator():
        ballot.created = four_weeks_before_election_date(
            election=ballot.election
        )
        ballot.save()


class Migration(migrations.Migration):
    dependencies = [("candidates", "0070_auto_20210617_1506")]

    operations = [
        migrations.RunPython(
            code=add_created_date, reverse_code=migrations.RunPython.noop
        )
    ]
