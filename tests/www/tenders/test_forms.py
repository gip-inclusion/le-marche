from django.test import TestCase

from lemarche.tenders import constants as tender_constants
from lemarche.www.tenders.forms import TenderCreateStepGeneralForm


class TenderCreateStepGeneralFormTest(TestCase):
    def _data(self, description):
        return {
            "kind": tender_constants.KIND_QUOTE,
            "title": "Titre du besoin",
            "description": description,
            "is_country_area": True,
        }

    def test_description_is_sanitized(self):
        form = TenderCreateStepGeneralForm(data=self._data("<p>ok</p><script>alert('xss')</script>"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertNotIn("<script", form.cleaned_data["description"])

    def test_description_preserves_legitimate_formatting(self):
        html = '<p>Voir <a href="https://example.com" target="_blank" rel="noopener">ici</a></p>'
        form = TenderCreateStepGeneralForm(data=self._data(html))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn('href="https://example.com"', form.cleaned_data["description"])

    def test_description_only_dangerous_markup_is_rejected_as_required(self):
        form = TenderCreateStepGeneralForm(data=self._data("<script>alert('xss')</script>"))
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)
