from django import forms


class ContactForm(forms.Form):
    first_name = forms.CharField(
        label="Prénom",
        widget=forms.TextInput(attrs={"autofocus": "autofocus", "class": "form-control"}),
        required=False,
    )
    last_name = forms.CharField(label="Nom", widget=forms.TextInput(attrs={"class": "form-control"}), required=False)
    email = forms.EmailField(
        label="Adresse e-mail", widget=forms.TextInput(attrs={"class": "form-control"}), required=True
    )
    phone = forms.CharField(
        label="Numéro de téléphone",
        max_length=16,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False,
    )
    siret = forms.CharField(
        label="SIRET",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False,
    )

    # ChoiceField + choices=SUBJECT_CHOICES ?
    subject = forms.CharField(
        label="Sujet", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}), required=True
    )

    message = forms.CharField(label="Message", widget=forms.Textarea(attrs={"class": "form-control"}), required=True)
