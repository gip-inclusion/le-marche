from django import forms
from django.db.models import Value
from django.db.models.functions import NullIf

from lemarche.perimeters.models import Perimeter
from lemarche.sectors.models import Sector
from lemarche.siaes.models import Siae
from lemarche.utils.fields import GroupedModelChoiceField


EMPTY_CHOICE = (("", ""),)

SECTOR_FORM_QUERYSET = (
    Sector.objects.select_related("group")
    .exclude(group=None)
    .annotate(sector_is_autre=NullIf("name", Value("Autre")))
    .order_by("group__id", "sector_is_autre")
)


class SiaeSearchForm(forms.Form):
    FORM_KIND_CHOICES = EMPTY_CHOICE + Siae.KIND_CHOICES
    FORM_PRESTA_CHOICES = EMPTY_CHOICE + Siae.PRESTA_CHOICES

    sectors = GroupedModelChoiceField(
        label="Secteur d’activité",
        queryset=SECTOR_FORM_QUERYSET,
        choices_groupby="group",
        to_field_name="slug",
        required=False,
        widget=forms.Select(attrs={"style": "width:100%"}),
    )
    perimeter = forms.CharField(
        label="Lieu d'intervention",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Autour de (Arras, Bobigny, Strasbourg…)", "style": "width:100%"}
        ),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control"})

    def filter_queryset(self):
        qs = Siae.objects.prefetch_related("sectors", "networks")

        # we only display live Siae
        qs = qs.is_live()

        if not hasattr(self, "cleaned_data"):
            self.full_clean()

        sector = self.cleaned_data.get("sectors", None)
        if sector:
            qs = qs.filter(sectors__in=[sector])

        perimeter = self.cleaned_data.get("perimeter", None)
        if perimeter:
            qs = self.perimeter_filter(qs, perimeter)

        kind = self.cleaned_data.get("kind", None)
        if kind:
            qs = qs.filter(kind=kind)

        presta_type = self.cleaned_data.get("presta_type", None)
        if presta_type:
            qs = qs.filter(presta_type=presta_type)

        return qs

    def perimeter_filter(self, qs, search_perimeter):
        """
        The search_perimeter should be a Perimeter slug.
        Depending on the type of Perimeter that was chosen, different cases arise:
        - CITY: return only the Siae with a perimeter radius that overlaps with the city
        - DEPARTMENT: return only the Siae in this department
        - REGION: return only the Siae in this region
        """
        perimeter = Perimeter.objects.get(slug=search_perimeter)
        if perimeter.kind == Perimeter.KIND_CITY:
            qs = qs.within(perimeter.coords, 50)
        elif perimeter.kind == Perimeter.KIND_DEPARTMENT:
            qs = qs.in_department(code=perimeter.insee_code)
        elif perimeter.kind == Perimeter.KIND_REGION:
            qs = qs.in_region(name=perimeter.name)
        else:
            # unknown perimeter kind, don't filter
            pass
        return qs

    def order_queryset(self, qs):
        # perimeter = self.cleaned_data.get("perimeter", None)
        # if perimeter:
        qs = qs.order_by("name")
        return qs
