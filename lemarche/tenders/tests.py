# import datetime
from datetime import datetime, timedelta
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
from lemarche.siaes.models import Siae
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.factories import PartnerShareTenderFactory, TenderFactory
from lemarche.tenders.models import PartnerShareTender, Tender, TenderSiae
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class TenderModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        str_test = "Mon test"
        tender = TenderFactory(title=str_test)
        self.assertEqual(str(tender), str_test)

    def test_set_slug(self):
        tender = TenderFactory(title="Un besoin")
        self.assertEqual(tender.slug, "un-besoin")
        # with author
        user_1 = UserFactory(kind=User.KIND_BUYER)
        tender = TenderFactory(title="Un autre besoin", author=user_1)
        self.assertEqual(tender.slug, "un-autre-besoin")
        # with author.company_name
        user_2 = UserFactory(kind=User.KIND_BUYER, company_name="L'entreprise A")
        tender = TenderFactory(title="Un 3e besoin", author=user_2)
        self.assertEqual(tender.slug, "un-3e-besoin-lentreprise-a")

    # todo : update with testing form
    # def test_deadline_start_before_today(self):
    #     today = datetime.date.today()
    #     tender = TenderFactory()
    #     tender.deadline_date = today - timedelta(days=1)
    #     self.assertNotRaises(ValidationError, tender.clean)

    # def test_deadline_start_after_start_working_date(self):
    #     tender = TenderFactory()
    #     tender.start_working_date = tender.deadline_date - timedelta(days=1)
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

    def test_validated_queryset(self):
        TenderFactory(validated_at=timezone.now())
        TenderFactory(validated_at=None)
        self.assertEqual(Tender.objects.validated().count(), 1)

    def test_is_live_queryset(self):
        TenderFactory(deadline_date=timezone.now() + timedelta(days=1))
        TenderFactory(deadline_date=timezone.now() - timedelta(days=1))
        # TenderFactory(deadline_date=None)  # cannot be None
        self.assertEqual(Tender.objects.is_live().count(), 1)

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


class TenderModelQuerysetStatsTest(TestCase):
    @classmethod
    def setUpTestData(self):
        date_tomorrow = datetime.now() + timedelta(days=1)
        self.user_siae = UserFactory(kind=User.KIND_SIAE)
        self.siae_with_tender_1 = SiaeFactory(users=[self.user_siae])
        siae_with_tender_2 = SiaeFactory(users=[self.user_siae])
        siae_with_tender_3 = SiaeFactory(users=[self.user_siae])
        siae_with_tender_4 = SiaeFactory()
        siae_with_tender_5 = SiaeFactory()
        self.siae_without_tender = SiaeFactory()
        self.tender_with_siae_1 = TenderFactory(
            siaes=[self.siae_with_tender_1, siae_with_tender_2], deadline_date=timezone.make_aware(date_tomorrow)
        )
        TenderSiae.objects.create(
            tender=self.tender_with_siae_1, siae=siae_with_tender_3, email_send_date=timezone.now()
        )
        TenderSiae.objects.create(
            tender=self.tender_with_siae_1,
            siae=siae_with_tender_4,
            email_send_date=timezone.now(),
            detail_display_date=timezone.now(),
        )
        TenderSiae.objects.create(
            tender=self.tender_with_siae_1,
            siae=siae_with_tender_5,
            email_send_date=timezone.now(),
            detail_display_date=timezone.now(),
            contact_click_date=timezone.now(),
        )
        self.tender_with_siae_2 = TenderFactory()
        TenderSiae.objects.create(
            tender=self.tender_with_siae_2,
            siae=self.siae_with_tender_1,
            email_send_date=timezone.now(),
            detail_display_date=timezone.now(),
            contact_click_date=timezone.now(),
        )
        self.tender_without_siae = TenderFactory(deadline_date=timezone.make_aware(date_tomorrow))

    def test_filter_with_siaes_queryset(self):
        self.tender_with_siae_2.validated_at = None
        self.tender_with_siae_2.save()
        # tender_with_siae_2 is not validated
        self.assertEqual(Tender.objects.filter_with_siaes(self.user_siae.siaes.all()).count(), 1)

    def test_with_siae_stats_queryset(self):
        self.assertEqual(Tender.objects.count(), 2 + 1)
        tender_with_siae_1 = Tender.objects.with_siae_stats().filter(id=self.tender_with_siae_1.id).first()
        self.assertEqual(tender_with_siae_1.siaes.count(), 5)
        self.assertEqual(tender_with_siae_1.siae_count, 5)
        self.assertEqual(tender_with_siae_1.siae_email_send_count, 3)
        self.assertEqual(tender_with_siae_1.siae_detail_display_count, 2)
        self.assertEqual(tender_with_siae_1.siae_contact_click_count, 1)
        self.assertEqual(tender_with_siae_1.siae_contact_click_since_last_seen_date_count, 1)
        tender_with_siae_2 = Tender.objects.with_siae_stats().filter(id=self.tender_with_siae_2.id).first()
        self.assertEqual(tender_with_siae_2.siaes.count(), 1)
        self.assertEqual(tender_with_siae_2.siae_count, 1)
        self.assertEqual(tender_with_siae_2.siae_email_send_count, 1)
        self.assertEqual(tender_with_siae_2.siae_detail_display_count, 1)
        self.assertEqual(tender_with_siae_2.siae_contact_click_count, 1)
        self.assertEqual(tender_with_siae_2.siae_contact_click_since_last_seen_date_count, 1)
        tender_without_siae = Tender.objects.with_siae_stats().filter(id=self.tender_without_siae.id).first()
        self.assertEqual(tender_without_siae.siaes.count(), 0)
        self.assertEqual(tender_without_siae.siae_count, 0)
        self.assertEqual(tender_without_siae.siae_email_send_count, 0)
        self.assertEqual(tender_without_siae.siae_detail_display_count, 0)
        self.assertEqual(tender_without_siae.siae_contact_click_count, 0)
        self.assertEqual(tender_without_siae.siae_contact_click_since_last_seen_date_count, 0)

    def test_siae_with_tender_stats_queryset(self):
        self.assertEqual(Siae.objects.count(), 5 + 1)
        siae_with_tender_1 = Siae.objects.with_tender_stats().filter(id=self.siae_with_tender_1.id).first()
        # self.assertEqual(siae_with_tender_1.tenders.count(), 2)
        self.assertEqual(siae_with_tender_1.tender_count, 2)
        self.assertEqual(siae_with_tender_1.tender_email_send_count, 1)
        self.assertEqual(siae_with_tender_1.tender_detail_display_count, 1)
        self.assertEqual(siae_with_tender_1.tender_contact_click_count, 1)
        siae_without_tender = Siae.objects.with_tender_stats().filter(id=self.siae_without_tender.id).first()
        self.assertEqual(siae_without_tender.tenders.count(), 0)
        self.assertEqual(siae_without_tender.tender_count, 0)
        self.assertEqual(siae_without_tender.tender_email_send_count, 0)
        self.assertEqual(siae_without_tender.tender_detail_display_count, 0)
        self.assertEqual(siae_without_tender.tender_contact_click_count, 0)

    def test_with_deadline_date_is_outdated_queryset(self):
        date_last_week = datetime.now() - timedelta(days=7)
        TenderFactory(deadline_date=timezone.make_aware(date_last_week))
        tender_queryset = Tender.objects.with_deadline_date_is_outdated()
        tender_3 = tender_queryset.first()  # order by -created_at
        self.assertTrue(tender_3.deadline_date_is_outdated)
        tender_with_siae_1 = tender_queryset.last()
        self.assertEqual(tender_with_siae_1.id, self.tender_with_siae_1.id)
        self.assertFalse(tender_with_siae_1.deadline_date_is_outdated)


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
        self.assertEqual(tender_amount_range_0.amount, tender_constants.OLD_AMOUNT_RANGE_0)
        self.assertEqual(tender_amount_range_1.amount, tender_constants.OLD_AMOUNT_RANGE_1)
        self.assertEqual(tender_amount_range_2.amount, tender_constants.OLD_AMOUNT_RANGE_2)
        self.assertEqual(tender_amount_range_3.amount, tender_constants.OLD_AMOUNT_RANGE_3)
        self.assertEqual(tender_amount_range_4.amount, tender_constants.OLD_AMOUNT_RANGE_4)

        # test reverse method
        migration.reverse_update_amount(apps, None)
        tender_amount_range_0.refresh_from_db()
        self.assertEqual(int(tender_amount_range_0.amount), 24999)


class TenderPartnerMatchingTest(TestCase):
    @classmethod
    def setUpTestData(self):
        # perimeters
        self.auvergne_rhone_alpes_perimeter = PerimeterFactory(
            name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84"
        )
        self.isere_perimeter = PerimeterFactory(
            name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84"
        )
        self.rhone_perimeter = PerimeterFactory(
            name="Rhône", kind=Perimeter.KIND_DEPARTMENT, insee_code="69", region_code="84"
        )
        self.grenoble_perimeter = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
            # coords=Point(5.7301, 45.1825),
        )
        # partners
        PartnerShareTenderFactory(perimeters=[])
        PartnerShareTenderFactory(perimeters=[self.auvergne_rhone_alpes_perimeter])
        PartnerShareTenderFactory(perimeters=[self.isere_perimeter])
        PartnerShareTenderFactory(perimeters=[self.grenoble_perimeter])
        PartnerShareTenderFactory(perimeters=[], amount_in=tender_constants.AMOUNT_RANGE_0_1)
        PartnerShareTenderFactory(perimeters=[], amount_in=tender_constants.AMOUNT_RANGE_10_15)
        PartnerShareTenderFactory(perimeters=[], amount_in=tender_constants.AMOUNT_RANGE_100_150)
        PartnerShareTenderFactory(
            perimeters=[self.isere_perimeter, self.rhone_perimeter], amount_in=tender_constants.AMOUNT_RANGE_10_15
        )

    def test_tender_country_matching(self):
        # partners with perimeters=[]
        tender = TenderFactory(is_country_area=True)
        result = PartnerShareTender.objects.filter_by_tender(tender)
        self.assertEqual(len(result), 4)

    def test_tender_perimeters_matching(self):
        # partners with perimeters=[] + aura
        tender = TenderFactory(perimeters=[self.auvergne_rhone_alpes_perimeter])
        result = PartnerShareTender.objects.filter_by_tender(tender)
        self.assertEqual(len(result), 4 + 1)
        # partners with perimeters=[] + isere + aura
        tender = TenderFactory(perimeters=[self.rhone_perimeter])
        result = PartnerShareTender.objects.filter_by_tender(tender)
        self.assertEqual(len(result), 4 + 1 + 1)
        # partners with perimeters=[] + isere/rhone + aura
        tender = TenderFactory(perimeters=[self.isere_perimeter, self.rhone_perimeter])
        result = PartnerShareTender.objects.filter_by_tender(tender)
        self.assertEqual(len(result), 4 + 2 + 1)
        # partners with perimeters=[] + grenoble + isere/rhone + aura
        tender = TenderFactory(perimeters=[self.grenoble_perimeter])
        result = PartnerShareTender.objects.filter_by_tender(tender)
        self.assertEqual(len(result), 4 + 1 + 2 + 1)

    def test_tender_country_and_amount_matching(self):
        # partners with perimeters=[] & (amount_in empty or >=AMOUNT_RANGE_0_1)
        tender = TenderFactory(is_country_area=True, amount=tender_constants.AMOUNT_RANGE_0_1)
        result = PartnerShareTender.objects.filter_by_tender(tender)
        self.assertEqual(len(result), 4)
        # partners with perimeters=[] & (amount_in empty or >=AMOUNT_RANGE_10_15)
        tender = TenderFactory(is_country_area=True, amount=tender_constants.AMOUNT_RANGE_10_15)
        result = PartnerShareTender.objects.filter_by_tender(tender)
        self.assertEqual(len(result), 3)
        # partners with perimeters=[] & (amount_in empty or >=AMOUNT_RANGE_1000_MORE)
        tender = TenderFactory(is_country_area=True, amount=tender_constants.AMOUNT_RANGE_1000_MORE)
        result = PartnerShareTender.objects.filter_by_tender(tender)
        self.assertEqual(len(result), 1)

    def test_tender_perimeters_and_amount_matching(self):
        # partners with (perimeters=[] or aura) & (amount_in empty or >=AMOUNT_RANGE_0_1)
        tender = TenderFactory(
            perimeters=[self.auvergne_rhone_alpes_perimeter], amount=tender_constants.AMOUNT_RANGE_0_1
        )
        result = PartnerShareTender.objects.filter_by_tender(tender)
        self.assertEqual(len(result), 2 + 3)
        # partners with (perimeters=[] or isere overlap) & (amount_in empty or >=AMOUNT_RANGE_10_15)
        tender_3 = TenderFactory(perimeters=[self.isere_perimeter], amount=tender_constants.AMOUNT_RANGE_10_15)
        result = PartnerShareTender.objects.filter_by_tender(tender_3)
        self.assertEqual(len(result), 3 + 3)
