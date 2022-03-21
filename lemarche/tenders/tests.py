import datetime

from django.db import IntegrityError
from django.forms import ValidationError
from django.test import TestCase

from lemarche.sectors.factories import SectorFactory
from lemarche.tenders.factories import TenderFactory
from lemarche.tenders.models import Tender


class TenderModelTest(TestCase):
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


class TenderModelQuerysetTest(TestCase):
    def setUp(self):
        pass

    def test_in_sectors_queryset(self):
        sector_1 = SectorFactory(name="Un secteur")
        sector_2 = SectorFactory(name="Un deuxieme secteur")
        sector_3 = SectorFactory(name="Autre")
        TenderFactory()
        TenderFactory(sectors=[sector_1, sector_2])
        self.assertEqual(Tender.objects.in_sectors([sector_1]).count(), 1)
        self.assertEqual(Tender.objects.in_sectors([sector_1, sector_2]).count(), 1)
        self.assertEqual(Tender.objects.in_sectors([sector_1, sector_3]).count(), 1)
        self.assertEqual(Tender.objects.in_sectors([sector_3]).count(), 0)
        self.assertEqual(Tender.objects.in_sectors([]).count(), 2)
