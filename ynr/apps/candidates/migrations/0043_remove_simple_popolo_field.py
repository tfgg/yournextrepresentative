# Generated by Django 1.9.13 on 2018-05-21 14:47


from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("candidates", "0042_loggedaction_post_election"),
        ("uk", "0004_add_biography"),
    ]

    operations = [migrations.DeleteModel(name="SimplePopoloField")]
