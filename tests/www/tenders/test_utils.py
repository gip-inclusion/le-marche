from django.test import TestCase

from lemarche.www.tenders.utils import update_or_create_questions_list
from tests.tenders.factories import TenderFactory, TenderQuestionFactory


class UpdateOrCreateQuestionsListTest(TestCase):
    def test_update_own_question(self):
        tender = TenderFactory()
        question = TenderQuestionFactory(tender=tender, text="Original")

        update_or_create_questions_list(tender, [{"id": question.id, "text": "Modifiée"}, {"text": "Nouvelle"}])

        question.refresh_from_db()
        self.assertEqual(question.text, "Modifiée")
        self.assertEqual(tender.questions.count(), 2)

    def test_cannot_update_question_of_another_tender(self):
        tender = TenderFactory()
        other_tender = TenderFactory()
        other_question = TenderQuestionFactory(tender=other_tender, text="Original")

        update_or_create_questions_list(tender, [{"id": other_question.id, "text": "Modifiée"}])

        other_question.refresh_from_db()
        self.assertEqual(other_question.text, "Original")
        self.assertEqual(other_question.tender, other_tender)
