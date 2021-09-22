from django import forms

from lemarche.sectors.models import Sector
from lemarche.utils.fields import GroupedModelChoiceField


class SiaeSearchForm(forms.Form):
    sectors = GroupedModelChoiceField(
        label="Secteur d’activité",
        queryset=Sector.objects.select_related("group").exclude(group=None),
        choices_groupby="group",
        to_field_name="slug",
        required=False,
        widget=forms.Select(attrs={"autofocus": "autofocus", "style": "width:100%"}),
    )
