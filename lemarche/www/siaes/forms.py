from django import forms
from django.contrib.gis.db.models.functions import Distance
from django.db.models import BooleanField, Case, Value, When
from django.db.models.functions import NullIf

from lemarche.favorites.models import FavoriteList
from lemarche.networks.models import Network
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.models import Sector
from lemarche.siaes.models import Siae
from lemarche.utils.fields import GroupedModelMultipleChoiceField


EMPTY_CHOICE = (("", ""),)

SECTOR_FORM_QUERYSET = (
    Sector.objects.select_related("group")
    .exclude(group=None)  # sector must have a group !
    .annotate(sector_is_autre=NullIf("name", Value("Autre")))
    .order_by("group__id", "sector_is_autre")
)


class SiaeSearchForm(forms.Form):
    FORM_KIND_CHOICES_GROUPED = (
        ("Insertion par l'activité économique", Siae.KIND_CHOICES_WITH_EXTRA_INSERTION),
        ("Handicap", Siae.KIND_CHOICES_WITH_EXTRA_HANDICAP),
    )
    FORM_PRESTA_CHOICES = EMPTY_CHOICE + Siae.PRESTA_CHOICES

    sectors = GroupedModelMultipleChoiceField(
        label="Secteur d’activité",
        queryset=SECTOR_FORM_QUERYSET,
        choices_groupby="group",
        to_field_name="slug",
        required=False,
    )
    # The hidden `perimeter` field is populated by the autocomplete JavaScript mechanism,
    # see `perimeter_autocomplete_field.js`.
    perimeter = forms.CharField(required=False, widget=forms.HiddenInput())
    # Most of the field will be overridden by the autocomplete mechanism
    perimeter_name = forms.CharField(
        label="Lieu d'intervention",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Région, département, ville"}),
    )
    kind = forms.MultipleChoiceField(
        label="Type de structure",
        choices=FORM_KIND_CHOICES_GROUPED,
        required=False,
    )
    presta_type = forms.ChoiceField(
        label="Type de prestation",
        choices=FORM_PRESTA_CHOICES,
        required=False,
    )
    networks = forms.ModelChoiceField(
        label="Réseau",
        queryset=Network.objects.all().order_by("name"),
        to_field_name="slug",
        empty_label="",
        required=False,
    )

    favorite_list = forms.ModelChoiceField(
        queryset=FavoriteList.objects.all(), to_field_name="slug", required=False, widget=forms.HiddenInput()
    )

    def clean(self):
        """
        We override the clean method to manage 2 edge cases:
        - if perimeter is empty but perimeter_name is not (the user used the typeahead but didn't select a perimeter option): show an error  # noqa
        - if perimeter_name is empty but perimeter is not (the user had previously searched a valid perimeter option, but erased it): erase the perimeter data (TODO: manage this case in the frontend ?)  # noqa
        """
        cleaned_data = super().clean()
        perimeter = cleaned_data.get("perimeter", "")
        perimeter_name = cleaned_data.get("perimeter_name", "")
        if perimeter_name and not perimeter:
            raise forms.ValidationError(
                {"perimeter_name": "Périmètre inconnu. Veuillez en choisir un dans la liste, ou effacer le texte."}
            )
        if perimeter and not perimeter_name:
            self.cleaned_data["perimeter"] = ""
            return self.cleaned_data

    def filter_queryset(self, perimeter):
        """
        Method to filter the Siaes depending on the search filters.
        We also make sure there are no duplicates.
        """
        # we only display live Siae
        qs = Siae.objects.search_query_set()

        if not hasattr(self, "cleaned_data"):
            self.full_clean()

        sectors = self.cleaned_data.get("sectors", None)
        if sectors:
            qs = qs.filter_sectors(sectors)

        if perimeter:
            qs = self.perimeter_filter(qs, perimeter)

        kind = self.cleaned_data.get("kind", None)
        if kind:
            qs = qs.filter(kind__in=kind)

        presta_type = self.cleaned_data.get("presta_type", None)
        if presta_type:
            qs = qs.filter(presta_type__overlap=[presta_type])

        network = self.cleaned_data.get("networks", None)
        if network:
            qs = qs.filter(networks__in=[network])

        favorite_list = self.cleaned_data.get("favorite_list", None)
        if favorite_list:
            qs = qs.filter(favorite_lists__in=[favorite_list])

        # avoid duplicates
        qs = qs.distinct()

        return qs

    def get_perimeter(self):
        try:
            search_perimeter = self.data.get("perimeter", None)
            perimeter = Perimeter.objects.get(slug=search_perimeter)
        except Perimeter.DoesNotExist:
            perimeter = None
        return perimeter

    def perimeter_filter(self, qs, perimeter):
        """
        Method to filter the Siaes depending on the perimeter filter.
        The search_perimeter should be a Perimeter slug.
        Depending on the type of Perimeter that was chosen, different cases arise:

        **CITY**
        return the Siae with the post code in Perimeter.post_codes+department
        OR the Siae with geo_range=GEO_RANGE_CUSTOM and a perimeter radius that overlaps with the search_perimeter
        OR the Siae with geo_range=GEO_RANGE_DEPARTMENT and a department equal to the search_perimeter's

        **DEPARTMENT**
        return only the Siae in this department

        **REGION**
        return only the Siae in this region
        """
        if not perimeter:
            return qs
        if perimeter.kind == Perimeter.KIND_CITY:
            # qs = qs.in_range_of_point(city_coords=perimeter.coords)
            qs = qs.in_city_area(perimeter=perimeter)
        elif perimeter.kind == Perimeter.KIND_DEPARTMENT:
            qs = qs.in_department(department_code=perimeter.insee_code)
        elif perimeter.kind == Perimeter.KIND_REGION:
            qs = qs.in_region(region_name=perimeter.name)
        else:
            # unknown perimeter kind, don't filter
            pass
        return qs

    def order_queryset(self, qs, perimeter):
        """
        Method to order the search results (can depend on the search filters).

        By default, the Siaes are ordered by name.

        **BUT**
        - if a Siae has a a SiaeOffer, or a description, or a User, then it is "boosted"
        - if the search is on a CITY perimeter, we order by coordinates first
        """
        ORDER_BY_FIELDS = ["-has_offer", "-has_description", "-has_user", "name"]
        # annotate on description presence: https://stackoverflow.com/a/65014409/4293684
        # qs = qs.annotate(has_description=Exists(F("description")))  # doesn't work
        qs = qs.annotate(
            has_description=Case(
                When(description__gte=1, then=Value(True)), default=Value(False), output_field=BooleanField()
            )
        )
        qs = qs.annotate(
            has_offer=Case(
                When(offer_count__gte=1, then=Value(True)), default=Value(False), output_field=BooleanField()
            )
        )
        qs = qs.annotate(
            has_user=Case(When(user_count__gte=1, then=Value(True)), default=Value(False), output_field=BooleanField())
        )

        # annotate on distance to siae if CITY searched
        if perimeter:
            if perimeter and perimeter.kind == Perimeter.KIND_CITY:
                qs = qs.annotate(
                    distance=Case(
                        # if it's in the same city we set the distance at 0
                        When(post_code__in=perimeter.post_codes, then=Distance("coords", "coords")),
                        default=Distance("coords", perimeter.coords),
                    )
                )
                ORDER_BY_FIELDS = ["distance"] + ORDER_BY_FIELDS

        # final ordering
        qs = qs.order_by(*ORDER_BY_FIELDS)
        return qs


class SiaeFavoriteForm(forms.ModelForm):
    favorite_lists = forms.ModelChoiceField(
        label="Liste à associer",
        queryset=FavoriteList.objects.all(),
        widget=forms.RadioSelect,
        required=False,
    )

    class Meta:
        model = Siae
        fields = ["favorite_lists"]
