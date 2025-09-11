from django import forms
from django.contrib.gis.db.models.functions import Distance
from django.core.exceptions import ValidationError
from django.db.models import BooleanField, Case, OuterRef, Q, Subquery, Value, When

from lemarche.favorites.models import FavoriteList
from lemarche.labels.models import Label
from lemarche.networks.models import Network
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.models import Sector
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae, SiaeActivity, SiaeClientReference, SiaeGroup
from lemarche.tenders.models import Tender
from lemarche.utils.fields import GroupedModelMultipleChoiceField
from lemarche.utils.widgets import CustomSelectMultiple
from lemarche.www.siaes.widgets import CustomLocationWidget


FORM_KIND_CHOICES_GROUPED = (
    ("Insertion par l'activité économique", siae_constants.KIND_INSERTION_CHOICES_WITH_EXTRA),
    ("Handicap", siae_constants.KIND_HANDICAP_CHOICES_WITH_EXTRA),
)
FORM_TERRITORY_CHOICES = (
    ("QPV", "Quartier prioritaire de la politique de la ville (QPV)"),
    ("ZRR", "Zone de revitalisation rurale (ZRR)"),
)

FORM_CA_CHOICES = (
    ("", ""),
    ("-100000", "Moins de 100 K€"),
    ("100000-500000", "100 K€ à 500 K€"),
    ("500000-1000000", "500 K€ à 1 M€"),
    ("1000000-5000000", "1 M€ à 5 M€"),
    ("5000000-10000000", "5 M€ à 10 M€"),
    ("10000000-", "Plus de 10 M€"),
)

FORM_EMPLOYEES_CHOICES = (
    ("", ""),
    ("1-9", "1 à 9 salariés"),
    ("10-49", "10 à 49 salariés"),
    ("50-99", "50 à 99 salariés"),
    ("100-249", "100 à 249 salariés"),
    ("250-499", "250 à 499 salariés"),
    ("500-", "Plus de 500 salariés"),
)

EMPLOYEES_API_ENTREPRISE_MAPPING = {
    "1-9": ["1 ou 2 salariés", "3 à 5 salariés", "6 à 9 salariés"],
    "10-49": ["10 à 19 salariés", "20 à 49 salariés"],
    "50-99": ["50 à 99 salariés"],
    "100-249": ["100 à 199 salariés", "200 à 249 salariés"],
    "250-499": ["250 à 499 salariés"],
    "500-": [
        "500 à 999 salariés",
        "1 000 à 1 999 salariés",
        "2 000 à 4 999 salariés",
        "5 000 à 9 999 salariés",
        "10 000 salariés et plus",
    ],
}


class SiaeFilterForm(forms.Form):
    ADVANCED_SEARCH_FIELDS = [
        "kind",
        "presta_type",
        "territory",
        "networks",
        "locations",
        "has_client_references",
        "has_groups",
        "ca",
        "legal_form",
        "employees",
        "labels",
    ]

    sectors = GroupedModelMultipleChoiceField(
        label=Sector._meta.verbose_name_plural,
        queryset=Sector.objects.form_filter_queryset(),
        choices_groupby="group",
        to_field_name="slug",
        required=False,
        widget=CustomSelectMultiple(),
    )
    perimeters = forms.ModelMultipleChoiceField(
        label=Perimeter._meta.verbose_name_plural,
        queryset=Perimeter.objects.all(),
        to_field_name="slug",
        required=False,
    )
    kind = forms.MultipleChoiceField(
        label=Siae._meta.get_field("kind").verbose_name,
        choices=FORM_KIND_CHOICES_GROUPED,
        required=False,
        widget=CustomSelectMultiple(),
    )
    presta_type = forms.MultipleChoiceField(
        label=SiaeActivity._meta.get_field("presta_type").verbose_name,
        choices=siae_constants.PRESTA_CHOICES,
        required=False,
        widget=CustomSelectMultiple(),
    )
    territory = forms.MultipleChoiceField(
        label="Territoire spécifique",
        choices=FORM_TERRITORY_CHOICES,
        required=False,
        widget=CustomSelectMultiple(),
    )
    networks = forms.ModelMultipleChoiceField(
        label="Réseau",
        queryset=Network.objects.all().order_by("name"),
        to_field_name="slug",
        required=False,
        widget=CustomSelectMultiple(),
    )

    locations = forms.ModelMultipleChoiceField(
        label="Localisation",
        queryset=Perimeter.objects.all(),
        to_field_name="slug",
        required=False,
        widget=CustomLocationWidget(  # displayed with a JS autocomplete library (see `perimeter_autocomplete_field.js`)  # noqa
            attrs={
                "placeholder": "Région, département, ville",
            }
        ),
    )

    has_client_references = forms.ChoiceField(
        label=SiaeClientReference._meta.verbose_name,
        help_text="Le prestataire inclusif a-t-il des références clients ?",
        choices=[("", ""), (True, "Oui"), (False, "Non")],
        required=False,
    )
    has_groups = forms.ChoiceField(
        label=SiaeGroup._meta.verbose_name,
        help_text="Le prestataire inclusif fait-il partie d'un groupement ?",
        choices=[("", ""), (True, "Oui"), (False, "Non")],
        required=False,
    )
    legal_form = forms.MultipleChoiceField(
        label=Siae._meta.get_field("legal_form").verbose_name,
        choices=siae_constants.LEGAL_FORM_CHOICES,
        required=False,
        widget=CustomSelectMultiple(),
    )

    ca = forms.ChoiceField(
        label=Siae._meta.get_field("ca").verbose_name,
        choices=FORM_CA_CHOICES,
        required=False,
    )

    employees = forms.ChoiceField(
        label="Effectifs",
        choices=FORM_EMPLOYEES_CHOICES,
        required=False,
    )

    labels = forms.ModelMultipleChoiceField(
        label="Certifications",
        queryset=Label.objects.all().order_by("name"),
        to_field_name="slug",
        required=False,
        widget=CustomSelectMultiple(),
    )

    company_client_reference = forms.CharField(
        label="Indiquez le nom de votre entreprise",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Votre entreprise…"}),
    )

    # name/brand/siret/siren search
    q = forms.CharField(
        label="Recherche via le numéro de SIRET, SIREN ou le nom de votre structure",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Votre recherche…"}),
    )

    # other hidden filters
    tender = forms.ModelChoiceField(
        queryset=Tender.objects.all(), to_field_name="slug", required=False, widget=forms.HiddenInput()
    )
    tendersiae_status = forms.CharField(required=False, widget=forms.HiddenInput())
    favorite_list = forms.ModelChoiceField(
        queryset=FavoriteList.objects.all(), to_field_name="slug", required=False, widget=forms.HiddenInput()
    )

    def __init__(self, advanced_search=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["has_groups"].help_text = None
        self.fields["has_client_references"].help_text = None
        # these fields are autocompletes
        self.fields["perimeters"].choices = []
        self.fields["locations"].choices = []
        # manage disabled fields
        if not advanced_search:
            for field in self.ADVANCED_SEARCH_FIELDS:
                self.fields[field].disabled = True
                self.fields[field].widget.attrs["disabled"] = True

    def filter_queryset(self, qs=None):  # noqa C901
        """
        Method to filter the Siaes depending on the search filters.
        We also make sure there are no duplicates.
        """
        if qs is None:
            # we only display live Siae
            qs = Siae.objects.search_query_set()

        if not hasattr(self, "cleaned_data"):
            self.full_clean()

        qs = qs.prefetch_related("activities__sector__group")
        kinds = self.cleaned_data.get("kind", None)
        if kinds:
            qs = qs.filter(kind__in=kinds)

        # Create a very nice subquery to filter SiaeActivity by presta_type, sector and perimeter
        siae_activity_subquery = SiaeActivity.objects.filter(siae=OuterRef("pk")).values("pk")

        if sectors := self.cleaned_data.get("sectors", None):
            siae_activity_subquery = siae_activity_subquery.filter_sectors(sectors)

        if perimeters := self.cleaned_data.get("perimeters", None):
            siae_activity_subquery = siae_activity_subquery.geo_range_in_perimeter_list(perimeters)

        if presta_types := self.cleaned_data.get("presta_type", None):
            siae_activity_subquery = siae_activity_subquery.filter(presta_type__overlap=presta_types)

        if sectors or perimeters or presta_types:
            qs = qs.filter(Q(activities__in=Subquery(siae_activity_subquery)))

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

        has_client_references = self.cleaned_data.get("has_client_references", None)
        if has_client_references in (True, "True"):
            qs = qs.filter(client_reference_count__gte=1)
        elif has_client_references in (False, "False"):
            qs = qs.filter(client_reference_count=0)

        has_groups = self.cleaned_data.get("has_groups", None)
        if has_groups in (True, "True"):
            qs = qs.filter(group_count__gte=1)
        elif has_groups in (False, "False"):
            qs = qs.filter(group_count=0)

        # for CA, "ca" field is taken first, otherwise "api_entreprise_ca" is taken
        ca = self.cleaned_data.get("ca", None)
        if ca:
            lower_limit, upper_limit = ca.split("-")
            if lower_limit:
                qs = qs.filter(
                    (Q(ca__gt=0) & Q(ca__gte=int(lower_limit)))
                    | ((Q(ca=None) | Q(ca=0)) & Q(api_entreprise_ca__gte=int(lower_limit)))
                )
            if upper_limit:
                qs = qs.filter(
                    (Q(ca__gt=0) & Q(ca__lt=int(upper_limit)))
                    | ((Q(ca=None) | Q(ca=0)) & Q(api_entreprise_ca__gt=0) & Q(api_entreprise_ca__lt=int(upper_limit)))
                )

        legal_forms = self.cleaned_data.get("legal_form", None)
        if legal_forms:
            qs = qs.filter(legal_form__in=legal_forms)

        employees = self.cleaned_data.get("employees", None)
        if employees:
            lower_limit, upper_limit = employees.split("-")

            # Check lower limitation, it always exists when employees filter is used
            qs = qs.with_employees_stats().filter(
                (Q(employees_count_annotated__isnull=False) & Q(employees_count_annotated__gte=int(lower_limit)))
                | (
                    Q(employees_count_annotated=None)
                    & Q(api_entreprise_employees__in=EMPLOYEES_API_ENTREPRISE_MAPPING[employees])
                )
            )

            # Upper limitation
            if upper_limit:
                qs = qs.filter(
                    (Q(employees_count_annotated__isnull=False) & Q(employees_count_annotated__lte=int(upper_limit)))
                    | (
                        Q(employees_count_annotated=None)
                        & Q(api_entreprise_employees__in=EMPLOYEES_API_ENTREPRISE_MAPPING[employees])
                    )
                )

        labels = self.cleaned_data.get("labels", None)
        if labels:
            qs = qs.filter_labels(labels)

        company_client_reference = self.cleaned_data.get("company_client_reference", None)
        if company_client_reference:
            qs = qs.prefetch_related("client_references").filter(
                client_references__name__icontains=company_client_reference
            )

        # name/brand/siret/siren search
        full_text_string = self.cleaned_data.get("q", None)
        if full_text_string:
            # case where a siret/siren search was done, strip all spaces
            if full_text_string.replace(" ", "").isdigit():
                full_text_string = full_text_string.replace(" ", "")
            qs = qs.filter_full_text(full_text_string)

        # a Tender author can export its Siae list
        tender = self.cleaned_data.get("tender", None)
        if tender:
            tendersiae_status = self.cleaned_data.get("tendersiae_status", "ALL")
            qs = qs.filter_with_tender_through_activities(tender=tender, tendersiae_status=tendersiae_status)

        locations = self.cleaned_data.get("locations", None)
        if locations:
            qs = qs.address_in_perimeter_list(locations)

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
        - if a Siae has a a SiaeOffer, or a description, or a logo, or a User, then it is "boosted"
        - if the search is on a CITY perimeter, we order by coordinates first
        - if the search is by keyword, order by "similarity" only
        """
        DEFAULT_ORDERING = ["-updated_at"]
        ORDER_BY_FIELDS = ["-has_offer", "-has_description", "-has_logo", "-has_user"] + DEFAULT_ORDERING
        # annotate on description presence: https://stackoverflow.com/a/65014409/4293684
        # qs = qs.annotate(has_description=Exists(F("description")))  # doesn't work
        qs = qs.annotate(
            has_offer=Case(
                When(offer_count__gte=1, then=Value(True)), default=Value(False), output_field=BooleanField()
            )
        )
        qs = qs.annotate(
            has_description=Case(
                When(description__gte=1, then=Value(True)), default=Value(False), output_field=BooleanField()
            )
        )
        qs = qs.annotate(
            has_logo=Case(When(logo_url__gte=1, then=Value(True)), default=Value(False), output_field=BooleanField())
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

        # if name/brand/siret/siren search, order by postgres similarity
        full_text_string = self.cleaned_data.get("q", None)
        if full_text_string:
            ORDER_BY_FIELDS = ["-similarity"]

        # final ordering
        qs = qs.order_by(*ORDER_BY_FIELDS)

        return qs

    def is_advanced_search(self) -> bool:
        if not hasattr(self, "cleaned_data"):
            self.full_clean()

        for field in self.ADVANCED_SEARCH_FIELDS:
            if self.cleaned_data.get(field):
                return True

        return False


class SiaeFavoriteForm(forms.ModelForm):
    favorite_list = forms.ModelChoiceField(
        label="Liste à associer",
        queryset=FavoriteList.objects.none(),
        widget=forms.RadioSelect,
        required=False,
    )

    class Meta:
        model = Siae
        fields = ["favorite_list"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["favorite_list"].queryset = FavoriteList.objects.filter(user=self.user)

    def clean_favorite_list(self):
        fav_list = self.cleaned_data["favorite_list"]
        # The siae is already in a favorite list of this user
        if FavoriteList.objects.filter(siaes=self.instance, user=self.user).exists():
            raise ValidationError("Cette structure est déjà liée à une liste de favoris.")
        return fav_list


class NetworkSiaeFilterForm(forms.Form):
    perimeter = forms.ModelChoiceField(
        label="Filtrer par région",
        queryset=Perimeter.objects.regions().order_by("name"),
        to_field_name="slug",
        required=False,
        widget=forms.Select(
            attrs={
                "class": "fr-select",
                "onchange": "this.form.submit()",
            }
        ),
    )

    def filter_queryset(self, qs=None):
        if qs is None:
            qs = Siae.objects.search_query_set()

        if not hasattr(self, "cleaned_data"):
            self.full_clean()

        perimeter = self.cleaned_data.get("perimeter", None)
        if perimeter:
            qs = qs.address_in_perimeter_list([perimeter])

        # avoid duplicates
        qs = qs.distinct()

        return qs


class SiaeSiretFilterForm(forms.Form):
    siret = forms.CharField(label="Indiquez votre SIRET", max_length=17, min_length=14, required=False)

    def clean_siret(self):
        """Clean spaces from siret"""
        siret = self.cleaned_data["siret"]
        siret = siret.replace(" ", "")
        return siret
