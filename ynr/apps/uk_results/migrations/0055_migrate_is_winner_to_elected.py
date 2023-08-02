# Generated by Django 2.2.18 on 2021-05-13 15:33

from django.db import migrations


def forwards(apps, schema_editor):
    """
    Ensures that for every candidate result we have we store the definitive True
    or False value for if they were elected against the related candidacy before
    we throw this data away in next migration to remove the is_winner field
    """
    Membership = apps.get_model("popolo", "Membership")
    # get memberships where we have a result but elected isnt set
    memberships = Membership.objects.filter(result__isnull=False, elected=None)
    # seperate winners and losers
    winners = memberships.filter(result__is_winner=True)
    losers = memberships.filter(result__is_winner=False)
    # update accordingly
    winners.update(elected=True)
    losers.update(elected=False)
    # using update avoids the modified timestamp being updated


def backwards(apps, schema_editor):
    """
    Applies the reverse of the above - takes the elected value, and stores it
    against the result object
    """
    CandidateResult = apps.get_model("uk_results", "CandidateResult")
    winners = CandidateResult.objects.filter(membership__elected=True)
    losers = CandidateResult.objects.filter(membership__elected=False)
    winners.update(is_winner=True)
    losers.update(is_winner=False)


class Migration(migrations.Migration):
    dependencies = [("uk_results", "0054_update_is_winner_to_elected")]

    operations = [migrations.RunPython(code=forwards, reverse_code=backwards)]
