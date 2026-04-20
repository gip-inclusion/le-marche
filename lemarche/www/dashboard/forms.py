from django import forms
from django.forms import formset_factory

from lemarche.conversations.models import DisabledEmail, EmailGroup
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.models import Sector
from lemarche.users.models import User
from lemarche.utils.emails import update_contact_email_blacklisted
from lemarche.utils.fields import GroupedModelMultipleChoiceField
from lemarche.utils.widgets import CustomSelectMultiple


class ProfileEditForm(forms.ModelForm):
    sectors = GroupedModelMultipleChoiceField(
        label=Sector._meta.verbose_name_plural,
        queryset=Sector.objects.form_filter_queryset(),
        choices_groupby="group",
        to_field_name="slug",
        required=True,
        widget=CustomSelectMultiple(),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "email", "sectors"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mandatory fields.
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True
        if self.instance.kind != User.KIND_BUYER:
            self.fields["sectors"].widget = forms.HiddenInput()
            self.fields["sectors"].required = False

        # Disabled fields
        self.fields["email"].disabled = True


class DisabledEmailEditForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.group_items = []
        super().__init__(*args, **kwargs)

        disabled_groups = [disable_email.group for disable_email in self.user.disabled_emails.all()]
        for email_group in EmailGroup.objects.filter(can_be_unsubscribed=True, relevant_user_kind=self.user.kind):
            field_name = f"email_group_{email_group.pk}"
            self.fields[field_name] = forms.BooleanField(
                required=False,
                label=email_group.display_name,
                initial=email_group not in disabled_groups,
                widget=forms.CheckboxInput(),
            )
            self.group_items.append({"group": email_group, "field_name": field_name})

    def save(self):
        disabled_emails = []

        disabled_emails_marketing = False

        # add unchecked fields to disabled_emails
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith("email_group_") and not value:
                group = EmailGroup.objects.get(pk=int(field_name.replace("email_group_", "")))
                disabled_email, _ = DisabledEmail.objects.get_or_create(user=self.user, group=group)
                disabled_emails.append(disabled_email)

                if group.display_name == EmailGroup.COMMUNICATION_MARKETING:
                    disabled_emails_marketing = True

        self.user.disabled_emails.set(disabled_emails)

        # remove old disabled_emails
        DisabledEmail.objects.exclude(pk__in=[de.pk for de in disabled_emails]).delete()

        update_contact_email_blacklisted(self.user.email, disabled_emails_marketing)


class PurchaseProjectForm(forms.Form):
    titre = forms.CharField(
        label="Titre du projet d'achat",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "fr-input", "placeholder": "Ex : Prestations de nettoyage"}),
    )
    description = forms.CharField(
        label="Description (optionnelle)",
        required=False,
        widget=forms.Textarea(attrs={"class": "fr-input", "rows": 2, "placeholder": "Décrivez brièvement le besoin"}),
    )
    secteur = forms.ModelChoiceField(
        label="Secteur d'achat",
        queryset=Sector.objects.form_filter_queryset(),
        to_field_name="slug",
        empty_label="Sélectionnez un secteur",
        widget=forms.Select(attrs={"class": "fr-select"}),
    )
    montant = forms.IntegerField(
        label="Montant estimatif (€)",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "fr-input", "placeholder": "Ex : 80000"}),
    )
    perimeter_slug = forms.CharField(
        label="Périmètre géographique",
        required=False,
        widget=forms.HiddenInput(),
    )
    france_entiere = forms.BooleanField(
        label="Toute la France (structures à couverture nationale)",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "fr-checkbox-group__input"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        perimeter_slug = cleaned_data.get("perimeter_slug")
        france_entiere = cleaned_data.get("france_entiere")

        if france_entiere and perimeter_slug:
            raise forms.ValidationError(
                "Veuillez sélectionner soit un périmètre géographique, soit \"Toute la France\", pas les deux."
            )
        if not france_entiere and not perimeter_slug:
            raise forms.ValidationError(
                "Le périmètre géographique est obligatoire. Sélectionnez une zone ou choisissez \"Toute la France\"."
            )

        if perimeter_slug:
            try:
                Perimeter.objects.get(slug=perimeter_slug)
            except Perimeter.DoesNotExist:
                self.add_error(
                    "perimeter_slug",
                    f"Le périmètre géographique '{perimeter_slug}' n'est pas reconnu.",
                )

        return cleaned_data


PurchaseProjectFormSet = formset_factory(PurchaseProjectForm, extra=0)
