from django import forms

from lemarche.sectors.models import Sector
from lemarche.users.models import User
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
