# import datetime
from datetime import timedelta
from importlib import import_module
from random import randint

from django.apps import apps
from django.contrib.gis.geos import Point
from django.forms.models import model_to_dict
from django.test import RequestFactory, TestCase
from django.utils import timezone

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory, SectorGroupFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.admin import TenderAdmin
from lemarche.tenders.factories import PartnerShareTenderFactory, TenderFactory, TenderQuestionFactory
from lemarche.tenders.models import PartnerShareTender, Tender, TenderQuestion, TenderSiae
from lemarche.users.factories import UserFactory
from lemarche.users.models import User
from lemarche.utils.admin.admin_site import MarcheAdminSite, get_admin_change_view_url


date_tomorrow = timezone.now() + timedelta(days=1)
date_next_week = timezone.now() + timedelta(days=7)
date_two_days_ago = timezone.now() - timedelta(days=2)
date_last_week = timezone.now() - timedelta(days=7)


class TenderModelTest(TestCase):
    def test_str(self):
        str_test = "Mon test"
        tender = TenderFactory(title=str_test)
        self.assertEqual(str(tender), str_test)


class TenderModelPropertyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.grenoble_perimeter = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
            # coords=Point(5.7301, 45.1825),
        )
        cls.chamrousse_perimeter = PerimeterFactory(
            name="Chamrousse",
            kind=Perimeter.KIND_CITY,
            insee_code="38567",
            department_code="38",
            region_code="84",
            post_codes=["38410"],
            # coords=Point(5.8862, 45.1106),
        )

    def test_sectors_list(self):
        sector_group = SectorGroupFactory(name="Bricolage")
        sector_1 = SectorFactory(name="Autre", group=sector_group)
        sector_2 = SectorFactory(name="Un secteur", group=sector_group)
        sector_3 = SectorFactory(name="Un autre secteur", group=None)
        tender_without_sectors = TenderFactory()
        self.assertEqual(len(tender_without_sectors.sectors_list()), 0)
        self.assertEqual(tender_without_sectors.sectors_list_string(), "")
        tender_with_sectors = TenderFactory(sectors=[sector_1, sector_2, sector_3])
        self.assertEqual(len(tender_with_sectors.sectors_list()), 2)  # only sectors with groups are displayed
        self.assertEqual(tender_with_sectors.sectors_list()[0], sector_2.name)  # Autre at the end
        self.assertEqual(tender_with_sectors.sectors_list_string(), "Un secteur, Autre")

    def test_perimeters_list(self):
        tender_whithout_perimeters = TenderFactory()
        self.assertEqual(len(tender_whithout_perimeters.perimeters_list()), 0)
        self.assertEqual(tender_whithout_perimeters.perimeters_list_string, "")
        tender_with_perimeters = TenderFactory(
            title="Besoin 3", perimeters=[self.grenoble_perimeter, self.chamrousse_perimeter]
        )
        self.assertEqual(len(tender_with_perimeters.perimeters_list()), 2)
        self.assertEqual(tender_with_perimeters.perimeters_list()[0], self.grenoble_perimeter.name)
        self.assertEqual(tender_with_perimeters.perimeters_list_string, "Grenoble, Chamrousse")

    def test_location_display(self):
        tender_country_area = TenderFactory(title="Besoin 1", is_country_area=True)
        self.assertEqual(tender_country_area.location_display, "France entière")
        tender_location = TenderFactory(title="Besoin 2", location=self.grenoble_perimeter)
        self.assertTrue("Grenoble" in tender_location.location_display)
        tender_with_perimeters = TenderFactory(
            title="Besoin 3", perimeters=[self.grenoble_perimeter, self.chamrousse_perimeter]
        )
        self.assertTrue("Grenoble" in tender_with_perimeters.location_display)
        self.assertTrue("Chamrousse" in tender_with_perimeters.location_display)

    def test_questions_list(self):
        tender_without_questions = TenderFactory()
        self.assertEqual(len(tender_without_questions.questions_list()), 0)
        tender_with_questions = TenderFactory()
        tender_question_1 = TenderQuestionFactory(tender=tender_with_questions)
        TenderQuestionFactory(tender=tender_with_questions)
        self.assertEqual(len(tender_with_questions.questions_list()), 2)
        self.assertEqual(tender_with_questions.questions_list()[0].get("text"), tender_question_1.text)


class TenderModelSaveTest(TestCase):
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

    # def test_not_empty_deadline(self):
    #     tender = TenderFactory()
    #     tender.deadline_date = None
    #     self.assertRaises(IntegrityError, tender.save)


class TenderModelQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.grenoble_perimeter = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
            # coords=Point(5.7301, 45.1825),
        )
        cls.chamrousse_perimeter = PerimeterFactory(
            name="Chamrousse",
            kind=Perimeter.KIND_CITY,
            insee_code="38567",
            department_code="38",
            region_code="84",
            post_codes=["38410"],
            # coords=Point(5.8862, 45.1106),
        )

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
        TenderFactory(perimeters=[auvergne_rhone_alpes_perimeter])
        TenderFactory(perimeters=[isere_perimeter])
        TenderFactory(perimeters=[self.grenoble_perimeter])
        TenderFactory(perimeters=[self.chamrousse_perimeter])
        TenderFactory(perimeters=[self.grenoble_perimeter, self.chamrousse_perimeter])
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


class TenderModelQuerysetOrderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tender_1 = TenderFactory(deadline_date=date_next_week)
        cls.tender_2 = TenderFactory(deadline_date=date_tomorrow)
        cls.tender_3 = TenderFactory(deadline_date=date_last_week)

    def test_default_order(self):
        tender_queryset = Tender.objects.all()
        self.assertEqual(tender_queryset.count(), 3)
        self.assertEqual(tender_queryset.first().id, self.tender_3.id)

    def test_order_by_deadline_date_queryset(self):
        tender_queryset = Tender.objects.order_by_deadline_date()
        self.assertEqual(tender_queryset.count(), 3)
        self.assertEqual(tender_queryset.first().id, self.tender_2.id)
        self.assertEqual(tender_queryset.last().id, self.tender_3.id)


class TenderModelQuerysetStatsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_tender_1 = SiaeFactory(users=[cls.user_siae])
        siae_with_tender_2 = SiaeFactory(users=[cls.user_siae])
        siae_with_tender_3 = SiaeFactory(users=[cls.user_siae])
        siae_with_tender_4 = SiaeFactory()
        siae_with_tender_5 = SiaeFactory()
        siae_with_tender_6 = SiaeFactory()
        cls.siae_without_tender = SiaeFactory()
        cls.tender_with_siae_1 = TenderFactory(
            siaes=[cls.siae_with_tender_1, siae_with_tender_2], deadline_date=date_tomorrow
        )
        TenderSiae.objects.create(
            tender=cls.tender_with_siae_1, siae=siae_with_tender_3, email_send_date=timezone.now()
        )
        TenderSiae.objects.create(
            tender=cls.tender_with_siae_1,
            siae=siae_with_tender_4,
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
        )
        TenderSiae.objects.create(
            tender=cls.tender_with_siae_1,
            siae=siae_with_tender_5,
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
        )
        TenderSiae.objects.create(
            tender=cls.tender_with_siae_1,
            siae=siae_with_tender_6,
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
            detail_contact_click_date=timezone.now(),
        )
        cls.tender_with_siae_2 = TenderFactory()
        TenderSiae.objects.create(
            tender=cls.tender_with_siae_2,
            siae=cls.siae_with_tender_1,
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
            detail_contact_click_date=timezone.now(),
        )
        cls.tender_without_siae = TenderFactory(deadline_date=date_tomorrow)
        TenderQuestionFactory(tender=cls.tender_with_siae_1)
        TenderQuestionFactory(tender=cls.tender_with_siae_1)

    def test_filter_with_siaes_queryset(self):
        self.tender_with_siae_2.validated_at = None
        self.tender_with_siae_2.save()
        # tender_with_siae_2 is not validated
        self.assertEqual(Tender.objects.filter_with_siaes(self.user_siae.siaes.all()).count(), 1)

    def test_with_siae_stats_queryset(self):
        self.assertEqual(Tender.objects.count(), 2 + 1)
        tender_with_siae_1 = Tender.objects.with_siae_stats().filter(id=self.tender_with_siae_1.id).first()
        self.assertEqual(tender_with_siae_1.siaes.count(), 6)
        self.assertEqual(tender_with_siae_1.siae_count, 6)
        self.assertEqual(tender_with_siae_1.siae_email_send_count, 4)
        self.assertEqual(tender_with_siae_1.siae_email_link_click_count, 3)
        self.assertEqual(tender_with_siae_1.siae_detail_display_count, 2)
        self.assertEqual(tender_with_siae_1.siae_detail_contact_click_count, 1)
        self.assertEqual(tender_with_siae_1.siae_detail_contact_click_since_last_seen_date_count, 1)
        tender_with_siae_2 = Tender.objects.with_siae_stats().filter(id=self.tender_with_siae_2.id).first()
        self.assertEqual(tender_with_siae_2.siaes.count(), 1)
        self.assertEqual(tender_with_siae_2.siae_count, 1)
        self.assertEqual(tender_with_siae_2.siae_email_send_count, 1)
        self.assertEqual(tender_with_siae_2.siae_detail_display_count, 1)
        self.assertEqual(tender_with_siae_2.siae_detail_contact_click_count, 1)
        self.assertEqual(tender_with_siae_2.siae_detail_contact_click_since_last_seen_date_count, 1)
        tender_without_siae = Tender.objects.with_siae_stats().filter(id=self.tender_without_siae.id).first()
        self.assertEqual(tender_without_siae.siaes.count(), 0)
        self.assertEqual(tender_without_siae.siae_count, 0)
        self.assertEqual(tender_without_siae.siae_email_send_count, 0)
        self.assertEqual(tender_without_siae.siae_detail_display_count, 0)
        self.assertEqual(tender_without_siae.siae_detail_contact_click_count, 0)
        self.assertEqual(tender_without_siae.siae_detail_contact_click_since_last_seen_date_count, 0)

    def test_siae_with_tender_stats_queryset(self):
        self.assertEqual(Siae.objects.count(), 6 + 1)
        siae_with_tender_1 = Siae.objects.with_tender_stats().filter(id=self.siae_with_tender_1.id).first()
        # self.assertEqual(siae_with_tender_1.tenders.count(), 2)
        self.assertEqual(siae_with_tender_1.tender_count, 2)
        self.assertEqual(siae_with_tender_1.tender_email_send_count, 1)
        self.assertEqual(siae_with_tender_1.tender_detail_display_count, 1)
        self.assertEqual(siae_with_tender_1.tender_detail_contact_click_count, 1)
        siae_without_tender = Siae.objects.with_tender_stats().filter(id=self.siae_without_tender.id).first()
        self.assertEqual(siae_without_tender.tenders.count(), 0)
        self.assertEqual(siae_without_tender.tender_count, 0)
        self.assertEqual(siae_without_tender.tender_email_send_count, 0)
        self.assertEqual(siae_without_tender.tender_detail_display_count, 0)
        self.assertEqual(siae_without_tender.tender_detail_contact_click_count, 0)

    def test_with_question_stats(self):
        self.assertEqual(TenderQuestion.objects.count(), 2)
        tender_with_siae_1 = Tender.objects.with_question_stats().filter(id=self.tender_with_siae_1.id).first()
        self.assertEqual(tender_with_siae_1.questions.count(), 2)
        self.assertEqual(tender_with_siae_1.question_count, 2)

    def test_with_deadline_date_is_outdated_queryset(self):
        TenderFactory(deadline_date=date_last_week)
        tender_queryset = Tender.objects.with_deadline_date_is_outdated()
        tender_3 = tender_queryset.first()  # order by -created_at
        self.assertTrue(tender_3.deadline_date_is_outdated)
        tender_with_siae_1 = tender_queryset.last()
        self.assertEqual(tender_with_siae_1.id, self.tender_with_siae_1.id)
        self.assertFalse(tender_with_siae_1.deadline_date_is_outdated)

    # doesn't work when chaining these 2 querysets: adds duplicates...
    # def test_chain_querysets(self):
    #     tender_with_siae_1 = (
    #         Tender.objects.with_question_stats().with_siae_stats().filter(id=self.tender_with_siae_1.id).first()
    #     )
    #     self.assertEqual(tender_with_siae_1.siaes.count(), 6)
    #     self.assertEqual(tender_with_siae_1.siae_count, 6)
    #     self.assertEqual(tender_with_siae_1.siae_email_send_count, 4)
    #     self.assertEqual(tender_with_siae_1.siae_email_link_click_count, 3)
    #     self.assertEqual(tender_with_siae_1.siae_detail_display_count, 2)
    #     self.assertEqual(tender_with_siae_1.siae_detail_contact_click_count, 1)
    #     self.assertEqual(tender_with_siae_1.siae_detail_contact_click_since_last_seen_date_count, 1)


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


class TenderQuestionModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tender = TenderFactory()

    def test_str(self):
        str_test = "Quelle est la taille de votre entreprise ?"
        tender_question = TenderQuestionFactory(text=str_test, tender=self.tender)
        self.assertEqual(str(tender_question), str_test)


class TenderPartnerMatchingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # perimeters
        cls.auvergne_rhone_alpes_perimeter = PerimeterFactory(
            name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84"
        )
        cls.isere_perimeter = PerimeterFactory(
            name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84"
        )
        cls.rhone_perimeter = PerimeterFactory(
            name="Rhône", kind=Perimeter.KIND_DEPARTMENT, insee_code="69", region_code="84"
        )
        cls.grenoble_perimeter = PerimeterFactory(
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
        PartnerShareTenderFactory(perimeters=[cls.auvergne_rhone_alpes_perimeter])
        PartnerShareTenderFactory(perimeters=[cls.isere_perimeter])
        PartnerShareTenderFactory(perimeters=[cls.grenoble_perimeter])
        PartnerShareTenderFactory(perimeters=[], amount_in=tender_constants.AMOUNT_RANGE_0_1)
        PartnerShareTenderFactory(perimeters=[], amount_in=tender_constants.AMOUNT_RANGE_10_15)
        PartnerShareTenderFactory(perimeters=[], amount_in=tender_constants.AMOUNT_RANGE_100_150)
        PartnerShareTenderFactory(
            perimeters=[cls.isere_perimeter, cls.rhone_perimeter], amount_in=tender_constants.AMOUNT_RANGE_10_15
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


class TenderSiaeModelQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_tender_1 = SiaeFactory(users=[cls.user_siae])
        siae_with_tender_2 = SiaeFactory(users=[cls.user_siae])
        siae_with_tender_3 = SiaeFactory(users=[cls.user_siae])
        siae_with_tender_4 = SiaeFactory()
        siae_with_tender_5 = SiaeFactory()
        cls.siae_without_tender = SiaeFactory()
        cls.tender_with_siae_1 = TenderFactory(
            siaes=[cls.siae_with_tender_1, siae_with_tender_2], deadline_date=date_tomorrow
        )
        TenderSiae.objects.create(
            tender=cls.tender_with_siae_1, siae=siae_with_tender_3, email_send_date=date_last_week
        )
        TenderSiae.objects.create(
            tender=cls.tender_with_siae_1, siae=siae_with_tender_4, email_send_date=date_two_days_ago
        )
        TenderSiae.objects.create(
            tender=cls.tender_with_siae_1,
            siae=siae_with_tender_5,
            email_send_date=date_two_days_ago,
            email_link_click_date=date_two_days_ago,
            detail_contact_click_date=date_two_days_ago,
        )
        TenderSiae.objects.create(
            tender=cls.tender_with_siae_1,
            siae=siae_with_tender_5,
            detail_display_date=date_last_week,
            detail_contact_click_date=date_last_week,
        )
        cls.tender_with_siae_2 = TenderFactory(
            siaes=[siae_with_tender_2, siae_with_tender_3], deadline_date=date_tomorrow
        )

    def test_email_click_reminder_queryset(self):
        lt_days_ago = timezone.now() - timedelta(days=2)
        gte_days_ago = timezone.now() - timedelta(days=2 + 1)
        self.assertEqual(TenderSiae.objects.count(), 2 + 2 + 4)
        self.assertEqual(
            TenderSiae.objects.email_click_reminder(lt_days_ago=lt_days_ago, gte_days_ago=gte_days_ago).count(), 1
        )

    def test_detail_contact_click_post_reminder_queryset(self):
        lt_days_ago = timezone.now() - timedelta(days=2)
        gte_days_ago = timezone.now() - timedelta(days=2 + 1)
        self.assertEqual(TenderSiae.objects.count(), 2 + 2 + 4)
        self.assertEqual(
            TenderSiae.objects.detail_contact_click_post_reminder(
                lt_days_ago=lt_days_ago, gte_days_ago=gte_days_ago
            ).count(),
            1,
        )


class TenderAdminTest(TestCase):
    def setUp(cls):
        cls.factory = RequestFactory()
        cls.site = MarcheAdminSite()
        cls.admin = TenderAdmin(Tender, cls.site)
        cls.user = User.objects.create_superuser(email="admin@example.com", password="admin")
        cls.sectors = [SectorFactory() for i in range(10)]
        cls.perimeter_paris = PerimeterFactory(department_code="75", post_codes=["75019", "75018"])
        cls.perimeter_marseille = PerimeterFactory(coords=Point(43.35101634452076, 5.379616625955892))
        cls.perimeters = [cls.perimeter_paris, PerimeterFactory()]
        # by default is Paris
        coords_paris = Point(48.86385199985207, 2.337071483848432)

        siae_one = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            coords=coords_paris,
            geo_range_custom_distance=100,
        )
        siae_two = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_ESAT,
            presta_type=[siae_constants.PRESTA_BUILD],
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            coords=coords_paris,
            geo_range_custom_distance=10,
        )
        for i in range(5):
            siae_one.sectors.add(cls.sectors[i])
            siae_two.sectors.add(cls.sectors[i + 5])

        cls.tender = TenderFactory(
            sectors=cls.sectors[6:8],
            perimeters=[cls.perimeter_paris],
            status=tender_constants.STATUS_PUBLISHED,
            published_at=timezone.now(),
        )
        cls.form_data = model_to_dict(cls.tender) | {
            "_continue": "Enregistrer et continuer les modifications",
            "amount": "",
            "why_amount_is_blank": "DONT_WANT_TO_SHARE",
            "location": cls.perimeter_paris.pk,
            "perimeters": [cls.perimeter_paris.pk],
            "sectors": [sector.id for sector in cls.sectors[1:8]],
            "questions-INITIAL_FORMS": "0",
            "questions-__prefix__-id": "",
            "initial-response_kind": "TEL",
            "questions-MIN_NUM_FORMS": "0",
            "questions-MAX_NUM_FORMS": "1000",
            "initial-presta_type": "BUILD",
            "questions-TOTAL_FORMS": "0",
            "questions-__prefix__-text": "",
            "questions-__prefix__-tender": cls.tender.pk,
        }
        for key, value in cls.form_data.items():
            if value is None:
                cls.form_data[key] = ""

    def test_edit_form_matching_on_submission(self):
        self.client.force_login(self.user)
        tender_update_post_url = get_admin_change_view_url(self.tender)
        self.assertEqual(self.tender.tendersiae_set.count(), 0)
        # create post request to update the model
        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "title": "New title",
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance
        self.assertEqual(tender_response.id, self.tender.id)
        self.assertEqual(hasattr(tender_response, "siae_count"), True)
        self.assertEqual(tender_response.siae_count, 2)
        self.assertEqual(tender_response.siae_count, self.tender.tendersiae_set.count())
        # update sectors to have only one match for siaes
        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "title": "New title",
                "sectors": [sector.id for sector in self.sectors[1:3]],
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance
        self.assertEqual(tender_response.siae_count, 1)
        tender_siae_matched = tender_response.tendersiae_set.first()  # only one siae
        # update for another sectors and check if siaes are not the same
        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "sectors": [sector.id for sector in self.sectors[7:8]],
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance
        self.assertEqual(tender_response.siae_count, 1)
        tender_siae_matched_2 = tender_response.tendersiae_set.first()  # only one siae
        self.assertNotEqual(tender_siae_matched.pk, tender_siae_matched_2.pk)
