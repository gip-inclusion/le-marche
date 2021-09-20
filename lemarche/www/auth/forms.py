from django import forms
from django.contrib.auth.forms import UserCreationForm

from lemarche.users.models import User


class SignupForm(UserCreationForm):
    KIND_CHOICES_FORM = (
        (User.KIND_SIAE, "Une entreprise sociale inclusive (SIAE ou structure du handicap, GEIQ)"),
        (User.KIND_BUYER, "Un acheteur"),
        (User.KIND_PARTNER, "Un partenaire (réseaux, facilitateurs)")
    )

    kind = forms.ChoiceField(
        label="",
        widget=forms.RadioSelect,
        choices=KIND_CHOICES_FORM,
        required=True)
    first_name = forms.CharField(
        label='Votre prénom',
        required=True)
    last_name = forms.CharField(
        label='Votre nom',
        required=True)
    phone = forms.CharField(
        label='Votre numéro de téléphone',
        max_length=35,
        required=False)
    email = forms.EmailField(
        label='Votre adresse e-mail',
        required=True,
        help_text="Nous enverrons un e-mail de confirmation à cette adresse avant de valider le compte.")  # noqa

    class Meta:
        model = User
        fields = [
            "kind", "first_name", "last_name", "phone",
            "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'autofocus': True})
        self.fields['email'].widget.attrs.update({
            'placeholder': "Merci de bien vérifier l'adresse saisie."})

    def clean_email(self):
        email = self.cleaned_data['email']
        return email.lower()
