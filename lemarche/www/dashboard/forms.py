from django import forms
from django.forms.models import inlineformset_factory
from django_select2.forms import ModelSelect2MultipleWidget

from lemarche.networks.models import Network
from lemarche.sectors.models import Sector
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import (
    Siae,
    SiaeClientReference,
    SiaeGroup,
    SiaeImage,
    SiaeLabel,
    SiaeOffer,
    SiaeUserRequest,
)
from lemarche.users.models import User
from lemarche.utils.fields import GroupedModelMultipleChoiceField


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mandatory fields.
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True

        # Disabled fields
        self.fields["email"].disabled = True


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


class SiaeEditSearchForm(forms.ModelForm):
    presta_type = forms.MultipleChoiceField(
        label=Siae._meta.get_field("presta_type").verbose_name,
        choices=siae_constants.PRESTA_CHOICES,
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )
    geo_range = forms.ChoiceField(
        label=Siae._meta.get_field("geo_range").verbose_name,
        choices=siae_constants.GEO_RANGE_CHOICES,
        required=True,
        widget=forms.RadioSelect,
    )
    sectors = GroupedModelMultipleChoiceField(
        label=Sector._meta.verbose_name_plural,
        queryset=Sector.objects.form_filter_queryset(),
        choices_groupby="group",
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Siae
        fields = [
            "presta_type",
            "geo_range",
            "geo_range_custom_distance",
            "sectors",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["geo_range_custom_distance"].widget.attrs.update({"placeholder": "Distance en kilomètres"})

    def save(self, *args, **kwargs):
        """Clean geo_range_custom_distance before save."""
        if self.cleaned_data["geo_range"] != siae_constants.GEO_RANGE_CUSTOM:
            self.instance.geo_range_custom_distance = None
        super().save(*args, **kwargs)


class SiaeEditInfoForm(forms.ModelForm):
    class Meta:
        model = Siae
        fields = [
            "description",
            "logo_url",
            "ca",
            "year_constitution",
            "employees_insertion_count",
            "employees_permanent_count",
            # "labels",  # SiaeLabelFormSet
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].label = "Présentation commerciale de votre structure"
        self.fields["description"].widget.attrs.update(
            {
                "placeholder": "Décrivez votre activité commerciale puis votre projet social",
            }
        )
        # self.fields["logo_url"].label = "Importez votre logo"


class SiaeLabelForm(forms.ModelForm):
    class Meta:
        model = SiaeLabel
        fields = ["name"]


SiaeLabelFormSet = inlineformset_factory(Siae, SiaeLabel, form=SiaeLabelForm, extra=1, can_delete=True)


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
    is_cocontracting = forms.BooleanField(
        label="Êtes-vous ouvert à la co-traitance ?",
        required=False,
        widget=forms.RadioSelect(choices=[(True, "Oui"), (False, "Non")]),
    )
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
            "is_cocontracting",
            "networks",
            "groups",
        ]


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
