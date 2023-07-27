# Generated by Django 3.2.12 on 2022-05-11 11:22
from candidates.models.db import LoggedAction
from django.db import migrations


def populate_version_fields(apps, schema):
    queryset = LoggedAction.objects.filter(person__isnull=False).select_related(
        "person"
    )
    for logged_action in queryset.iterator():
        version_id = logged_action.popit_person_new_version
        logged_action.version_fields = logged_action.person.version_fields(
            version_id
        )
        logged_action.save()


class Migration(migrations.Migration):

    dependencies = [("people", "0039_auto_20220428_1635")]

    operations = []
