import json

from django.test import TestCase

from lemarche.tenders import constants as tender_constants
from lemarche.tenders.models import Tender
from lemarche.www.tenders.forms import TenderCreateStepDetailForm, TenderCreateStepGeneralForm
from tests.tenders.factories import TenderFactory, TenderQuestionFactory


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


class TenderCreateStepDetailFormQuestionsListTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tender = TenderFactory(status=Tender.StatusChoices.STATUS_DRAFT)
        cls.question = TenderQuestionFactory(tender=cls.tender, text="Question du besoin")
        cls.other_tender = TenderFactory()
        cls.other_question = TenderQuestionFactory(tender=cls.other_tender, text="Question d'un autre besoin")

    def _form(self, questions_list, instance):
        return TenderCreateStepDetailForm(
            kind=tender_constants.KIND_QUOTE,
            data={"questions_list": json.dumps(questions_list)},
            instance=instance,
        )

    def test_own_question_id_is_accepted(self):
        form = self._form([{"id": self.question.id, "text": "Modifiée"}], instance=self.tender)
        form.is_valid()
        self.assertNotIn("questions_list", form.errors)

    def test_question_id_of_another_tender_is_rejected(self):
        form = self._form([{"id": self.other_question.id, "text": "Modifiée"}], instance=self.tender)
        self.assertFalse(form.is_valid())
        self.assertIn("questions_list", form.errors)

    def test_question_id_is_rejected_for_new_tender(self):
        form = self._form([{"id": self.other_question.id, "text": "Modifiée"}], instance=Tender())
        self.assertFalse(form.is_valid())
        self.assertIn("questions_list", form.errors)
