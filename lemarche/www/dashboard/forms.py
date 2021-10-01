from django import forms

from lemarche.siaes.models import Siae
from lemarche.users.models import User


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]

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
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=True,
    )

    def clean_siret(self):
        siret = self.cleaned_data["siret"]
        if siret:
            # strip spaces (beginning, inbetween, end)
            siret = siret.replace(" ", "")
            # check siret length
            if len(siret) < 8:
                msg = "Le longueur du numéro doit être supérieure ou égale à 9 caractères."
                raise forms.ValidationError(msg)
            if len(siret) > 14:
                msg = "Le longueur du numéro ne peut pas dépasser 14 caractères."
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


class SiaeAdoptConfirmForm(forms.ModelForm):
    class Meta:
        model = Siae
        fields = []
