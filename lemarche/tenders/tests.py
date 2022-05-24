# import datetime
from importlib import import_module
from random import randint

from django.apps import apps
from django.db import IntegrityError

# from django.forms import ValidationError
from django.test import TestCase
from django.utils import timezone

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.tenders.factories import PartnerShareTenderFactory, TenderFactory
from lemarche.tenders.models import AMOUNT_RANGE_0, AMOUNT_RANGE_2, AMOUNT_RANGE_3, AMOUNT_RANGE_4, Tender, TenderSiae
from lemarche.users.factories import UserFactory
from lemarche.www.tenders.tasks import match_tender_for_partners


class TenderModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        str_test = "Mon test"
        tender = TenderFactory(title=str_test)
        self.assertEqual(str(tender), str_test)

    # todo : update with testing form
    # def test_deadline_start_before_today(self):
    #     today = datetime.date.today()
    #     tender = TenderFactory()
    #     tender.deadline_date = today - datetime.timedelta(days=1)
    #     self.assertNotRaises(ValidationError, tender.clean)

    # def test_deadline_start_after_start_working_date(self):
    #     tender = TenderFactory()
    #     tender.start_working_date = tender.deadline_date - datetime.timedelta(days=1)
    #     self.assertRaises(ValidationError, tender.clean)

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
        siae_4 = SiaeFactory()
        tender_with_siae = TenderFactory(siaes=[siae_1])
        TenderSiae.objects.create(tender=tender_with_siae, siae=siae_2, email_send_date=timezone.now())
        TenderSiae.objects.create(
            tender=tender_with_siae, siae=siae_3, email_send_date=timezone.now(), detail_display_date=timezone.now()
        )
        TenderSiae.objects.create(
            tender=tender_with_siae,
            siae=siae_4,
            email_send_date=timezone.now(),
            detail_display_date=timezone.now(),
            contact_click_date=timezone.now(),
        )
        tender_without_siae = TenderFactory()
        self.assertEqual(tender_with_siae.siaes.count(), 4)
        self.assertEqual(Tender.objects.count(), 2)
        tender_with_siae = Tender.objects.with_siae_stats().first()
        self.assertEqual(tender_with_siae.siae_email_send_count, 3)
        self.assertEqual(tender_with_siae.siae_detail_display_count, 2)
        self.assertEqual(tender_with_siae.siae_contact_click_count, 1)
        tender_without_siae = Tender.objects.with_siae_stats().last()
        self.assertEqual(tender_without_siae.siae_email_send_count, 0)
        self.assertEqual(tender_without_siae.siae_detail_display_count, 0)
        self.assertEqual(tender_without_siae.siae_contact_click_count, 0)


class TenderMigrationToSelectTest(TestCase):
    def test_migrate_amount_to_select(self):
        # the migrations can't be imported directly, it's a syntax error.
        migration = import_module("lemarche.tenders.migrations.0006_alter_tender_amount")

        tender_amount_none = TenderFactory(amount=None)
        tender_amount_range_0 = TenderFactory(amount=randint(0, 25000 - 1))
        tender_amount_range_1 = TenderFactory(amount=randint(25000, 100000 - 1))
        tender_amount_range_2 = TenderFactory(amount=randint(100000, 1000000 - 1))
        tender_amount_range_3 = TenderFactory(amount=randint(1000000, 5000000 - 1))
        tender_amount_range_4 = TenderFactory(amount=randint(5000000, 10000000))

        migration.update_amount(apps, None)

        tender_amount_none.refresh_from_db()
        tender_amount_range_0.refresh_from_db()
        tender_amount_range_1.refresh_from_db()
        tender_amount_range_2.refresh_from_db()
        tender_amount_range_3.refresh_from_db()
        tender_amount_range_4.refresh_from_db()

        self.assertIsNone(tender_amount_none.amount)
        self.assertEqual(tender_amount_range_0.amount, Tender.AMOUNT_RANGE_0)
        self.assertEqual(tender_amount_range_1.amount, Tender.AMOUNT_RANGE_1)
        self.assertEqual(tender_amount_range_2.amount, Tender.AMOUNT_RANGE_2)
        self.assertEqual(tender_amount_range_3.amount, Tender.AMOUNT_RANGE_3)
        self.assertEqual(tender_amount_range_4.amount, Tender.AMOUNT_RANGE_4)

        # test reverse method
        migration.reverse_update_amount(apps, None)
        tender_amount_range_0.refresh_from_db()
        self.assertEqual(int(tender_amount_range_0.amount), 24999)


class TenderPartnerMatchingTest(TestCase):
    @classmethod
    def setUpTestData(self):
        # perimeters
        self.perimeter_1 = PerimeterFactory()
        self.perimeter_2 = PerimeterFactory()
        # partners
        PartnerShareTenderFactory(perimeters=[self.perimeter_1])
        PartnerShareTenderFactory(perimeters=[])
        PartnerShareTenderFactory(perimeters=[self.perimeter_1])
        PartnerShareTenderFactory(perimeters=[self.perimeter_2])
        PartnerShareTenderFactory(perimeters=[], amount_in=AMOUNT_RANGE_0)
        PartnerShareTenderFactory(perimeters=[], amount_in=AMOUNT_RANGE_2)
        PartnerShareTenderFactory(perimeters=[], amount_in=AMOUNT_RANGE_3)
        PartnerShareTenderFactory(perimeters=[self.perimeter_1, self.perimeter_2], amount_in=AMOUNT_RANGE_2)
        # tenders
        self.tender_1 = TenderFactory(perimeters=[self.perimeter_1, self.perimeter_2])
        self.tender_2 = TenderFactory(perimeters=[self.perimeter_1], amount=AMOUNT_RANGE_0)
        self.tender_3 = TenderFactory(perimeters=[self.perimeter_2], amount=AMOUNT_RANGE_2)
        self.tender_4 = TenderFactory(is_country_area=True, amount=AMOUNT_RANGE_2)
        self.tender_5 = TenderFactory(is_country_area=True, amount=AMOUNT_RANGE_4)

    def test_partner_1_matching(self):
        result = match_tender_for_partners(self.tender_1)
        # partner 1, 2, 3, 4, 5, 6, 7, 8
        self.assertEqual(len(result), 8)

    def test_partner_2_matching(self):

        result = match_tender_for_partners(self.tender_2)
        # partner 1, 2, 3, 5, 6, 7, 8
        self.assertEqual(len(result), 7)

    def test_partner_3_matching(self):
        result = match_tender_for_partners(self.tender_3)
        # partner 2, 4, 6, 7, 8
        self.assertEqual(len(result), 5)

    def test_partner_4_matching(self):
        result = match_tender_for_partners(self.tender_4)
        # partner 2, 6, 7
        self.assertEqual(len(result), 3)

    def test_partner_5_matching(self):
        result = match_tender_for_partners(self.tender_5)
        # partner 2
        self.assertEqual(len(result), 1)
