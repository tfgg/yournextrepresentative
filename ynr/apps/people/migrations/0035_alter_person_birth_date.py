# Generated by Django 3.2.4 on 2021-10-25 16:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("people", "0034_get_birth_year")]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="birth_date",
            field=models.CharField(
                blank=True,
                help_text="A year of birth",
                max_length=4,
                verbose_name="birth date",
            ),
        )
    ]
