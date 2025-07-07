from datetime import timedelta
from importlib import import_module
from random import randint
from unittest.mock import patch

from django.apps import apps
from django.contrib.gis.geos import Point
from django.contrib.messages import get_messages
from django.forms.models import model_to_dict
from django.test import RequestFactory, TestCase, TransactionTestCase
from django.utils import timezone

from lemarche.networks.factories import NetworkFactory
from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory, SectorGroupFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeActivityFactory, SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.admin import TenderAdmin
from lemarche.tenders.factories import PartnerShareTenderFactory, TenderFactory, TenderQuestionFactory
from lemarche.tenders.models import PartnerShareTender, Tender, TenderQuestion, TenderSiae
from lemarche.tenders.utils import find_amount_ranges
from lemarche.users.factories import UserFactory
from lemarche.users.models import User
from lemarche.utils.admin.admin_site import MarcheAdminSite, get_admin_change_view_url
from lemarche.www.tenders import utils as tender_utils


date_today = timezone.now()
date_tomorrow = date_today + timedelta(days=1)
date_next_week = date_today + timedelta(days=7)
date_two_days_ago = date_today - timedelta(days=2)
date_last_week = date_today - timedelta(days=7)
date_last_month = date_today - timedelta(days=30)


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

    def test_sectors_list_property(self):
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

    def test_perimeters_list_property(self):
        tender_whithout_perimeters = TenderFactory()
        self.assertEqual(len(tender_whithout_perimeters.perimeters_list()), 0)
        self.assertEqual(tender_whithout_perimeters.perimeters_list_string, "")
        tender_with_perimeters = TenderFactory(
            title="Besoin 3", perimeters=[self.grenoble_perimeter, self.chamrousse_perimeter]
        )
        self.assertEqual(len(tender_with_perimeters.perimeters_list()), 2)
        self.assertEqual(
            tender_with_perimeters.perimeters_list(), [self.chamrousse_perimeter.name, self.grenoble_perimeter.name]
        )
        self.assertEqual(tender_with_perimeters.perimeters_list_string, "Chamrousse, Grenoble")

    def test_location_display_property(self):
        tender_country_area = TenderFactory(title="Besoin 1", is_country_area=True)
        self.assertEqual(tender_country_area.location_display, "France entière")
        tender_location = TenderFactory(title="Besoin 2", location=self.grenoble_perimeter)
        self.assertTrue("Grenoble" in tender_location.location_display)
        tender_with_perimeters = TenderFactory(
            title="Besoin 3", perimeters=[self.grenoble_perimeter, self.chamrousse_perimeter]
        )
        self.assertTrue("Grenoble" in tender_with_perimeters.location_display)
        self.assertTrue("Chamrousse" in tender_with_perimeters.location_display)

    def test_questions_list_property(self):
        tender_without_questions = TenderFactory()
        self.assertEqual(len(tender_without_questions.questions_list()), 0)
        tender_with_questions = TenderFactory()
        tender_question_1 = TenderQuestionFactory(tender=tender_with_questions)
        TenderQuestionFactory(tender=tender_with_questions)
        self.assertEqual(len(tender_with_questions.questions_list()), 2)
        self.assertEqual(tender_with_questions.questions_list()[0].get("text"), tender_question_1.text)

    def test_deadline_date_outdated_property(self):
        tender_without_deadline_date = TenderFactory(deadline_date=None)
        tender_not_outdated = TenderFactory(deadline_date=date_next_week.date())
        tender_outdated = TenderFactory(deadline_date=date_last_week.date())
        self.assertFalse(tender_without_deadline_date.deadline_date_outdated)
        self.assertFalse(tender_not_outdated.deadline_date_outdated)
        self.assertTrue(tender_outdated.deadline_date_outdated)

    def test_start_working_date_outdated(self):
        tender_without_start_working_date = TenderFactory(start_working_date=None)
        tender_not_outdated = TenderFactory(start_working_date=date_next_week.date())
        tender_outdated = TenderFactory(start_working_date=date_last_week.date())
        self.assertFalse(tender_without_start_working_date.start_working_date_outdated)
        self.assertFalse(tender_not_outdated.start_working_date_outdated)
        self.assertTrue(tender_outdated.start_working_date_outdated)

    def test_status_property(self):
        tender_draft = TenderFactory(status=Tender.StatusChoices.STATUS_DRAFT)
        tender_pending_validation = TenderFactory(status=Tender.StatusChoices.STATUS_SUBMITTED)
        tender_validated_half = TenderFactory(status=Tender.StatusChoices.STATUS_VALIDATED)
        tender_validated_full = TenderFactory(
            status=Tender.StatusChoices.STATUS_VALIDATED, validated_at=timezone.now()
        )
        tender_sent = TenderFactory(status=Tender.StatusChoices.STATUS_SENT, first_sent_at=timezone.now())
        self.assertTrue(tender_draft.is_draft)
        self.assertTrue(tender_pending_validation.is_pending_validation)
        self.assertTrue(tender_validated_half.is_validated)
        self.assertTrue(tender_validated_full.is_validated)
        self.assertTrue(tender_sent.is_sent)

    def test_amount_display_property(self):
        tender_with_amount = TenderFactory(amount=tender_constants.AMOUNT_RANGE_0_1, accept_share_amount=True)
        tender_with_amount_2 = TenderFactory(amount=tender_constants.AMOUNT_RANGE_10_15, accept_share_amount=True)
        tender_with_amount_exact = TenderFactory(
            amount=tender_constants.AMOUNT_RANGE_10_15, amount_exact=10000, accept_share_amount=True
        )
        tender_dont_share_amount = TenderFactory(
            amount=tender_constants.AMOUNT_RANGE_10_15, amount_exact=10000, accept_share_amount=False
        )
        tender_no_amount = TenderFactory(amount=None, amount_exact=None, accept_share_amount=True)
        self.assertEqual(tender_with_amount.amount_display, "0-1000 €")
        self.assertEqual(tender_with_amount_2.amount_display, "10-15 K€")
        self.assertEqual(tender_with_amount_exact.amount_display, "10000 €")
        self.assertEqual(tender_dont_share_amount.amount_display, "Non renseigné")
        self.assertEqual(tender_no_amount.amount_display, "Non renseigné")


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


class TenderModelMatchingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector = SectorFactory()

        # siae found by presta_type
        cls.siae_one = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
        )
        SiaeActivityFactory(
            siae=cls.siae_one,
            sector=cls.sector,
            presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
            with_country_perimeter=True,
        )

        # siae found by presta_type
        cls.siae_two = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_ESAT,
        )
        SiaeActivityFactory(
            siae=cls.siae_two,
            sector=cls.sector,
            presta_type=[siae_constants.PRESTA_BUILD],
            with_country_perimeter=True,
        )

        # siae not found
        cls.siae_five = SiaeFactory()

    def test_set_siae_found_list(self):
        tender = TenderFactory(
            presta_type=[siae_constants.PRESTA_BUILD],
            sectors=[self.sector],
            is_country_area=True,
            validated_at=None,
        )

        siaes_found = Siae.objects.filter_with_tender_through_activities(tender)
        tender.set_siae_found_list()
        tender.refresh_from_db()
        self.assertEqual(list(siaes_found), list(tender.siaes.all()))


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

    def test_by_user(self):
        user = UserFactory()
        TenderFactory(author=user)
        TenderFactory()
        self.assertEqual(Tender.objects.by_user(user).count(), 1)

    def test_validated(self):
        TenderFactory(validated_at=timezone.now())
        TenderFactory(validated_at=None)
        self.assertEqual(Tender.objects.validated().count(), 1)

    def test_sent(self):
        TenderFactory(first_sent_at=timezone.now())
        TenderFactory(first_sent_at=None)
        self.assertEqual(Tender.objects.sent().count(), 1)

    def test_validated_but_not_sent(self):
        siae = SiaeFactory()
        TenderFactory(
            siaes=[siae], status=Tender.StatusChoices.STATUS_SUBMITTED, validated_at=None, first_sent_at=None
        )
        TenderFactory(
            siaes=[siae], status=Tender.StatusChoices.STATUS_VALIDATED, validated_at=timezone.now(), first_sent_at=None
        )
        TenderFactory(
            siaes=[siae],
            status=Tender.StatusChoices.STATUS_SENT,
            validated_at=timezone.now(),
            first_sent_at=timezone.now(),
        )
        self.assertEqual(Tender.objects.validated_but_not_sent().count(), 1)

    def test_validated_sent_batch(self):
        one_hour_ago = timezone.now() - timedelta(hours=1)
        two_days_ago = timezone.now() - timedelta(days=1)
        siae = SiaeFactory()
        TenderFactory(
            siaes=[siae],
            version=1,
            status=Tender.StatusChoices.STATUS_SUBMITTED,
            validated_at=None,
            first_sent_at=None,
            last_sent_at=None,
            send_to_commercial_partners_only=False,
        )
        TenderFactory(
            siaes=[siae],
            version=1,
            status=Tender.StatusChoices.STATUS_VALIDATED,
            validated_at=timezone.now(),
            first_sent_at=None,
            last_sent_at=None,
            send_to_commercial_partners_only=False,
        )
        TenderFactory(
            siaes=[siae],
            version=1,
            status=Tender.StatusChoices.STATUS_SENT,
            validated_at=timezone.now(),
            first_sent_at=timezone.now(),
            last_sent_at=timezone.now(),
            send_to_commercial_partners_only=False,
        )
        TenderFactory(
            siaes=[siae],
            version=1,
            status=Tender.StatusChoices.STATUS_SENT,
            validated_at=one_hour_ago,
            first_sent_at=one_hour_ago,
            last_sent_at=one_hour_ago,
            send_to_commercial_partners_only=False,
        )
        # This tender would be sent if send_to_commercial_partners_only was False
        TenderFactory(
            siaes=[siae],
            version=1,
            status=Tender.StatusChoices.STATUS_SENT,
            validated_at=two_days_ago,
            first_sent_at=two_days_ago,
            last_sent_at=two_days_ago,
            send_to_commercial_partners_only=True,
        )
        self.assertEqual(Tender.objects.validated_sent_batch().count(), 0)

    def test_is_not_outdated(self):
        TenderFactory(deadline_date=None)
        TenderFactory(deadline_date=timezone.now() + timedelta(days=1))
        TenderFactory(deadline_date=timezone.now() - timedelta(days=1))
        # TenderFactory(deadline_date=None)  # cannot be None
        self.assertEqual(Tender.objects.is_not_outdated().count(), 1 + 1)

    def test_is_live(self):
        TenderFactory(deadline_date=timezone.now() + timedelta(days=1))
        TenderFactory(
            deadline_date=timezone.now() + timedelta(days=1),
            first_sent_at=None,
            status=Tender.StatusChoices.STATUS_DRAFT,
        )
        TenderFactory(deadline_date=timezone.now() - timedelta(days=1))
        # TenderFactory(deadline_date=None)  # cannot be None
        self.assertEqual(Tender.objects.is_live().count(), 1)

    def test_has_amount(self):
        TenderFactory()
        TenderFactory(amount=tender_constants.AMOUNT_RANGE_0_1)
        TenderFactory(amount_exact=1000)
        TenderFactory(amount=tender_constants.AMOUNT_RANGE_0_1, amount_exact=1000)
        self.assertEqual(Tender.objects.count(), 4)
        self.assertEqual(Tender.objects.has_amount().count(), 3)
        self.assertEqual(Tender.objects.filter(amount__isnull=True, amount_exact__isnull=True).count(), 1)

    def test_in_sectors(self):
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

    def test_in_perimeters(self):
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

    def test_filter_by_amount_exact(self):
        TenderFactory(amount_exact=1000)
        TenderFactory(amount_exact=5000)
        TenderFactory(amount_exact=7500)
        TenderFactory(amount_exact=10000)
        TenderFactory(amount_exact=100000)
        tender_qs = Tender.objects.has_amount()
        self.assertEqual(tender_qs.filter_by_amount_exact(1000, operation="lt").count(), 0)
        self.assertEqual(tender_qs.filter_by_amount_exact(1000, operation="gte").count(), 5)
        self.assertEqual(tender_qs.filter_by_amount_exact(100000, operation="gt").count(), 0)
        self.assertEqual(tender_qs.filter_by_amount_exact(100000, operation="lte").count(), 5)
        self.assertEqual(
            tender_qs.filter_by_amount_exact(10000, operation="lte")
            .filter_by_amount_exact(5000, operation="gte")
            .count(),
            3,
        )
        self.assertEqual(
            tender_qs.filter_by_amount_exact(10000, operation="lt")
            .filter_by_amount_exact(5000, operation="gte")
            .count(),
            2,
        )


class TenderModelQuerysetOrderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tender_1 = TenderFactory(deadline_date=date_next_week, published_at=date_today)
        cls.tender_2 = TenderFactory(deadline_date=date_tomorrow, published_at=date_two_days_ago)
        cls.tender_3 = TenderFactory(deadline_date=date_last_week, published_at=date_last_month)

    def test_default_order(self):
        tender_queryset = Tender.objects.all()
        self.assertEqual(tender_queryset.count(), 3)
        self.assertEqual(tender_queryset.first().id, self.tender_3.id)

    def test_order_by_last_published(self):
        tender_queryset = Tender.objects.order_by_last_published()
        self.assertEqual(tender_queryset.count(), 3)
        self.assertEqual(tender_queryset.first().id, self.tender_1.id)
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
        siae_with_tender_7 = SiaeFactory()
        siae_with_tender_8 = SiaeFactory()
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
        TenderSiae.objects.create(
            tender=cls.tender_with_siae_1,
            siae=siae_with_tender_7,
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
        )
        TenderSiae.objects.create(
            tender=cls.tender_with_siae_1,
            siae=siae_with_tender_8,
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
            detail_not_interested_click_date=timezone.now(),
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

    def test_filter_with_siaes(self):
        self.tender_with_siae_2.first_sent_at = None
        self.tender_with_siae_2.save()
        # tender_with_siae_2 is not sent
        self.assertEqual(Tender.objects.filter_with_siaes(self.user_siae.siaes.all()).count(), 1)

    def test_with_siae_stats(self):
        self.assertEqual(Tender.objects.count(), 2 + 1)
        tender_with_siae_1 = Tender.objects.with_siae_stats().filter(id=self.tender_with_siae_1.id).first()
        self.assertEqual(tender_with_siae_1.siaes.count(), 8)
        self.assertEqual(tender_with_siae_1.siae_count_annotated, 8)
        self.assertEqual(tender_with_siae_1.siae_email_send_count_annotated, 6)
        self.assertEqual(tender_with_siae_1.siae_email_link_click_count_annotated, 5)
        self.assertEqual(tender_with_siae_1.siae_detail_display_count_annotated, 4)
        self.assertEqual(tender_with_siae_1.siae_email_link_click_or_detail_display_count_annotated, 5)
        self.assertEqual(tender_with_siae_1.siae_detail_contact_click_count_annotated, 1)
        self.assertEqual(tender_with_siae_1.siae_detail_not_interested_click_count_annotated, 1)
        self.assertEqual(tender_with_siae_1.siae_detail_contact_click_since_last_seen_date_count_annotated, 1)
        tender_with_siae_2 = Tender.objects.with_siae_stats().filter(id=self.tender_with_siae_2.id).first()
        self.assertEqual(tender_with_siae_2.siaes.count(), 1)
        self.assertEqual(tender_with_siae_2.siae_count_annotated, 1)
        self.assertEqual(tender_with_siae_2.siae_email_send_count_annotated, 1)
        self.assertEqual(tender_with_siae_2.siae_detail_display_count_annotated, 1)
        self.assertEqual(tender_with_siae_2.siae_email_link_click_or_detail_display_count_annotated, 1)
        self.assertEqual(tender_with_siae_2.siae_detail_contact_click_count_annotated, 1)
        self.assertEqual(tender_with_siae_2.siae_detail_contact_click_since_last_seen_date_count_annotated, 1)
        tender_without_siae = Tender.objects.with_siae_stats().filter(id=self.tender_without_siae.id).first()
        self.assertEqual(tender_without_siae.siaes.count(), 0)
        self.assertEqual(tender_without_siae.siae_count_annotated, 0)
        self.assertEqual(tender_without_siae.siae_email_send_count_annotated, 0)
        self.assertEqual(tender_without_siae.siae_detail_display_count_annotated, 0)
        self.assertEqual(tender_without_siae.siae_email_link_click_or_detail_display_count_annotated, 0)
        self.assertEqual(tender_without_siae.siae_detail_contact_click_count_annotated, 0)
        self.assertEqual(tender_without_siae.siae_detail_contact_click_since_last_seen_date_count_annotated, 0)

    def test_siae_with_tender_stats(self):
        self.assertEqual(Siae.objects.count(), 8 + 1)
        siae_with_tender_1 = Siae.objects.with_tender_stats().filter(id=self.siae_with_tender_1.id).first()
        # self.assertEqual(siae_with_tender_1.tenders.count(), 2)
        self.assertEqual(siae_with_tender_1.tender_count_annotated, 2)
        self.assertEqual(siae_with_tender_1.tender_email_send_count_annotated, 1)
        self.assertEqual(siae_with_tender_1.tender_detail_display_count_annotated, 1)
        self.assertEqual(siae_with_tender_1.tender_detail_contact_click_count_annotated, 1)
        siae_without_tender = Siae.objects.with_tender_stats().filter(id=self.siae_without_tender.id).first()
        self.assertEqual(siae_without_tender.tenders.count(), 0)
        self.assertEqual(siae_without_tender.tender_count_annotated, 0)
        self.assertEqual(siae_without_tender.tender_email_send_count_annotated, 0)
        self.assertEqual(siae_without_tender.tender_detail_display_count_annotated, 0)
        self.assertEqual(siae_without_tender.tender_detail_contact_click_count_annotated, 0)

    def test_with_question_stats(self):
        self.assertEqual(TenderQuestion.objects.count(), 2)
        tender_with_siae_1 = Tender.objects.with_question_stats().filter(id=self.tender_with_siae_1.id).first()
        self.assertEqual(tender_with_siae_1.questions.count(), 2)
        self.assertEqual(tender_with_siae_1.question_count_annotated, 2)

    def test_with_deadline_date_is_outdated(self):
        TenderFactory(deadline_date=date_last_week)
        tender_queryset = Tender.objects.with_deadline_date_is_outdated()
        tender_3 = tender_queryset.first()  # order by -created_at
        self.assertTrue(tender_3.deadline_date_is_outdated_annotated)
        tender_with_siae_1 = tender_queryset.last()
        self.assertEqual(tender_with_siae_1.id, self.tender_with_siae_1.id)
        self.assertFalse(tender_with_siae_1.deadline_date_is_outdated_annotated)

    def test_with_network_siae_stats(self):
        network_with_siaes = NetworkFactory(siaes=[self.siae_with_tender_1, self.siae_without_tender])
        tender_with_siae_2 = (
            Tender.objects.with_network_siae_stats(network_with_siaes.siaes.all())
            .filter(id=self.tender_with_siae_2.id)
            .first()
        )
        self.assertEqual(tender_with_siae_2.network_siae_email_send_count_annotated, 1)
        self.assertEqual(tender_with_siae_2.network_siae_detail_contact_click_count_annotated, 1)

    # doesn't work when chaining these 2 querysets: adds duplicates...
    # def test_chain_querysets(self):
    #     tender_with_siae_1 = (
    #         Tender.objects.with_question_stats().with_siae_stats().filter(id=self.tender_with_siae_1.id).first()
    #     )
    #     self.assertEqual(tender_with_siae_1.siaes.count(), 6)
    #     self.assertEqual(tender_with_siae_1.siae_count_annotated, 6)
    #     self.assertEqual(tender_with_siae_1.siae_email_send_count_annotated, 4)
    #     self.assertEqual(tender_with_siae_1.siae_email_link_click_count_annotated, 3)
    #     self.assertEqual(tender_with_siae_1.siae_detail_display_count_annotated, 2)
    #     self.assertEqual(tender_with_siae_1.siae_email_link_click_or_detail_display_count_annotated, 2)
    #     self.assertEqual(tender_with_siae_1.siae_detail_contact_click_count_annotated, 1)
    #     self.assertEqual(tender_with_siae_1.siae_detail_contact_click_since_last_seen_date_count_annotated, 1)


class TenderModelQuerysetUnreadStatsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        _ = UserFactory(kind=User.KIND_SIAE)

        siae_with_tender_1 = SiaeFactory(users=[cls.user_siae])
        siae_with_tender_2 = SiaeFactory(users=[cls.user_siae])
        siae_with_tender_3 = SiaeFactory()
        tender_with_siae_1 = TenderFactory(siaes=[siae_with_tender_1, siae_with_tender_2], deadline_date=date_tomorrow)
        TenderSiae.objects.create(tender=tender_with_siae_1, siae=siae_with_tender_3)

        tender_with_siae_2 = TenderFactory()
        TenderSiae.objects.create(
            tender=tender_with_siae_2,
            siae=siae_with_tender_1,
            detail_display_date=timezone.now(),  # the user read it
        )
        _ = TenderFactory(deadline_date=date_tomorrow)
        _ = TenderFactory(siaes=[siae_with_tender_1], deadline_date=date_tomorrow, kind=tender_constants.KIND_QUOTE)
        _ = TenderFactory(siaes=[siae_with_tender_1], deadline_date=date_tomorrow, kind=tender_constants.KIND_TENDER)

    def test_unread_stats(self):
        with self.assertNumQueries(1):
            stats = Tender.objects.unread_stats(user=self.user_siae)
        self.assertEqual(stats[f"unread_count_{tender_constants.KIND_TENDER}_annotated"], 1)
        self.assertEqual(stats[f"unread_count_{tender_constants.KIND_QUOTE}_annotated"], 2)
        self.assertEqual(stats[f"unread_count_{tender_constants.KIND_PROJECT}_annotated"], 0)


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
        PartnerShareTenderFactory(perimeters=[], is_active=True)
        PartnerShareTenderFactory(perimeters=[cls.auvergne_rhone_alpes_perimeter], is_active=True)
        PartnerShareTenderFactory(perimeters=[cls.isere_perimeter], is_active=True)
        PartnerShareTenderFactory(perimeters=[cls.grenoble_perimeter], is_active=True)
        PartnerShareTenderFactory(perimeters=[], amount_in=tender_constants.AMOUNT_RANGE_0_1, is_active=True)
        PartnerShareTenderFactory(perimeters=[], amount_in=tender_constants.AMOUNT_RANGE_10_15, is_active=True)
        PartnerShareTenderFactory(perimeters=[], amount_in=tender_constants.AMOUNT_RANGE_100_150, is_active=True)
        PartnerShareTenderFactory(
            perimeters=[cls.isere_perimeter, cls.rhone_perimeter],
            amount_in=tender_constants.AMOUNT_RANGE_10_15,
            is_active=True,
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

    def test_tender_partner_is_active(self):
        # partners with perimeters=[]
        tender = TenderFactory(is_country_area=True)
        # by default is_active is False
        partner = PartnerShareTenderFactory(perimeters=[])
        result = PartnerShareTender.objects.filter_by_tender(tender)
        self.assertEqual(len(result), 4)
        # update partner
        partner.is_active = True
        partner.save()
        # we should have +1 partner
        result_2 = PartnerShareTender.objects.filter_by_tender(tender)
        self.assertEqual(len(result_2), 4 + 1)


class TenderSiaeModelAndQuerysetTest(TestCase):
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
            siaes=[cls.siae_with_tender_1, siae_with_tender_2],
            deadline_date=date_tomorrow,
            kind=tender_constants.KIND_TENDER,
        )
        cls.tendersiae_1 = TenderSiae.objects.create(
            tender=cls.tender_with_siae_1, siae=siae_with_tender_3, email_send_date=date_last_week
        )
        cls.tendersiae_2 = TenderSiae.objects.create(
            tender=cls.tender_with_siae_1, siae=siae_with_tender_4, email_send_date=date_two_days_ago
        )
        cls.tendersiae_3 = TenderSiae.objects.create(
            tender=cls.tender_with_siae_1,
            siae=siae_with_tender_5,
            email_send_date=date_two_days_ago,
            email_link_click_date=date_two_days_ago,
            detail_contact_click_date=date_two_days_ago,
        )
        cls.tendersiae_4 = TenderSiae.objects.create(
            tender=cls.tender_with_siae_1,
            siae=siae_with_tender_5,
            detail_display_date=date_last_week,
            detail_contact_click_date=date_last_week,
        )
        cls.tender_with_siae_2 = TenderFactory(
            siaes=[siae_with_tender_2, siae_with_tender_3], deadline_date=date_tomorrow
        )

    def test_with_status(self):
        tendersiae_queryset = TenderSiae.objects.with_status()
        self.assertEqual(
            tendersiae_queryset.get(id=self.tendersiae_1.id).status_annotated,
            tender_constants.TENDER_SIAE_STATUS_EMAIL_SEND_DATE,
        )
        self.assertEqual(
            tendersiae_queryset.get(id=self.tendersiae_4.id).status_annotated,
            tender_constants.TENDER_SIAE_STATUS_DETAIL_CONTACT_CLICK_DATE,
        )

    def test_email_click_reminder(self):
        lt_days_ago = timezone.now() - timedelta(days=2)
        gte_days_ago = timezone.now() - timedelta(days=2 + 1)
        self.assertEqual(TenderSiae.objects.count(), 2 + 2 + 4)
        self.assertEqual(
            TenderSiae.objects.email_click_reminder(lt_days_ago=lt_days_ago, gte_days_ago=gte_days_ago).count(), 1
        )

    def test_detail_contact_click_post_reminder(self):
        lt_days_ago = timezone.now() - timedelta(days=2)
        gte_days_ago = timezone.now() - timedelta(days=2 + 1)
        self.assertEqual(TenderSiae.objects.count(), 2 + 2 + 4)
        self.assertEqual(
            TenderSiae.objects.detail_contact_click_post_reminder(
                lt_days_ago=lt_days_ago, gte_days_ago=gte_days_ago
            ).count(),
            1,
        )

    def test_status_property(self):
        self.assertEqual(
            TenderSiae.objects.get(id=self.tendersiae_1.id).status,
            tender_constants.TENDER_SIAE_STATUS_EMAIL_SEND_DATE_DISPLAY,
        )
        self.assertEqual(
            TenderSiae.objects.get(id=self.tendersiae_4.id).status,
            tender_constants.TENDER_SIAE_STATUS_DETAIL_CONTACT_CLICK_DATE_DISPLAY,
        )


class TenderAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.site = MarcheAdminSite()
        cls.admin = TenderAdmin(Tender, cls.site)
        cls.user = User.objects.create_superuser(email="admin@example.com", password="admin")
        cls.sectors = [SectorFactory() for i in range(10)]
        cls.perimeter_paris = PerimeterFactory(department_code="75", post_codes=["75019", "75018"])
        cls.perimeter_marseille = PerimeterFactory(
            name="Marseille", department_code="13", coords=Point(43.35101634452076, 5.379616625955892)
        )
        # by default is Paris
        coords_paris = Point(48.86385199985207, 2.337071483848432)

        siae_one = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_AI,
            coords=coords_paris,
        )

        siae_two = SiaeFactory(
            is_active=True,
            kind=siae_constants.KIND_ESAT,
            coords=coords_paris,
        )

        for i in range(5):
            SiaeActivityFactory(
                siae=siae_one,
                sector=cls.sectors[i],
                presta_type=[siae_constants.PRESTA_PREST, siae_constants.PRESTA_BUILD],
                geo_range=siae_constants.GEO_RANGE_CUSTOM,
                geo_range_custom_distance=100,
            )
            SiaeActivityFactory(
                siae=siae_two,
                sector=cls.sectors[i + 5],
                presta_type=[siae_constants.PRESTA_BUILD],
                geo_range=siae_constants.GEO_RANGE_CUSTOM,
                geo_range_custom_distance=10,
            )

        cls.tender = TenderFactory(
            sectors=cls.sectors[6:8],
            perimeters=[cls.perimeter_paris],
            status=Tender.StatusChoices.STATUS_SUBMITTED,
            published_at=timezone.now(),
            validated_at=None,
        )
        cls.form_data = model_to_dict(cls.tender) | {
            "amount": "",
            "why_amount_is_blank": "DONT_WANT_TO_SHARE",
            "location": cls.perimeter_paris.pk,
            "perimeters": [cls.perimeter_paris.pk],
            "sectors": [sector.id for sector in cls.sectors[1:8]],
            "initial-response_kind": "TEL",
            "initial-presta_type": "BUILD",
            "notes-note-content_type-object_id-TOTAL_FORMS": "0",
            "notes-note-content_type-object_id-INITIAL_FORMS": "0",
            "notes-note-content_type-object_id-MIN_NUM_FORMS": "0",
            "notes-note-content_type-object_id-MAX_NUM_FORMS": "1000",
            "notes-note-content_type-object_id-__prefix__-id": "",
            "notes-note-content_type-object_id-__prefix__-text": "",
            "questions-TOTAL_FORMS": "0",
            "questions-INITIAL_FORMS": "0",
            "questions-MIN_NUM_FORMS": "0",
            "questions-MAX_NUM_FORMS": "1000",
            "questions-__prefix__-id": "",
            "questions-__prefix__-text": "",
            "questions-__prefix__-tender": cls.tender.pk,
            "tendersiae_set-TOTAL_FORMS": "0",
            "tendersiae_set-INITIAL_FORMS": "0",
            "tendersiae_set-MIN_NUM_FORMS": "0",
            "tendersiae_set-MAX_NUM_FORMS": "1000",
            "tendersiae_set-__prefix__-id": "",
            "tendersiae_set-__prefix__-text": "",
            "tendersiae_set-2-TOTAL_FORMS": "0",
            "tendersiae_set-2-INITIAL_FORMS": "0",
            "tendersiae_set-2-MIN_NUM_FORMS": "0",
            "tendersiae_set-2-MAX_NUM_FORMS": "1000",
            "tendersiae_set-2-__prefix__-id": "",
            "tendersiae_set-2-__prefix__-text": "",
            "tendersiae_set-3-TOTAL_FORMS": "0",
            "tendersiae_set-3-INITIAL_FORMS": "0",
            "tendersiae_set-3-MIN_NUM_FORMS": "0",
            "tendersiae_set-3-MAX_NUM_FORMS": "1000",
            "tendersiae_set-3-__prefix__-id": "",
            "tendersiae_set-3-__prefix__-text": "",
            "attachment_one": "",
            "attachment_two": "",
            "attachment_three": "",
        }
        for key, value in cls.form_data.items():
            if value is None:
                cls.form_data[key] = ""

    def test_edit_form_no_matching_on_simple_submission(self):
        self.client.force_login(self.user)
        tender_update_post_url = get_admin_change_view_url(self.tender)
        self.assertEqual(self.tender.tendersiae_set.count(), 0)
        # create post request to update the model
        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "title": "New title",
                "_continue": "Enregistrer et continuer les modifications",
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance
        self.assertEqual(tender_response.id, self.tender.id)
        self.assertTrue(hasattr(tender_response, "siae_count_annotated"))
        self.assertEqual(tender_response.siae_count_annotated, 0)

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
                "_calculate_tender": "Sauvegarder et chercher les structures correspondantes",
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance
        self.assertEqual(tender_response.id, self.tender.id)
        self.assertTrue(hasattr(tender_response, "siae_count_annotated"))
        self.assertEqual(tender_response.siae_count_annotated, 2)
        self.assertEqual(tender_response.siae_count_annotated, self.tender.tendersiae_set.count())
        # update sectors to have only one match for siaes
        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "title": "New title",
                "sectors": [sector.id for sector in self.sectors[1:3]],
                "_calculate_tender": "Sauvegarder et chercher les structures correspondantes",
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance
        self.assertEqual(tender_response.siae_count_annotated, 1)
        tender_siae_matched = tender_response.tendersiae_set.first()  # only one siae
        # update for another sectors and check if siaes are not the same
        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "sectors": [sector.id for sector in self.sectors[7:8]],
                "_calculate_tender": "Sauvegarder et chercher les structures correspondantes",
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance
        self.assertEqual(tender_response.siae_count_annotated, 1)
        tender_siae_matched_2 = tender_response.tendersiae_set.first()  # only one siae
        self.assertNotEqual(tender_siae_matched.pk, tender_siae_matched_2.pk)

    def test_edit_form_no_matching_on_validate_submission(self):
        self.client.force_login(self.user)
        tender_update_post_url = get_admin_change_view_url(self.tender)
        self.assertEqual(self.tender.tendersiae_set.count(), 0)
        # create post request to update the model
        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "title": "New title",
                "_calculate_tender": "Sauvegarder et chercher les structures correspondantes",
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance
        self.assertEqual(tender_response.id, self.tender.id)
        self.assertNotContains(response, "Validé le ")
        self.assertTrue(hasattr(tender_response, "siae_count_annotated"))
        self.assertEqual(tender_response.siae_count_annotated, 2)
        self.assertEqual(tender_response.siae_count_annotated, self.tender.tendersiae_set.count())

        # delete for moderation per example
        TenderSiae.objects.first().delete()
        self.assertEqual(self.tender.tendersiae_set.count(), 1)

        # validation does not match again and keep moderation
        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "title": "New title",
                "_validate_send_to_siaes": "Valider (sauvegarder) et envoyer aux structures",
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance
        self.assertEqual(tender_response.id, self.tender.id)
        self.assertContains(response, "Validé le ")
        self.assertFalse(tender_response.send_to_commercial_partners_only)
        self.assertTrue(hasattr(tender_response, "siae_count_annotated"))
        self.assertEqual(tender_response.siae_count_annotated, 1)
        self.assertEqual(tender_response.siae_count_annotated, self.tender.tendersiae_set.count())

    def test_edit_form_validate_submission_to_commercial_partners(self):
        self.client.force_login(self.user)
        tender_update_post_url = get_admin_change_view_url(self.tender)

        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "title": "New title",
                "_validate_send_to_commercial_partners": "Valider (sauvegarder) et envoyer aux partenaires.",
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance
        self.assertEqual(tender_response.id, self.tender.id)
        self.assertContains(response, "Validé le ")
        self.assertTrue(tender_response.send_to_commercial_partners_only)

    @patch("lemarche.tenders.admin.send_tender_author_modification_request")
    def test_email_sent_for_submitted_status(self, mock_send_email):
        """
        When the admin saves a SUBMITTED tender with the email_sent_for_modification field to True,
        the email is sent to the author and the status of the tender is set to STATUS_DRAFT.
        """
        self.client.force_login(self.user)
        tender_update_post_url = get_admin_change_view_url(self.tender)

        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "title": "New title",
                "_send_modification_request": "Envoyer une demande de modification",
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance
        actions = [log["action"] for log in tender_response.logs]

        mock_send_email.assert_called_once_with(tender=tender_response)
        self.assertTrue(tender_response.email_sent_for_modification)
        self.assertEqual(tender_response.status, Tender.StatusChoices.STATUS_DRAFT)
        self.assertIn("send tender author modification request", actions)

    def test_email_sent_for_modification_updates_status_and_logs(self):
        """Test 'email_sent_for_modification' updates tender status and logs"""
        self.client.force_login(self.user)
        tender_update_post_url = get_admin_change_view_url(self.tender)

        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "title": "New title",
                "_send_modification_request": "Envoyer une demande de modification",
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance

        # Tender status changed from SUBMITTED to DRAFT
        self.assertEqual(tender_response.status, Tender.StatusChoices.STATUS_DRAFT)

        # Tasks 'send_tender_autor_modification_request' logs email sent date
        log_entry = tender_response.logs[0]
        self.assertEqual(log_entry["action"], "send tender author modification request")
        self.assertIn("date", log_entry)

    @patch("lemarche.tenders.admin.send_tender_author_modification_request")
    def test_handle_email_sent_for_modification_failure(self, mock_send_email):
        """
        Test 'handle_email_sent_for_modification_failure' method to check that tender status
        and email_sent_for_modification fields are not updated if an exception is raised when sending the email.
        """
        mock_send_email.side_effect = Exception("Simulated email sending failure")

        self.client.force_login(self.user)
        tender_update_post_url = get_admin_change_view_url(self.tender)

        response = self.client.post(
            tender_update_post_url,
            self.form_data
            | {
                "title": "New title",
                "_send_modification_request": "Envoyer une demande de modification",
            },
            follow=True,
        )
        tender_response = response.context_data["adminform"].form.instance

        actions = [log["action"] for log in tender_response.logs]
        messages = list(get_messages(response.wsgi_request))
        message_texts = [msg.message for msg in messages]

        self.assertEqual(tender_response.status, Tender.StatusChoices.STATUS_SUBMITTED)
        self.assertFalse(tender_response.email_sent_for_modification)
        self.assertNotIn("send tender author modification request", actions)
        self.assertIn(
            "Erreur lors de l'envoi de la demande de modification : veuillez contacter le support.", message_texts
        )
        mock_send_email.assert_called_once_with(tender=tender_response)


class TenderUtilsTest(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER)
        cls.siae_with_tender_1 = SiaeFactory(users=[cls.user_siae])
        siae_with_tender_2 = SiaeFactory(users=[cls.user_siae])
        cls.sector = SectorFactory()
        cls.tender_with_siae = TenderFactory(
            siaes=[cls.siae_with_tender_1, siae_with_tender_2],
            sectors=[cls.sector],
            author=cls.user_buyer,
            deadline_date=date_tomorrow,
            status=Tender.StatusChoices.STATUS_SENT,
            first_sent_at=timezone.now(),
        )

    def test_duplicate(self):
        new_tender = tender_utils.duplicate(self.tender_with_siae)
        self.assertEqual(self.tender_with_siae.title, new_tender.title)
        self.assertEqual(self.tender_with_siae.author, new_tender.author)
        self.assertNotEqual(self.tender_with_siae.status, new_tender.status)
        self.assertEqual(self.tender_with_siae.sectors.count(), new_tender.sectors.count())
        self.assertNotEqual(self.tender_with_siae.siaes.count(), new_tender.siaes.count())
        self.assertNotEqual(self.tender_with_siae.slug, new_tender.slug)


class TenderUtilsFindAmountRangesTests(TestCase):
    def test_gte_operation(self):
        """Test the 'gte' operation."""
        expected_keys = [
            tender_constants.AMOUNT_RANGE_250_500,
            tender_constants.AMOUNT_RANGE_500_750,
            tender_constants.AMOUNT_RANGE_750_1000,
            tender_constants.AMOUNT_RANGE_1000_MORE,
        ]
        self.assertListEqual(find_amount_ranges(250000, "gte"), expected_keys)

    def test_lt_operation(self):
        """Test the 'lt' operation."""
        expected_keys = [
            tender_constants.AMOUNT_RANGE_0_1,
            tender_constants.AMOUNT_RANGE_1_5,
            tender_constants.AMOUNT_RANGE_5_10,
        ]
        self.assertListEqual(find_amount_ranges(10000, "lt"), expected_keys)

    def test_invalid_operation(self):
        """Test using an invalid operation."""
        with self.assertRaises(ValueError):
            find_amount_ranges(5000, "invalid_op")

    def test_edge_case(self):
        """Test an edge case, such as exactly 1M€ for 'gt' operation."""
        expected_keys = [tender_constants.AMOUNT_RANGE_1000_MORE]
        self.assertListEqual(find_amount_ranges(1000000, "gt"), expected_keys)

    def test_no_matching_ranges(self):
        """Test when no ranges match the criteria."""
        expected_keys = [tender_constants.AMOUNT_RANGE_0_1]
        self.assertListEqual(find_amount_ranges(100, "lte"), expected_keys)
