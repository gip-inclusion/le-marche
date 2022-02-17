from django import forms

from lemarche.tenders.models import Tender


class AddTenderForm(forms.ModelForm):
    class Meta:
        model = Tender
        fields = [
            "kind",
            "title",
            "description",
            "sector",
            "constraints",
            "completion_time",
            "perimeter",
            "external_link",
            "kind_response",
        ]
