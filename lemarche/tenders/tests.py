import datetime

from django.db import IntegrityError
from django.forms import ValidationError
from django.test import TestCase

from lemarche.tenders.factories import TenderFactory


# Create your tests here.
class SiaeModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        str_test = "Mon test"
        tender = TenderFactory(title=str_test)
        self.assertEqual(str(tender), str_test)

    def test_deadline_start_before_today(self):
        today = datetime.date.today()
        tender = TenderFactory()
        tender.deadline_date = today - datetime.timedelta(days=1)
        self.assertRaises(ValidationError, tender.clean)

    def test_deadline_start_after_start_working_date(self):
        tender = TenderFactory()
        tender.start_working_date = tender.deadline_date - datetime.timedelta(days=1)
        self.assertRaises(ValidationError, tender.clean)

    def test_not_empty_deadline(self):
        tender = TenderFactory()
        tender.deadline_date = None
        self.assertRaises(IntegrityError, tender.save)
