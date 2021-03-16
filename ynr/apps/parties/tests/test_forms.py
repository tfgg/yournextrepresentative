from django.core.exceptions import ValidationError
from django.test import TestCase

from django import forms

from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from parties.forms import PartyIdentifierField, PopulatePartiesMixin
from parties.models import Party
from parties.tests.factories import PartyFactory
from parties.tests.fixtures import DefaultPartyFixtures
from people.forms.fields import CurrentUnlockedBallotsField
from people.forms.forms import PersonMembershipForm
from people.tests.factories import PersonFactory


class TestPartyFields(UK2015ExamplesMixin, DefaultPartyFixtures, TestCase):
    def setUp(self):
        Party.objects.all().delete()

        class DefaultPartyForm(forms.Form):
            party = PartyIdentifierField(required=False)

        self.default_form = DefaultPartyForm

    def test_field_html(self):
        form = self.default_form()
        self.assertHTMLEqual(
            form.as_p(),
            """
            <p>
                <label for="id_party_0">Party:</label>
                <select class="party_widget_select" disabled name="party_0"
                id="id_party_0">
                    <option value="" selected>
                    </option>
                </select>
                <input class="party_widget_input" type="text" name="party_1"
                id="id_party_1">
            </p>
            """,
        )

    def test_validate_party_ids(self):
        form = self.default_form(
            {"party_0": "not a party", "party_1": "not a party"}
        )
        form.full_clean()
        self.assertDictEqual(
            form.errors,
            {
                "party": [
                    "Select a valid choice. not a party is not one of the available choices.",
                    "'not a party' is not a current party identifier",
                ]
            },
        )
        self.assertFalse(form.is_valid())

    def test_party_selected(self):
        PartyFactory(ec_id="PP12", name="New party")
        PartyFactory(
            ec_id="PP13",
            name="New party without candidates",
            current_candidates=0,
        )
        field = PartyIdentifierField(required=False)
        self.assertEqual(
            field.fields[0].choices,
            [
                ("", {"label": ""}),
                ("PP12", {"label": "New party", "register": "GB"}),
            ],
        )

    def test_char_input_returned_if_values_in_both_fields(self):
        party1 = PartyFactory(ec_id="PP12", name="New party")
        party2 = PartyFactory(
            ec_id="PP13",
            name="New party without candidates",
            current_candidates=0,
        )

        field = PartyIdentifierField(required=False)
        # We should get the last value from right to left
        self.assertEqual(field.clean(["", "PP13"]), party2)
        self.assertEqual(field.clean(["PP12", "PP13"]), party2)
        self.assertEqual(field.clean(["PP12", ""]), party1)

    def test_validation_errors(self):
        PartyFactory(ec_id="PP12", name="New party")
        PartyFactory(
            ec_id="PP13",
            name="New party without candidates",
            current_candidates=0,
        )

        field = PartyIdentifierField(required=False)
        msg = (
            "'Select a valid choice. PP99 is not one of the available choices.'"
        )
        with self.assertRaisesMessage(ValidationError, msg):
            field.clean(["PP99", ""])

        msg = "'PP99' is not a current party identifier"
        with self.assertRaisesMessage(ValidationError, msg):
            field.clean(["", "PP99"])

    def test_select_with_initial_contains_party(self):
        """
        If a user has selected a party previously, it should be a selected
        option in the dropdown, even if it normally wouldn't be in there
        """
        PartyFactory(ec_id="PP12", name="New party")
        PartyFactory(
            ec_id="PP13",
            name="New party without candidates",
            current_candidates=0,
        )
        field = PartyIdentifierField(required=False)
        # Make sure PP13 isn't in the default list
        self.assertEqual(
            field.fields[0].choices,
            [
                ("", {"label": ""}),
                ("PP12", {"label": "New party", "register": "GB"}),
            ],
        )

        class PartyForm(PopulatePartiesMixin, forms.Form):
            ballot = CurrentUnlockedBallotsField()
            party = PartyIdentifierField(
                required=False, require_all_fields=False
            )

        form = PartyForm(initial={"party": ["", "PP13"]})
        self.assertEqual(
            form["party"].field.fields[0].choices,
            [
                ("", {"label": ""}),
                ("PP12", {"label": "New party", "register": "GB"}),
                (
                    "PP13",
                    {"label": "New party without candidates", "register": "GB"},
                ),
            ],
        )

    def test_update_model_form_populates_other_parties(self):
        """
        PersonMembershipForm uses PopulatePartiesMixin, so should add our new
        party to the default choices

        """
        new_party = PartyFactory(ec_id="PP12", name="New party")
        person = PersonFactory()
        membership = MembershipFactory(
            ballot=self.dulwich_post_ballot, person=person, party=new_party
        )
        form = PersonMembershipForm(instance=membership)
        self.assertEqual(
            form["party_identifier"].field.fields[0].choices[1],
            ("PP12", {"label": "New party", "register": "GB"}),
        )
