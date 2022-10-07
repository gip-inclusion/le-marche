from django import forms
from django.contrib.gis.db.models.functions import Distance
from django.db.models import BooleanField, Case, Q, Value, When

from lemarche.favorites.models import FavoriteList
from lemarche.networks.models import Network
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.models import Sector
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender
from lemarche.utils.fields import GroupedModelMultipleChoiceField


class SiaeSearchForm(forms.Form):
    FORM_KIND_CHOICES_GROUPED = (
        ("Insertion par l'activité économique", Siae.KIND_CHOICES_WITH_EXTRA_INSERTION),
        ("Handicap", Siae.KIND_CHOICES_WITH_EXTRA_HANDICAP),
    )
    FORM_TERRITORY_CHOICES = (
        ("QPV", "Quartier prioritaire de la politique de la ville (QPV)"),
        ("ZRR", "Zone de revitalisation rurale (ZRR)"),
    )

    q = forms.CharField(
        label="Recherche via le numéro de SIRET ou le nom de votre structure",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Votre recherche…"}),
    )
    sectors = GroupedModelMultipleChoiceField(
        label=Sector._meta.verbose_name_plural,
        queryset=Sector.objects.form_filter_queryset(),
        choices_groupby="group",
        to_field_name="slug",
        required=False,
    )
    # The hidden `perimeters` field is populated by the JS autocomplete library, see `perimeters_autocomplete_field.js`
    perimeters = forms.ModelMultipleChoiceField(
        label=Perimeter._meta.verbose_name_plural,
        queryset=Perimeter.objects.all(),
        to_field_name="slug",
        required=False,
        # widget=forms.HiddenInput()
    )
    kind = forms.MultipleChoiceField(
        label=Siae._meta.get_field("kind").verbose_name,
        choices=FORM_KIND_CHOICES_GROUPED,
        required=False,
    )
    presta_type = forms.MultipleChoiceField(
        label=Siae._meta.get_field("presta_type").verbose_name,
        choices=siae_constants.PRESTA_CHOICES,
        required=False,
    )
    territory = forms.MultipleChoiceField(
        label="Territoire spécifique",
        choices=FORM_TERRITORY_CHOICES,
        required=False,
    )
    networks = forms.ModelMultipleChoiceField(
        label="Réseau",
        queryset=Network.objects.all().order_by("name"),
        to_field_name="slug",
        required=False,
    )

    tender = forms.ModelChoiceField(
        queryset=Tender.objects.all(), to_field_name="slug", required=False, widget=forms.HiddenInput()
    )
    favorite_list = forms.ModelChoiceField(
        queryset=FavoriteList.objects.all(), to_field_name="slug", required=False, widget=forms.HiddenInput()
    )

    def filter_queryset(self):  # noqa C901
        """
        Method to filter the Siaes depending on the search filters.
        We also make sure there are no duplicates.
        """
        # we only display live Siae
        qs = Siae.objects.search_query_set()

        if not hasattr(self, "cleaned_data"):
            self.full_clean()

        full_text_string = self.cleaned_data.get("q", None)
        if full_text_string:
            # case where a siret search was done, strip all spaces
            if full_text_string.replace(" ", "").isdigit():
                full_text_string = full_text_string.replace(" ", "")
            qs = qs.filter_full_text(full_text_string)

        sectors = self.cleaned_data.get("sectors", None)
        if sectors:
            qs = qs.filter_sectors(sectors)

        perimeters = self.cleaned_data.get("perimeters", None)
        if perimeters:
            qs = qs.in_perimeters_area(perimeters)

        kinds = self.cleaned_data.get("kind", None)
        if kinds:
            qs = qs.filter(kind__in=kinds)

        presta_types = self.cleaned_data.get("presta_type", None)
        if presta_types:
            qs = qs.filter(presta_type__overlap=presta_types)

        territory = self.cleaned_data.get("territory", None)
        if territory:
            if len(territory) == 1:
                if "QPV" in territory:
                    qs = qs.filter(is_qpv=True)
                elif "ZRR" in territory:
                    qs = qs.filter(is_zrr=True)
            elif len(territory) == 2:
                qs = qs.filter(Q(is_qpv=True) | Q(is_zrr=True))

        networks = self.cleaned_data.get("networks", None)
        if networks:
            qs = qs.filter_networks(networks)

        # un auteur d'un dépôt de besoin peut exporter la liste des structures intéressées
        tender = self.cleaned_data.get("tender", None)
        if tender:
            qs = qs.filter(tendersiae__tender=tender, tendersiae__contact_click_date__isnull=False)

        favorite_list = self.cleaned_data.get("favorite_list", None)
        if favorite_list:
            qs = qs.filter(favorite_lists__in=[favorite_list])

        # avoid duplicates
        qs = qs.distinct()

        return qs

    def order_queryset(self, qs):
        """
        Method to order the search results (can depend on the search filters).

        By default, Siae will be ordered by "-updated_at"
        **WHY**
        - push siae to update their profile, and have the freshest data at the top
        - we tried random order ("?"), but it had some bugs with pagination
        **BUT**
        - if a Siae has a a SiaeOffer, or a description, or a User, then it is "boosted"
        - if the search is on a CITY perimeter, we order by coordinates first
        - if the search is by keyword, order by "similarity" only
        """
        DEFAULT_ORDERING = ["-updated_at"]
        ORDER_BY_FIELDS = ["-has_offer", "-has_description", "-has_user"] + DEFAULT_ORDERING
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
        # TODO: QUID des distances
        perimeters = self.cleaned_data.get("perimeters", None)
        if perimeters and len(perimeters) == 1:
            perimeter = perimeters[0]
            if perimeter and perimeter.kind == Perimeter.KIND_CITY:
                qs = qs.annotate(
                    distance=Case(
                        # if it's in the same city we set the distance at 0
                        When(post_code__in=perimeter.post_codes, then=Distance("coords", "coords")),
                        default=Distance("coords", perimeter.coords),
                    )
                )
                ORDER_BY_FIELDS = ["distance"] + ORDER_BY_FIELDS

        full_text_string = self.cleaned_data.get("q", None)
        if full_text_string:
            ORDER_BY_FIELDS = ["-similarity"]

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
