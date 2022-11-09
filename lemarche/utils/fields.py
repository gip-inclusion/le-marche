import json
from functools import partial
from itertools import groupby
from operator import attrgetter

from django import forms
from django.contrib.postgres.fields import ArrayField
from django.forms.models import ModelChoiceField, ModelChoiceIterator, ModelMultipleChoiceField
from django.utils.html import escape
from django.utils.safestring import mark_safe


# taken from https://github.com/MTES-MCT/aides-territoires/blob/master/src/core/fields.py
class ChoiceArrayField(ArrayField):
    """
    Custom ArrayField with a ChoiceField as default field.
    The default field is a comma-separated InputText, which is not very useful.
    """

    def formfield(self, **kwargs):
        defaults = {
            "form_class": forms.MultipleChoiceField,
            "choices": self.base_field.choices,
        }
        defaults.update(kwargs)
        return super(ArrayField, self).formfield(**defaults)


# taken from https://simpleisbetterthancomplex.com/tutorial/2019/01/02/how-to-implement-grouped-model-choice-field.html
class GroupedModelChoiceIterator(ModelChoiceIterator):
    def __init__(self, field, groupby):
        self.groupby = groupby
        super().__init__(field)

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", "")  # ("", self.field.empty_label)
        queryset = self.queryset
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for group, objs in groupby(queryset, self.groupby):
            yield (group, [self.choice(obj) for obj in objs])


class GroupedModelChoiceField(ModelChoiceField):
    def __init__(self, *args, choices_groupby, **kwargs):
        if isinstance(choices_groupby, str):
            choices_groupby = attrgetter(choices_groupby)
        elif not callable(choices_groupby):
            raise TypeError("choices_groupby must either be a str or a callable accepting a single argument")
        self.iterator = partial(GroupedModelChoiceIterator, groupby=choices_groupby)
        super().__init__(*args, **kwargs)


class GroupedModelMultipleChoiceField(ModelMultipleChoiceField):
    def __init__(self, *args, choices_groupby, **kwargs):
        if isinstance(choices_groupby, str):
            choices_groupby = attrgetter(choices_groupby)
        elif not callable(choices_groupby):
            raise TypeError("choices_groupby must either be a str or a callable accepting a single argument")
        self.iterator = partial(GroupedModelChoiceIterator, groupby=choices_groupby)
        super().__init__(*args, **kwargs)


def pretty_print_readonly_jsonfield(jsonfield_data):
    """
    Display a pretty readonly version of a JSONField
    https://stackoverflow.com/a/60219265
    """
    result = ""

    if jsonfield_data:
        result = json.dumps(jsonfield_data, indent=4, ensure_ascii=False)
        result = mark_safe(f"<pre>{escape(result)}</pre>")

    return result


class BooleanNotEmptyField(forms.BooleanField):
    def to_python(self, value):
        if isinstance(value, str) and value.lower() in ("false", "0"):
            value = False
        elif isinstance(value, str) and value.lower() in ("true", "1"):
            value = True
        else:
            value = None
        return value

    def validate(self, value):
        if value not in (0, 1) and self.required:
            raise forms.ValidationError(self.error_messages["required"], code="required")
