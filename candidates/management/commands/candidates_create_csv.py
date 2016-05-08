from __future__ import unicode_literals

from collections import defaultdict
from os import chmod, rename
from os.path import dirname
from tempfile import NamedTemporaryFile

from django.core.management.base import BaseCommand, CommandError
from django.db.models import F

from candidates.csv_helpers import list_to_csv
from candidates.models import PersonExtra
from elections.models import Election


class Command(BaseCommand):

    help = "Output CSV files for all elections"

    def add_arguments(self, parser):
        parser.add_argument(
            'OUTPUT-PREFIX',
            help='The prefix for output filenames'
        )
        parser.add_argument(
            '--site-base-url',
            help='The base URL of the site (for full image URLs)'
        )
        parser.add_argument(
            '--election',
            metavar='ELECTION-SLUG',
            help='Only output CSV for the election with this slug'
        )

    def handle(self, **options):
        if options['election']:
            try:
                all_elections = [Election.objects.get(slug=options['election'])]
            except Election.DoesNotExist:
                message = "Couldn't find an election with slug {election_slug}"
                raise CommandError(message.format(election_slug=options['election']))
        else:
            all_elections = list(Election.objects.all()) + [None]
        people_by_election = defaultdict(list)

        for election in all_elections:
            if election is None:
                # Get information for every candidate in every
                # election.  Unfortunately this may not be well
                # defined when mapping to CSV, since it's conceivable
                # that someone is standing in two different current
                # elections taking place on the same date.  This file
                # is only generated so that the same files are
                # generated by YourNextMP - we probably shouldn't
                # generate it in the future.
                for person_extra in PersonExtra.objects.all():
                    people_by_election[None] += person_extra.as_list_of_dicts(
                        None,
                        base_url=options['site_base_url']
                    )
            else:
                # This is the well-defined case - get all the
                # candidates for a particular election.
                for person_extra in PersonExtra.objects.filter(
                        base__memberships__extra__election=election,
                        base__memberships__role=election.candidate_membership_role
                ).select_related('base'):
                    people_by_election[election.slug].append(
                        person_extra.as_list_of_dicts(
                            election,
                            base_url=options['site_base_url']
                        )
                    )

        for election in all_elections:
            if election is None:
                output_filename = \
                    options['OUTPUT-PREFIX'] + '-all.csv'
                election_slug = None
            else:
                output_filename = \
                    options['OUTPUT-PREFIX'] + '-' + election.slug + '.csv'
                election_slug = election.slug
            people_data = people_by_election[election_slug]
            csv = list_to_csv(people_data)
            # Write to a temporary file and atomically rename into place:
            ntf = NamedTemporaryFile(
                delete=False,
                dir=dirname(output_filename)
            )
            ntf.write(csv.encode('utf-8'))
            chmod(ntf.name, 0o644)
            rename(ntf.name, output_filename)
