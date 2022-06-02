from django import forms

from lemarche.tenders.models import Tender


class TenderAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contact_email_list"].delimiter = ";"  # Or whichever other character you want.

    class Meta:
        model = Tender
        fields = "__all__"
