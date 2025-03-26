from django import forms

from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender, TenderQuestion


class TenderAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contact_email_list"].delimiter = ";"  # Or whichever other character you want.

    class Meta:
        model = Tender
        fields = "__all__"


class QuestionAnswerForm(forms.Form):
    answer = forms.CharField(label="Réponse", widget=forms.Textarea(attrs={"required": "required"}))
    question = forms.ModelChoiceField(
        label="Question", queryset=TenderQuestion.objects.all(), widget=forms.HiddenInput()
    )


class SiaeSelectionForm(forms.Form):
    siae = forms.ModelMultipleChoiceField(
        label="Pour quelle(s) structure(s) souhaitez-vous répondre ?",
        queryset=Siae.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
    )

    def __init__(self, queryset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["siae"].queryset = queryset
