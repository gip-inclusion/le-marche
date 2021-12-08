from django import forms
from django.forms.models import inlineformset_factory

from lemarche.favorites.models import FavoriteList
from lemarche.networks.models import Network
from lemarche.siaes.models import Siae, SiaeClientReference, SiaeImage, SiaeLabel, SiaeOffer
from lemarche.users.models import User
from lemarche.utils.fields import GroupedModelMultipleChoiceField
from lemarche.www.siaes.forms import SECTOR_FORM_QUERYSET


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


class ProfileFavoriteEditForm(forms.ModelForm):
    class Meta:
        model = FavoriteList
        fields = ["name"]

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # Mandatory fields.
    #     self.fields["name"].required = True


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
            qs = qs.filter(siret__startswith=siret)
        else:
            # show results only if there is a valid siret provided
            qs = qs.none()

        return qs


class SiaeSearchAdoptConfirmForm(forms.ModelForm):
    class Meta:
        model = Siae
        fields = []


class SiaeEditInfoContactForm(forms.ModelForm):
    # # to avoid select widget
    # kind = forms.CharField(label=Siae._meta.get_field("kind").verbose_name)
    # department = forms.CharField(label=Siae._meta.get_field("department").verbose_name)
    # region = forms.CharField(label=Siae._meta.get_field("region").verbose_name)

    class Meta:
        model = Siae
        fields = [
            "name",
            "brand",
            "siret",
            "kind",
            "website",
            "email",
            "phone",
            "address",
            "city",
            "post_code",
            "department",
            "region",
            "contact_first_name",
            "contact_last_name",
            "contact_website",
            "contact_email",
            "contact_phone",
            "logo_url",
            "api_entreprise_date_constitution",
            "api_entreprise_employees",
            "api_entreprise_employees_year_reference",
            "api_entreprise_etablissement_last_sync_date",
            "api_entreprise_ca",
            "api_entreprise_ca_date_fin_exercice",
            "api_entreprise_exercice_last_sync_date",
            "is_qpv",
            "api_qpv_last_sync_date",
            "qpv_name",
            "qpv_code",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disabled fields
        for field in Siae.READONLY_FIELDS:
            if field in self.fields:
                self.fields[field].disabled = True
                self.fields[field].required = False  # to avoid form errors on submit


class SiaeEditOfferForm(forms.ModelForm):
    presta_type = forms.MultipleChoiceField(
        label=Siae._meta.get_field("presta_type").verbose_name,
        choices=Siae.PRESTA_CHOICES,
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )
    geo_range = forms.ChoiceField(
        label=Siae._meta.get_field("geo_range").verbose_name,
        choices=Siae.GEO_RANGE_CHOICES,
        required=True,
        widget=forms.RadioSelect,
    )
    sectors = GroupedModelMultipleChoiceField(
        label=Siae._meta.get_field("sectors").verbose_name,
        queryset=SECTOR_FORM_QUERYSET,
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
        if self.cleaned_data["geo_range"] != Siae.GEO_RANGE_CUSTOM:
            self.instance.geo_range_custom_distance = None
        super().save(*args, **kwargs)


class SiaeEditPrestaForm(forms.ModelForm):
    class Meta:
        model = Siae
        fields = [
            "description",
            # "offers",  # inlineformset
            # "client_references",  # inlineformset
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].widget.attrs.update(
            {
                "placeholder": "N'hésitez pas à mettre en avant les spécificités de votre structure",
            }
        )


class SiaeOfferForm(forms.ModelForm):
    class Meta:
        model = SiaeOffer
        fields = ["name", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].widget.attrs.update({"rows": 5})


SiaeOfferFormSet = inlineformset_factory(Siae, SiaeOffer, form=SiaeOfferForm, extra=0, can_delete=True)


class SiaeClientReferenceForm(forms.ModelForm):
    class Meta:
        model = SiaeClientReference
        fields = ["name", "logo_url"]  # TODO: make name mandatory


SiaeClientReferenceFormSet = inlineformset_factory(
    Siae, SiaeClientReference, form=SiaeClientReferenceForm, extra=0, can_delete=True
)


class SiaeEditOtherForm(forms.ModelForm):
    is_cocontracting = forms.BooleanField(
        label="Êtes-vous ouvert à la co-traitance ?",
        required=False,
        widget=forms.RadioSelect(choices=[(True, "Oui"), (False, "Non")]),
    )
    networks = forms.ModelMultipleChoiceField(
        queryset=Network.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Siae
        fields = [
            "is_cocontracting",
            "networks",
            # "labels",  # inlineformset
        ]


class SiaeLabelForm(forms.ModelForm):
    class Meta:
        model = SiaeLabel
        fields = ["name"]


SiaeLabelFormSet = inlineformset_factory(Siae, SiaeLabel, form=SiaeLabelForm, extra=0, can_delete=True)


class SiaeImageForm(forms.ModelForm):
    class Meta:
        model = SiaeImage
        fields = ["name", "image_url"]  # TODO: make name mandatory ?


SiaeImageFormSet = inlineformset_factory(Siae, SiaeImage, form=SiaeImageForm, extra=0, can_delete=True)
