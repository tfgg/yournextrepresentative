# Generated by Django 2.2.4 on 2019-11-13 22:37

from django.db import migrations


def populate_edit_types(apps, schema_editor):
    LoggedAction = apps.get_model("candidates", "LoggedAction")
    KNOWN_BOT_USERS = ["CandidateBot", "ResultsBot", "TwitterBot"]

    LoggedAction.objects.filter(user__username__in=KNOWN_BOT_USERS).update(
        edit_type="BOT"
    )


class Migration(migrations.Migration):
    dependencies = [("candidates", "0062_loggedaction_edit_type")]

    operations = [
        migrations.RunPython(populate_edit_types, migrations.RunPython.noop)
    ]
