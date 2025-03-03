from django import forms
from django.forms.models import inlineformset_factory
from django_select2.forms import ModelSelect2MultipleWidget
from dsfr.forms import DsfrBaseForm

from lemarche.networks.models import Network
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.models import Sector, SectorGroup
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import (
    Siae,
    SiaeActivity,
    SiaeClientReference,
    SiaeGroup,
    SiaeImage,
    SiaeLabelOld,
    SiaeOffer,
    SiaeUserRequest,
)
from lemarche.utils.fields import GroupedModelMultipleChoiceField
from lemarche.www.siaes.widgets import CustomLocationWidget


class SiaeSearchBySiretForm(forms.Form):
    siret = forms.CharField(
        label="Entrez le numéro SIRET ou SIREN de votre structure",
        required=True,
    )

    def clean_siret(self):
        siret = self.cleaned_data["siret"]
        if siret:
            # strip spaces (beginning, inbetween, end)
            siret = siret.replace(" ", "")
            # siret/siren validation
            if len(siret) < 9:
                msg = "Le longueur du numéro doit être supérieure ou égale à 9 caractères."
                raise forms.ValidationError(msg)
            if len(siret) > 14:
                msg = "Le longueur du numéro ne peut pas dépasser 14 caractères."
                raise forms.ValidationError(msg)
            if not siret.isdigit():
                msg = "Le numéro ne doit être composé que de chiffres."
                raise forms.ValidationError(msg)
        return siret

    def filter_queryset(self):
        qs = Siae.objects.prefetch_related("users")

        if not hasattr(self, "cleaned_data"):
            self.full_clean()

        siret = self.cleaned_data.get("siret", None)
        if siret:
            qs = qs.filter_siret_startswith(siret)
        else:
            # show results only if there is a valid siret provided
            qs = qs.none()

        return qs


class SiaeSearchAdoptConfirmForm(forms.ModelForm):
    class Meta:
        model = Siae
        fields = []


class SiaeEditInfoForm(forms.ModelForm, DsfrBaseForm):
    class Meta:
        model = Siae
        fields = [
            "brand",
            "description",
            "logo_url",
            "ca",
            "year_constitution",
            "employees_insertion_count",
            "employees_permanent_count",
            # "labels",  # SiaeLabelOldFormSet
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["brand"].widget.attrs.update({"placeholder": self.instance.name})
        self.fields["description"].label = "Présentation commerciale de votre structure"
        self.fields["description"].widget.attrs.update(
            {
                "placeholder": "Décrivez votre activité commerciale puis votre projet social",
            }
        )
        self.fields["ca"].label = "Indiquez le chiffre d'affaires de votre structure"
        self.fields["year_constitution"].label = "Année de création de votre structure"
        self.fields["employees_insertion_count"].label = f"Nombre de {self.instance.etp_count_label_display.lower()}"
        # self.fields["logo_url"].label = "Importez votre logo"


class SiaeLabelOldForm(forms.ModelForm):
    class Meta:
        model = SiaeLabelOld
        fields = ["name"]


SiaeLabelOldFormSet = inlineformset_factory(Siae, SiaeLabelOld, form=SiaeLabelOldForm, extra=1, can_delete=True)


class SiaeEditOfferForm(forms.ModelForm):
    class Meta:
        model = Siae
        fields = [
            # "offers",  # SiaeOfferForm
            # "client_references",  # SiaeClientReferenceForm
            # "images",  # SiaeImageFormSet
        ]


class SiaeOfferForm(forms.ModelForm):
    class Meta:
        model = SiaeOffer
        fields = ["name", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].widget.attrs.update({"rows": 5})


SiaeOfferFormSet = inlineformset_factory(Siae, SiaeOffer, form=SiaeOfferForm, extra=1, can_delete=True)


class SiaeClientReferenceForm(forms.ModelForm):
    class Meta:
        model = SiaeClientReference
        fields = ["name", "logo_url"]  # TODO: make name mandatory


SiaeClientReferenceFormSet = inlineformset_factory(
    Siae, SiaeClientReference, form=SiaeClientReferenceForm, extra=1, can_delete=True
)


class SiaeImageForm(forms.ModelForm):
    class Meta:
        model = SiaeImage
        fields = ["name", "image_url"]  # TODO: make name mandatory ?


SiaeImageFormSet = inlineformset_factory(Siae, SiaeImage, form=SiaeImageForm, extra=1, can_delete=True)


class SiaeEditLinksForm(forms.ModelForm):
    networks = forms.ModelMultipleChoiceField(
        queryset=Network.objects.all().order_by("name"),
        required=False,
        widget=ModelSelect2MultipleWidget(
            model=Network,
            search_fields=["name__icontains"],
            attrs={"data-placeholder": "Choisissez le réseau", "data-minimum-input-length": 0},
        ),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=SiaeGroup.objects.all().order_by("name"),
        required=False,
        widget=ModelSelect2MultipleWidget(
            model=SiaeGroup,
            search_fields=["name__icontains"],
            attrs={"data-placeholder": "Choisissez le groupement", "data-minimum-input-length": 0},
        ),
    )

    class Meta:
        model = Siae
        fields = [
            "networks",
            "groups",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["networks"].label = "Votre structure est-elle adhérente à un réseau ou une fédération ?"
        self.fields["groups"].label = "Appartenez-vous à un groupement ou ensemblier ?"


class SiaeEditContactForm(forms.ModelForm):
    class Meta:
        model = Siae
        fields = [
            "contact_first_name",
            "contact_last_name",
            "contact_website",
            "contact_email",
            "contact_phone",
            "contact_social_website",
        ]


class SiaeUserRequestForm(forms.ModelForm):
    class Meta:
        model = SiaeUserRequest
        fields = []


class SiaeActivitiesCreateForm(forms.ModelForm):
    sector_group = forms.ModelChoiceField(
        label="Secteurs d'activités",
        queryset=SectorGroup.objects.all(),
        required=True,
    )
    sectors = GroupedModelMultipleChoiceField(
        label="Activités",
        queryset=Sector.objects.form_filter_queryset(),
        choices_groupby="group",
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )
    presta_type = forms.MultipleChoiceField(
        label=SiaeActivity._meta.get_field("presta_type").verbose_name,
        choices=siae_constants.PRESTA_CHOICES,
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )
    geo_range = forms.ChoiceField(
        label=SiaeActivity._meta.get_field("geo_range").verbose_name,
        choices=siae_constants.ACTIVITIES_GEO_RANGE_CHOICES,
        initial=siae_constants.GEO_RANGE_COUNTRY,
        required=True,
        widget=forms.RadioSelect,
    )
    geo_range_custom_distance = forms.IntegerField(
        label="",
        required=False,
        help_text="Distance mesurée depuis le point central de la ville où se situe votre structure.",
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
        help_text="Vous pouvez ajouter autant de régions, de départements ou de villes que vous le souhaitez.",
        # FIXME: help_text not displayed
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # these fields are autocompletes
        self.fields["locations"].choices = []

    def clean(self):
        cleaned_data = super().clean()
        geo_range = cleaned_data.get("geo_range")
        geo_range_custom_distance = cleaned_data.get("geo_range_custom_distance")

        if geo_range == siae_constants.GEO_RANGE_CUSTOM and not geo_range_custom_distance:
            self.add_error("geo_range_custom_distance", "Une distance en kilomètres est requise pour cette option.")

        if geo_range == siae_constants.GEO_RANGE_ZONES:
            if not cleaned_data.get("locations"):
                self.add_error(None, "Vous devez choisir au moins une zone d'intervention personnalisée.")
        else:
            cleaned_data["locations"] = []
        return cleaned_data

    class Meta:
        model = SiaeActivity
        fields = [
            "sector",
            "presta_type",
            "geo_range",
            "geo_range_custom_distance",
            "locations",
        ]
