from allauth.account.forms import LoginForm, SignupForm
from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from dsfr.forms import DsfrBaseForm

from lemarche.sectors.models import Sector
from lemarche.users import constants as user_constants
from lemarche.users.models import User
from lemarche.users.validators import professional_email_validator
from lemarche.utils.constants import EMPTY_CHOICE
from lemarche.utils.fields import GroupedModelMultipleChoiceField
from lemarche.utils.password_validation import CnilCompositionPasswordValidator
from lemarche.utils.widgets import CustomSelectMultiple


class CustomSignupForm(SignupForm, DsfrBaseForm):
    KIND_CHOICES_FORM = (
        (User.KIND_SIAE, "Fournisseur inclusif (SIAE, EA, EATT ou ESAT)"),
        (User.KIND_BUYER, "Acheteur public ou privé"),
        (User.KIND_PARTNER, "Un partenaire (réseaux, facilitateurs)"),
        (User.KIND_INDIVIDUAL, "Un particulier"),
    )
    FORM_BUYER_KIND_DETAIL_CHOICES = EMPTY_CHOICE + user_constants.BUYER_KIND_DETAIL_CHOICES
    FORM_PARTNER_KIND_CHOICES = EMPTY_CHOICE + user_constants.PARTNER_KIND_CHOICES

    kind = forms.ChoiceField(
        label="Indiquez votre profil", widget=forms.RadioSelect, choices=KIND_CHOICES_FORM, required=True
    )
    first_name = forms.CharField(label="Votre prénom", required=True)
    last_name = forms.CharField(label="Votre nom", required=True)
    phone = forms.CharField(
        label="Votre numéro de téléphone",
        max_length=35,
        required=False,
    )
    # buyer_kind_detail is hidden by default in the frontend. Shown if the user choses kind BUYER
    buyer_kind_detail = forms.ChoiceField(
        label="Type de votre organisation", choices=FORM_BUYER_KIND_DETAIL_CHOICES, required=False
    )
    # company_name is hidden by default in the frontend. Shown if the user choses kind BUYER or PARTNER
    company_name = forms.CharField(
        label="Le nom de votre structure",
        required=False,
    )
    # position is hidden by default in the frontend. Shown if the user choses kind BUYER
    position = forms.CharField(
        label="Votre poste",
        required=False,
    )
    # partner_kind is hidden by default in the frontend. Shown if the user choses kind PARTNER
    partner_kind = forms.ChoiceField(
        label=User._meta.get_field("partner_kind").verbose_name, choices=FORM_PARTNER_KIND_CHOICES, required=False
    )

    email = forms.EmailField(
        label="Votre adresse e-mail",
        widget=forms.TextInput(attrs={"placeholder": "Merci de bien vérifier l'adresse saisie."}),
        required=True,
    )

    sectors = GroupedModelMultipleChoiceField(
        label=User._meta.get_field("sectors").help_text,
        queryset=Sector.objects.form_filter_queryset(),
        choices_groupby="group",
        to_field_name="slug",
        required=False,
        widget=CustomSelectMultiple(),
    )

    accept_rgpd = forms.BooleanField(
        widget=forms.widgets.CheckboxInput(attrs={"class": "form-check-input"}), required=True
    )
    # accept_survey is hidden by default in the frontend. Shown if the user choses kind BUYER or PARTNER
    accept_survey = forms.BooleanField(
        label=User._meta.get_field("accept_survey").help_text, help_text="", required=False
    )

    # accept_share_contact_to_external_partners is hidden by default in the frontend. Shown if the user choses kind SIAE  # noqa
    accept_share_contact_to_external_partners = forms.BooleanField(
        label=User._meta.get_field("accept_share_contact_to_external_partners").help_text, help_text="", required=False
    )

    class Meta:
        model = User
        fields = [
            "kind",
            "first_name",
            "last_name",
            "phone",
            "buyer_kind_detail",
            "company_name",
            "position",
            "partner_kind",
            "email",
            "sectors",
            "password1",
            "password2",
            "accept_rgpd",
            "accept_survey",
            "accept_share_contact_to_external_partners",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.errors:
            for field in self.errors.keys():
                if field in self.fields:
                    self.fields[field].widget.attrs.update({"autofocus": ""})
                    break
        else:
            self.fields["kind"].widget.attrs.update({"autofocus": ""})

        # password validation rules
        self.fields["password1"].help_text = CnilCompositionPasswordValidator().get_help_text()

    def clean_email(self):
        """
        Allauth doest seem to handle basic integrity constraints. It's supposed to allow duplicate emails
        as the validated emails are checked later with integrity constraints.
        ACCOUNT_PREVENT_ENUMERATION = False had no effect in our case.
        """
        email = self.cleaned_data["email"]

        if User.objects.filter(email=email).exists():
            raise ValidationError("Cette adresse e-mail est déjà utilisée.")

        return email.lower()

    def clean(self):
        cleaned_data = super().clean()
        # email is not in cleaned data when detected as duplicated
        if self.cleaned_data["kind"] == User.KIND_BUYER and cleaned_data.get("email"):
            try:
                professional_email_validator(cleaned_data["email"])
            except ValidationError as e:
                self.add_error("email", e)
        # phone is required for BUYER and SIAE
        if self.cleaned_data["kind"] in [User.KIND_BUYER, User.KIND_SIAE]:
            if not self.cleaned_data.get("phone"):
                self.add_error("phone", "Ce champ est obligatoire.")
        return cleaned_data


class CustomLoginForm(LoginForm, DsfrBaseForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["login"].label = "Adresse e-mail"


class PasswordResetForm(PasswordResetForm, DsfrBaseForm):
    email = forms.EmailField(label="Votre adresse e-mail", required=True)
