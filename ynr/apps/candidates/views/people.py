import re

from braces.views import LoginRequiredMixin
from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import (
    Http404,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import urlquote
from django.views.decorators.cache import cache_control
from django.views.generic import FormView, TemplateView, View

from auth_helpers.views import GroupRequiredMixin, user_in_group
from candidates.forms import SingleElectionForm
from elections.mixins import ElectionMixin
from elections.models import Election
from people.forms import (
    NewPersonForm,
    PersonIdentifierFormsetFactory,
    UpdatePersonForm,
)
from people.models import Person
from popolo.models import NotStandingValidationError
from ynr.apps.people.merging import PersonMerger, InvalidMergeError

from ..diffs import get_version_diffs
from ..models import (
    TRUSTED_TO_MERGE_GROUP_NAME,
    LoggedAction,
    PersonRedirect,
    Ballot,
)
from ..models.auth import check_creation_allowed, check_update_allowed
from ..models.versions import revert_person_from_version_data
from .helpers import (
    ProcessInlineFormsMixin,
    get_field_groupings,
    get_person_form_fields,
)
from .version_data import get_change_metadata, get_client_ip


def get_call_to_action_flash_message(person, new_person=False):
    """Get HTML for a flash message after a person has been created or updated"""
    return render_to_string(
        "candidates/_person_update_call_to_action.html",
        {
            "new_person": new_person,
            "person_url": reverse(
                "person-view", kwargs={"person_id": person.id}
            ),
            "person_edit_url": reverse(
                "person-update", kwargs={"person_id": person.id}
            ),
            "person_name": person.name,
            "needing_attention_url": reverse("attention_needed"),
            # We want to offer the option to add another candidate in
            # any of the elections that this candidate is standing in,
            # which means we'll need the "create person" URL and
            # election name for each of those elections:
            "create_for_election_options": [
                (
                    reverse(
                        "person-create", kwargs={"election": election_data.slug}
                    ),
                    election_data.name,
                )
                for election_data in Election.objects.filter(
                    ballot__membership__person=person, current=True
                ).distinct()
            ],
        },
    )


class PersonView(TemplateView):
    template_name = "candidates/person-view.html"

    @method_decorator(cache_control(max_age=(60 * 20)))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = self.person.get_absolute_url()
        context["redirect_after_login"] = urlquote(path)
        context["canonical_url"] = self.person.wcivf_url()
        context["person"] = self.person

        context["elections_to_list"] = Election.objects.filter(
            ballot__membership__person=self.person
        ).order_by("-election_date")

        context["last_candidacy"] = self.person.last_candidacy
        context["election_to_show"] = None
        context["has_current_elections"] = (
            context["elections_to_list"].current_or_future().exists()
        )
        context["simple_fields"] = [
            field.name for field in settings.SIMPLE_POPOLO_FIELDS
        ]

        context["person_edits_allowed"] = self.person.user_can_edit(
            self.request.user
        )

        personal_fields, demographic_fields = get_field_groupings()
        context["has_demographics"] = any(
            demographic in context["simple_fields"]
            for demographic in demographic_fields
        )

        return context

    def get(self, request, *args, **kwargs):
        person_id = self.kwargs["person_id"]
        try:
            self.person = Person.objects.prefetch_related(
                "tmp_person_identifiers"
            ).get(pk=person_id)
        except Person.DoesNotExist:
            try:
                return self.get_person_redirect(person_id)
            except PersonRedirect.DoesNotExist:
                raise Http404(
                    "No person found with ID {person_id}".format(
                        person_id=person_id
                    )
                )
        return super().get(request, *args, **kwargs)

    def get_person_redirect(self, person_id):
        # If there's a PersonRedirect for this person ID, do the
        # redirect, otherwise process the GET request as usual.
        # try:
        new_person_id = PersonRedirect.objects.get(
            old_person_id=person_id
        ).new_person_id
        return HttpResponsePermanentRedirect(
            reverse("person-view", kwargs={"person_id": new_person_id})
        )


class RevertPersonView(LoginRequiredMixin, View):

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        version_id = self.request.POST["version_id"]
        person_id = self.kwargs["person_id"]
        source = self.request.POST["source"]

        with transaction.atomic():

            person = get_object_or_404(Person, id=person_id)

            versions = person.versions

            data_to_revert_to = None
            for version in versions:
                if version["version_id"] == version_id:
                    data_to_revert_to = version["data"]
                    break

            if not data_to_revert_to:
                message = "Couldn't find the version {0} of person {1}"
                raise Exception(message.format(version_id, person_id))

            change_metadata = get_change_metadata(self.request, source)

            # Update the person here...
            revert_person_from_version_data(person, data_to_revert_to)

            person.record_version(change_metadata)
            person.save()

            # Log that that action has taken place, and will be shown in
            # the recent changes, leaderboards, etc.
            LoggedAction.objects.create(
                user=self.request.user,
                person=person,
                action_type="person-revert",
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                source=change_metadata["information_source"],
            )

        return HttpResponseRedirect(
            reverse("person-view", kwargs={"person_id": person_id})
        )


class MergePeopleMixin:
    def do_merge(self, primary_person, secondary_person):
        merger = PersonMerger(
            primary_person, secondary_person, request=self.request
        )

        return merger.merge(delete=True)


class MergePeopleView(GroupRequiredMixin, TemplateView, MergePeopleMixin):

    http_method_names = ["get", "post"]
    required_group_name = TRUSTED_TO_MERGE_GROUP_NAME
    template_name = "candidates/generic-merge-error.html"

    def validate(self, context):
        if not re.search(r"^\d+$", context["other_person_id"]):
            message = "Malformed person ID '{0}'"
            raise InvalidMergeError(message.format(context["other_person_id"]))
        if context["person"].pk == int(context["other_person_id"]):
            message = "You can't merge a person ({0}) with themself ({1})"
            raise InvalidMergeError(
                message.format(context["person"].pk, context["other_person_id"])
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = get_object_or_404(
            Person, id=self.kwargs["person_id"]
        )
        context["other_person_id"] = self.request.POST.get("other", "")
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        # Check that the person IDs are well-formed:
        try:
            self.validate(context)
        except InvalidMergeError as e:
            context["error_message"] = e
            return self.render_to_response(context)

        with transaction.atomic():
            secondary_person = get_object_or_404(
                Person, id=context["other_person_id"]
            )

            try:
                merged_person = self.do_merge(
                    context["person"], secondary_person
                )
            except NotStandingValidationError:
                return HttpResponseRedirect(
                    reverse(
                        "person-merge-correct-not-standing",
                        kwargs={
                            "person_id": context["person"].pk,
                            "other_person_id": context["other_person_id"],
                        },
                    )
                )

        # And redirect to the primary person with the merged data:
        return HttpResponseRedirect(merged_person.get_absolute_url())


class CorrectNotStandingMergeView(
    GroupRequiredMixin, TemplateView, MergePeopleMixin
):
    template_name = "people/correct_not_standing_in_merge.html"
    required_group_name = TRUSTED_TO_MERGE_GROUP_NAME

    def extract_not_standing_edit(self, election, versions):
        versions_json = versions
        for version in versions_json:
            try:
                membership = version["data"]["standing_in"][election.slug]
                if membership is None:
                    return version
            except KeyError:
                continue
        return None

    def populate_not_standing_list(self, person, person_not_standing):
        for membership in person.memberships.all():
            if (
                membership.ballot.election
                in person_not_standing.not_standing.all()
            ):
                self.not_standing_elections.append(
                    {
                        "election": membership.ballot.election,
                        "person_standing": person,
                        "person_standing_ballot": membership.ballot,
                        "person_not_standing": person_not_standing,
                        "version": self.extract_not_standing_edit(
                            membership.ballot.election,
                            person_not_standing.versions,
                        ),
                    }
                )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person_a"] = get_object_or_404(
            Person, id=self.kwargs["person_id"]
        )
        context["person_b"] = get_object_or_404(
            Person, id=self.kwargs["other_person_id"]
        )

        self.not_standing_elections = []
        self.populate_not_standing_list(
            context["person_a"], context["person_b"]
        )
        self.populate_not_standing_list(
            context["person_b"], context["person_a"]
        )
        context["not_standing_elections"] = self.not_standing_elections
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()

        with transaction.atomic():
            for pair in context["not_standing_elections"]:
                pair["person_not_standing"].not_standing.remove(
                    pair["election"]
                )
        merged_person = self.do_merge(context["person_a"], context["person_b"])

        # And redirect to the primary person with the merged data:
        return HttpResponseRedirect(merged_person.get_absolute_url())


class UpdatePersonView(ProcessInlineFormsMixin, LoginRequiredMixin, FormView):
    template_name = "candidates/person-edit.html"
    form_class = UpdatePersonForm
    inline_formset_classes = {
        "identifiers_formset": PersonIdentifierFormsetFactory
    }

    def get_inline_formset_kwargs(self, formset_name):
        kwargs = {}

        if formset_name == "identifiers_formset":
            kwargs.update(
                {"instance": Person.objects.get(pk=self.kwargs["person_id"])}
            )
            model = self.inline_formset_classes["identifiers_formset"].model
            kwargs.update({"queryset": model.objects.editable_value_types()})

        return kwargs

    def get_initial(self):
        initial_data = super().get_initial()
        person = get_object_or_404(Person, pk=self.kwargs["person_id"])
        initial_data.update(person.get_initial_form_data())
        initial_data["person"] = person
        return initial_data

    def hide_locked_ballots(self, form):
        """
        This is, let's say, not ideal

        The problem is we don't let people change Ballots for people
        if that ballot is locked. Previously we disabled the HTML widget,
        but this means that browsers don't submit the form data. It's
        impossible to distinguish between a user trying to delete a ballot
        and a user not touching the form at all.

        The best thing in this case is to not show the thing that can't be
        changed, but we can't just remove the fields either, as that messes
        up other elements of the dynamic field creation.

        So, we end up just marking them all as hidden, at the point where we
        get the form.

        """
        election_slugs = []
        keys = ("standing", "constituency", "party_GB", "party_NI")
        for field in form.fields:
            if field.startswith("standing_"):
                election_slugs.append(field[9:])
        for slug in election_slugs:
            ballot_locked = Ballot.objects.filter(
                election__slug=slug,
                membership__person=form.initial["person"],
                candidates_locked=True,
            ).exists()

            if ballot_locked:
                for prefix in keys:
                    form.fields[
                        "{}_{}".format(prefix, slug)
                    ].widget = forms.HiddenInput()

        return form

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form = self.hide_locked_ballots(form)
        return form

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        person = get_object_or_404(Person, pk=self.kwargs["person_id"])
        context["person"] = person

        context["user_can_merge"] = user_in_group(
            self.request.user, TRUSTED_TO_MERGE_GROUP_NAME
        )

        context["person_edits_allowed"] = person.user_can_edit(
            self.request.user
        )

        context["versions"] = get_version_diffs(person.versions)

        context = get_person_form_fields(context, context["form"])

        return context

    def form_valid(self, all_forms):
        form = all_forms["form"]

        if not (settings.EDITS_ALLOWED or self.request.user.is_staff):
            return HttpResponseRedirect(reverse("all-edits-disallowed"))

        context = self.get_context_data()
        if not context["person_edits_allowed"]:
            raise PermissionDenied

        identifiers_formset = all_forms["identifiers_formset"]

        with transaction.atomic():

            person = context["person"]
            identifiers_formset.instance = person
            identifiers_formset.save()

            old_name = person.name
            old_candidacies = person.current_or_future_candidacies
            person.update_from_form(form)
            new_name = person.name
            new_candidacies = person.current_or_future_candidacies
            check_update_allowed(
                self.request.user,
                old_name,
                old_candidacies,
                new_name,
                new_candidacies,
            )
            if old_name != new_name:
                person.other_names.update_or_create(
                    name=old_name,
                    defaults={
                        "note": "Added when main name changed on person edit form"
                    },
                )

            change_metadata = get_change_metadata(
                self.request, form.cleaned_data.pop("source")
            )
            person.record_version(change_metadata)
            person.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=person,
                action_type="person-update",
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                source=change_metadata["information_source"],
            )

            # Add a message to be displayed after redirect:
            messages.add_message(
                self.request,
                messages.SUCCESS,
                get_call_to_action_flash_message(person, new_person=False),
                extra_tags="safe do-something-else",
            )

        return HttpResponseRedirect(
            reverse("person-view", kwargs={"person_id": person.id})
        )


class NewPersonSelectElectionView(LoginRequiredMixin, TemplateView):
    """
    For when we know new person's name, but not the election they are standing
    in.  This is normally because we've not come via a post page to add a new
    person (e.g., we've come from the search results page).
    """

    template_name = "candidates/person-create-select-election.html"

    def get_context_data(self, **kwargs):
        context = super(NewPersonSelectElectionView, self).get_context_data(
            **kwargs
        )
        context["name"] = self.request.GET.get("name")
        elections = []
        local_elections = []
        for election in Election.objects.current_or_future().order_by("slug"):
            election_type = election.slug.split(".")[0]
            if election_type == "local":
                election.type_name = "Local Elections"
                local_elections.append(election)
            else:
                election.type_name = election.name
                elections.append(election)
        elections += local_elections
        context["elections"] = elections

        return context


class NewPersonView(
    ProcessInlineFormsMixin, ElectionMixin, LoginRequiredMixin, FormView
):
    template_name = "candidates/person-create.html"
    form_class = NewPersonForm
    inline_formset_classes = {
        "identifiers_formset": PersonIdentifierFormsetFactory
    }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["election"] = self.election
        return kwargs

    def get_initial(self):
        result = super().get_initial()
        result["standing_" + self.election] = "standing"
        result["name"] = self.request.GET.get("name")
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["add_candidate_form"] = context["form"]

        context = get_person_form_fields(context, context["add_candidate_form"])
        return context

    def form_valid(self, all_forms):
        form = all_forms["form"]
        identifiers_formset = all_forms["identifiers_formset"]
        context = self.get_context_data()
        with transaction.atomic():

            person = Person.create_from_form(form)

            identifiers_formset.instance = person
            identifiers_formset.save()

            check_creation_allowed(
                self.request.user, person.current_or_future_candidacies
            )
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data["source"]
            )
            person.record_version(change_metadata)
            person.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=person,
                action_type="person-create",
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata["version_id"],
                source=change_metadata["information_source"],
            )

            # Add a message to be displayed after redirect:
            messages.add_message(
                self.request,
                messages.SUCCESS,
                get_call_to_action_flash_message(person, new_person=True),
                extra_tags="safe do-something-else",
            )

        return HttpResponseRedirect(
            reverse("person-view", kwargs={"person_id": person.id})
        )


class SingleElectionFormView(LoginRequiredMixin, FormView):
    template_name = "candidates/person-edit-add-single-election.html"
    form_class = SingleElectionForm

    def get_initial(self):
        initial_data = super().get_initial()
        election = get_object_or_404(
            Election.objects.all(), slug=self.kwargs["election"]
        )
        initial_data["election"] = election
        initial_data["user"] = self.request.user
        return initial_data
