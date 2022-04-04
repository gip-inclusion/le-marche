import datetime

from django.db import IntegrityError
from django.forms import ValidationError
from django.test import TestCase
from django.utils import timezone

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders.factories import TenderFactory
from lemarche.tenders.models import Tender, TenderSiae
from lemarche.users.factories import UserFactory


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

    def test_by_user_queryset(self):
        user = UserFactory()
        TenderFactory(author=user)
        TenderFactory()
        self.assertEqual(Tender.objects.by_user(user).count(), 1)

    def test_in_sectors_queryset(self):
        sector_1 = SectorFactory(name="Un secteur")
        sector_2 = SectorFactory(name="Un deuxieme secteur")
        sector_3 = SectorFactory(name="Autre")
        TenderFactory()
        TenderFactory(sectors=[sector_1, sector_2])
        self.assertEqual(Tender.objects.in_sectors([]).count(), 2)
        self.assertEqual(Tender.objects.in_sectors([sector_1]).count(), 1)
        self.assertEqual(Tender.objects.in_sectors([sector_1, sector_2]).count(), 1)
        self.assertEqual(Tender.objects.in_sectors([sector_1, sector_3]).count(), 1)
        self.assertEqual(Tender.objects.in_sectors([sector_3]).count(), 0)

    def test_in_perimeters_queryset(self):
        # create the Perimeters
        auvergne_rhone_alpes_perimeter = PerimeterFactory(
            name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84"
        )
        isere_perimeter = PerimeterFactory(
            name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84"
        )
        grenoble_perimeter = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
            # coords=Point(5.7301, 45.1825),
        )
        chamrousse_perimeter = PerimeterFactory(
            name="Chamrousse",
            kind=Perimeter.KIND_CITY,
            insee_code="38567",
            department_code="38",
            region_code="84",
            post_codes=["38410"],
            # coords=Point(5.8862, 45.1106),
        )
        TenderFactory(perimeters=[auvergne_rhone_alpes_perimeter])
        TenderFactory(perimeters=[isere_perimeter])
        TenderFactory(perimeters=[grenoble_perimeter])
        TenderFactory(perimeters=[chamrousse_perimeter])
        TenderFactory(perimeters=[grenoble_perimeter, chamrousse_perimeter])
        # self.assertEqual(Tender.objects.in_perimeters().count(), 5)
        self.assertEqual(
            Tender.objects.in_perimeters(post_code="38000", department="38", region="Auvergne-Rhône-Alpes").count(), 4
        )
        self.assertEqual(
            Tender.objects.in_perimeters(post_code="38100", department="38", region="Auvergne-Rhône-Alpes").count(), 4
        )
        self.assertEqual(
            Tender.objects.in_perimeters(post_code="38190", department="38", region="Auvergne-Rhône-Alpes").count(), 2
        )
        self.assertEqual(
            Tender.objects.in_perimeters(post_code="01300", department="01", region="Auvergne-Rhône-Alpes").count(), 1
        )
        self.assertEqual(
            Tender.objects.in_perimeters(post_code="29000", department="29", region="Bretagne").count(), 0
        )

    def test_with_siae_stats_queryset(self):
        siae_1 = SiaeFactory()
        siae_2 = SiaeFactory()
        siae_3 = SiaeFactory()
        tender = TenderFactory(siaes=[siae_1])
        TenderSiae.objects.create(tender=tender, siae=siae_2, email_send_date=timezone.now())
        TenderSiae.objects.create(
            tender=tender, siae=siae_3, email_send_date=timezone.now(), detail_display_date=timezone.now()
        )
        TenderFactory()
        self.assertEqual(tender.siaes.count(), 3)
        self.assertEqual(Tender.objects.count(), 2)
        tender_in_queryset = Tender.objects.with_siae_stats().first()
        self.assertEqual(tender_in_queryset.siae_email_send_count, 2)
        self.assertEqual(tender_in_queryset.siae_detail_display_count, 1)
        empty_tender_in_queryset = Tender.objects.with_siae_stats().last()
        self.assertEqual(empty_tender_in_queryset.siae_email_send_count, 0)
        self.assertEqual(empty_tender_in_queryset.siae_detail_display_count, 0)
