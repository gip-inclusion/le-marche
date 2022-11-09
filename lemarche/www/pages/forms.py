from django import forms
from django.db.models import Case, Count, F, IntegerField, Sum, When

from lemarche.siaes.models import Siae
from lemarche.utils.constants import EMPTY_CHOICE
from lemarche.www.siaes.forms import SiaeSearchForm


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


class ImpactCalculatorForm(SiaeSearchForm):
    # sectors = GroupedModelMultipleChoiceField(
    #     label=Sector._meta.verbose_name_plural,
    #     queryset=Sector.objects.form_filter_queryset(),
    #     choices_groupby="group",
    #     to_field_name="slug",
    #     required=True,
    # )
    # # The hidden `perimeters` field is populated by the JS autocomplete library, see `perimeters_autocomplete_field.js`  # noqa
    # perimeters = forms.ModelMultipleChoiceField(
    #     label=Perimeter._meta.verbose_name_plural,
    #     queryset=Perimeter.objects.all(),
    #     to_field_name="slug",
    #     required=True,
    #     # widget=forms.HiddenInput()
    # )
    # presta_type = forms.MultipleChoiceField(
    #     label=Siae._meta.get_field("presta_type").verbose_name,
    #     choices=siae_constants.PRESTA_CHOICES,
    #     required=True,
    # )

    class Meta:
        model = Siae
        fields = ["sectors", "perimeters", "presta_type"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # required fields
        self.fields["sectors"].required = True
        self.fields["perimeters"].required = True
        self.fields["presta_type"].required = True

    def impact_aggregation(self, qs=None):
        if not qs:
            qs = self.filter_queryset()
        qs = qs.annotate(
            ca_declared=Case(
                When(ca__isnull=False, then=F("ca")),
                When(ca__isnull=True, api_entreprise_ca__isnull=False, then=F("api_entreprise_ca")),
                default=0,
            ),
            employees_insertion=Case(
                When(c2_etp_count__isnull=False, then=F("c2_etp_count")),
                When(employees_insertion_count__isnull=False, then=F("employees_insertion_count")),
                default=0,
                output_field=IntegerField(),
            ),
        )
        return qs.aggregate(Count("id"), Sum("employees_insertion"), Sum("ca_declared"))
