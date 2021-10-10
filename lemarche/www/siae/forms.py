from django import forms
from django.contrib.gis.db.models.functions import Distance
from django.db.models import BooleanField, Case, Exists, OuterRef, Value, When
from django.db.models.functions import NullIf

from lemarche.perimeters.models import Perimeter
from lemarche.sectors.models import Sector
from lemarche.siaes.models import Siae, SiaeOffer
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
    # The hidden `perimeter` field is populated by the autocomplete JavaScript mechanism,
    # see `perimeter_autocomplete_field.js`.
    perimeter = forms.CharField(widget=forms.HiddenInput())
    # Most of the field will be overriden by the autocomplete mechanism
    perimeter_name = forms.CharField(
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
        qs = Siae.objects.prefetch_related("sectors", "networks", "users")

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

    def perimeter_filter(self, qs, search_perimeter, add_department_to_city_search=True):
        """
        The search_perimeter should be a Perimeter slug.
        Depending on the type of Perimeter that was chosen, different cases arise:

        **CITY**
        return the Siae with geo_range=GEO_RANGE_CUSTOM and a perimeter radius that overlaps with the search_perimeter
        OR the Siae with geo_range=GEO_RANGE_DEPARTMENT and a department equal to the search_perimeter's

        **DEPARTMENT**
        return only the Siae in this department

        **REGION**
        return only the Siae in this region
        """
        try:
            perimeter = Perimeter.objects.get(slug=search_perimeter)
        except Perimeter.DoesNotExist:
            perimeter = None
            return qs

        if perimeter.kind == Perimeter.KIND_CITY:
            if not add_department_to_city_search:
                qs = qs.in_range_of_point(city_coords=perimeter.coords)
            else:
                qs = qs.in_range_of_point_or_in_department(
                    city_coords=perimeter.coords, department_code=perimeter.department_code
                )
        elif perimeter.kind == Perimeter.KIND_DEPARTMENT:
            qs = qs.in_department(department_code=perimeter.insee_code)
        elif perimeter.kind == Perimeter.KIND_REGION:
            qs = qs.in_region(region_name=perimeter.name)
        else:
            # unknown perimeter kind, don't filter
            pass
        return qs

    def order_queryset(self, qs):
        """
        The Siae are ordered by name.

        **BUT**
        - if a Siae has a a SiaeOffer, or a description, or a User, then it is "boosted"
        - if the search is on a CITY perimeter, we order by coordinates first
        """
        ORDER_BY_FIELDS = ["-has_offer", "-has_description", "-has_user", "name"]
        # annotate on distance to siae if CITY searched
        # TODO: avoid duplicate Perimeter query...
        search_perimeter = self.cleaned_data.get("perimeter", None)
        if search_perimeter:
            perimeter = Perimeter.objects.get(slug=search_perimeter)
            if perimeter and perimeter.kind == Perimeter.KIND_CITY:
                qs = qs.annotate(distance=Distance("coords", perimeter.coords))
                ORDER_BY_FIELDS = ["distance"] + ORDER_BY_FIELDS
        # annotate on SiaeOffer FK exists
        qs = qs.annotate(has_offer=Exists(SiaeOffer.objects.filter(siae_id=OuterRef("pk"))))
        # annotate on description presence: https://stackoverflow.com/a/65014409/4293684
        # qs = qs.annotate(has_description=Exists(F("description")))  # doesn't work
        qs = qs.annotate(
            has_description=Case(
                When(description__gte=1, then=Value(True)), default=Value(False), output_field=BooleanField()
            )
        )
        # annotation on User M2M exists: https://stackoverflow.com/a/58641475/4293684
        qs = qs.annotate(has_user=Exists(Siae.users.through.objects.filter(siae_id=OuterRef("pk"))))
        # final ordering
        qs = qs.order_by(*ORDER_BY_FIELDS)
        return qs
