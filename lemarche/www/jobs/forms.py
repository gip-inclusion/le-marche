from django import forms

from lemarche.sectors.models import Sector
from lemarche.utils.fields import GroupedModelMultipleChoiceField
from lemarche.utils.widgets import CustomSelectMultiple


class SectorAppellationsForm(forms.Form):
    """
    Form to show appellations dynamically based on selected sectors.
    """

    sectors = GroupedModelMultipleChoiceField(
        label=Sector._meta.verbose_name_plural,
        queryset=Sector.objects.form_filter_queryset(),
        choices_groupby="group",
        to_field_name="slug",
        required=False,
        widget=CustomSelectMultiple(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sectors"].help_text = "Sélectionnez un ou plusieurs secteurs pour voir les métiers correspondants"
