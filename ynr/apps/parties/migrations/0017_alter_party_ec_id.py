# Generated by Django 3.2.12 on 2022-03-11 14:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("parties", "0016_enable_levenshtein")]

    operations = [
        migrations.AlterField(
            model_name="party",
            name="ec_id",
            field=models.CharField(
                db_index=True,
                help_text="\n            An ID issued by The Electoral Commission in their party register,\n            with the exception of Democracy Club psuedo IDs for special parties\n        ",
                max_length=25,
                unique=True,
                verbose_name="Electoral Commission Idenfitier",
            ),
        )
    ]
