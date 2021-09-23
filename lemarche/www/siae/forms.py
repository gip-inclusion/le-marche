from django import forms

from lemarche.sectors.models import Sector
from lemarche.siaes.models import Siae
from lemarche.utils.fields import GroupedModelChoiceField


EMPTY_CHOICE = (("", ""),)


class SiaeSearchForm(forms.Form):
    FORM_KIND_CHOICES = EMPTY_CHOICE + Siae.KIND_CHOICES
    FORM_PRESTA_CHOICES = EMPTY_CHOICE + Siae.PRESTA_CHOICES

    sectors = GroupedModelChoiceField(
        label="Secteur d’activité",
        queryset=Sector.objects.select_related("group").exclude(group=None),
        choices_groupby="group",
        to_field_name="slug",
        required=False,
        widget=forms.Select(attrs={"style": "width:100%"}),
    )
    kind = forms.ChoiceField(
        label="Type de structure",
        choices=FORM_KIND_CHOICES,
        required=False,
        widget=forms.Select(attrs={"style": "width:100%"}),
    )
    presta_type = forms.ChoiceField(
        label="Type de prestation",
        choices=FORM_PRESTA_CHOICES,
        required=False,
        widget=forms.Select(attrs={"style": "width:100%"}),
    )

    def filter_queryset(self):
        qs = Siae.objects.prefetch_related("sectors", "networks")

        if not hasattr(self, "cleaned_data"):
            self.full_clean()

        sector = self.cleaned_data.get("sectors", None)
        if sector:
            qs = qs.filter(sectors__in=[sector])

        kind = self.cleaned_data.get("kind", None)
        if kind:
            qs = qs.filter(kind=kind)

        presta_type = self.cleaned_data.get("presta_type", None)
        if presta_type:
            qs = qs.filter(presta_type=presta_type)

        return qs
