from django import forms

from lemarche.utils.constants import EMPTY_CHOICE


class ContactForm(forms.Form):
    KIND_CHOICES = EMPTY_CHOICE + (
        ("SIAE", "Entreprise sociale inclusive (SIAE, EA, GEIQ, ESAT)"),
        ("BUYER", "Acheteurs privés ou publics"),
        ("PARTNER", "Facilitateurs des clauses sociales"),
        ("OTHER", "Autre"),
    )
    first_name = forms.CharField(
        label="Prénom",
        widget=forms.TextInput(attrs={"autofocus": "autofocus"}),
        required=False,
    )
    last_name = forms.CharField(label="Nom", required=False)
    email = forms.EmailField(label="Adresse e-mail", required=True)
    phone = forms.CharField(
        label="Numéro de téléphone",
        max_length=16,
        required=False,
    )
    kind = forms.ChoiceField(label="Type d'utilisateur", widget=forms.Select, choices=KIND_CHOICES, required=True)
    siret = forms.CharField(
        label="SIRET",
        required=False,
    )

    # subject = ChoiceField + choices=SUBJECT_CHOICES ?
    subject = forms.CharField(label="Sujet", max_length=150, required=True)

    message = forms.CharField(label="Message", widget=forms.Textarea(), required=True)
