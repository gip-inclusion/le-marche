from django import forms
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm

from lemarche.users.models import User
from lemarche.utils.password_validation import CnilCompositionPasswordValidator


class SignupForm(UserCreationForm):
    KIND_CHOICES_FORM = (
        (User.KIND_SIAE, "Une entreprise sociale inclusive (SIAE ou structure du handicap, GEIQ)"),
        (User.KIND_BUYER, "Un acheteur"),
        (User.KIND_PARTNER, "Un partenaire (réseaux, facilitateurs)"),
    )

    kind = forms.ChoiceField(label="", widget=forms.RadioSelect, choices=KIND_CHOICES_FORM, required=True)
    first_name = forms.CharField(
        label="Votre prénom", widget=forms.TextInput(attrs={"class": "form-control"}), required=True
    )
    last_name = forms.CharField(
        label="Votre nom", widget=forms.TextInput(attrs={"class": "form-control"}), required=True
    )
    phone = forms.CharField(
        label="Votre numéro de téléphone",
        max_length=35,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False,
    )
    email = forms.EmailField(
        label="Votre adresse e-mail", widget=forms.TextInput(attrs={"class": "form-control"}), required=True
    )
    # help_text="Nous enverrons un e-mail de confirmation à cette adresse avant de valider le compte.")  # noqa

    class Meta:
        model = User
        fields = ["kind", "first_name", "last_name", "phone", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update(
            {"placeholder": "Merci de bien vérifier l'adresse saisie.", "class": "form-control"}
        )
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].help_text = CnilCompositionPasswordValidator().get_help_text()
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

    def clean_email(self):
        email = self.cleaned_data["email"]
        return email.lower()


class PasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Votre adresse e-mail", widget=forms.TextInput(attrs={"class": "form-control"}), required=True
    )
