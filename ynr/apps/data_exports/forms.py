from data_exports.csv_fields import csv_fields
from django import forms


def extra_field_choices():
    choices = []
    for name, field in csv_fields.items():
        if not field.core:
            choices.append((name, name))
    return choices


def grouped_choices():
    groups = {}
    for name, field in csv_fields.items():
        if field.core:
            continue
        group_fields = groups.get(field.value_group, [])
        group_fields.append((name, field))
        groups[field.value_group] = group_fields
    return groups


class AdditionalFieldsForm(forms.Form):
    extra_fields = forms.MultipleChoiceField(
        choices=extra_field_choices,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )
