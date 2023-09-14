import json
from datetime import timedelta

from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from sesame.utils import get_query_string as sesame_get_query_string

from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.factories import TenderFactory, TenderQuestionFactory
from lemarche.tenders.models import Tender, TenderSiae
from lemarche.users.factories import UserFactory
from lemarche.users.models import User
from lemarche.www.tenders.views import TenderCreateMultiStepView


class TenderCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER, company_name="Test")
        cls.sectors = [SectorFactory().slug for _ in range(3)]
        cls.location_slug = PerimeterFactory().slug

    @classmethod
    def _generate_fake_data_form(
        cls, _step_1={}, _step_2={}, _step_3={}, _step_4={}, _step_5={}, tender_not_saved: Tender = None
    ):
        if not tender_not_saved:
            tender_not_saved = TenderFactory.build(author=cls.user_buyer)

        step_1 = {
            "tender_create_multi_step_view-current_step": "general",
            "general-kind": tender_not_saved.kind,
            "general-title": tender_not_saved.title,
            "general-sectors": cls.sectors,
            "general-location": cls.location_slug,
            "general-is_country_area": tender_not_saved.is_country_area,
        } | _step_1
        step_2 = {
            "tender_create_multi_step_view-current_step": "description",
            "description-description": tender_not_saved.description,
            "description-start_working_date": tender_not_saved.start_working_date,
            "description-external_link": tender_not_saved.external_link,
            "description-amount": tender_constants.AMOUNT_RANGE_1000_MORE,
        } | _step_2
        step_3 = {
            "tender_create_multi_step_view-current_step": "contact",
            "contact-contact_first_name": tender_not_saved.contact_first_name,
            "contact-contact_last_name": tender_not_saved.contact_last_name,
            "contact-contact_email": tender_not_saved.contact_email,
            "contact-contact_phone": "0123456789",
            "contact-contact_company_name": "TEST",
            "contact-response_kind": [Tender.RESPONSE_KIND_EMAIL],
            "contact-deadline_date": tender_not_saved.deadline_date,
        } | _step_3
        step_4 = {
            "tender_create_multi_step_view-current_step": "survey",
            "survey-scale_marche_useless": tender_constants.SURVEY_SCALE_QUESTION_0,
            "survey-worked_with_inclusif_siae_this_kind_tender": tender_constants.SURVEY_DONT_KNOW,
            "survey-is_encouraged_by_le_marche": tender_constants.SURVEY_NOT_ENCOURAGED_ONLY_BY_US,
            "survey-providers_out_of_insertion": tender_constants.SURVEY_SCALE_QUESTION_2,
            "survey-le_marche_doesnt_exist_how_to_find_siae": "TEST",
        } | _step_4

        step_5 = {
            "tender_create_multi_step_view-current_step": "confirmation",
        } | _step_5

        return [step_1, step_2, step_3, step_4, step_5]

    def _check_every_step(self, tenders_step_data, final_redirect_page: str = reverse("wagtail_serve", args=("",))):
        for step, data_step in enumerate(tenders_step_data, 1):
            response = self.client.post(reverse("tenders:create"), data=data_step, follow=True)
            if step == len(tenders_step_data):
                # make sure that after the create tender we are redirected to ??
                self.assertEqual(response.status_code, 200)
                self.assertRedirects(response, final_redirect_page)
                return response
            else:
                self.assertEqual(response.status_code, 200)
                current_errors = response.context_data["form"].errors
                self.assertEquals(current_errors, {})

    def test_anyone_can_access_create_tender(self):
        # anonymous
        url = reverse("tenders:create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # buyer
        self.client.force_login(self.user_buyer)
        url = reverse("tenders:create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # siae
        self.client.force_login(self.user_siae)
        url = reverse("tenders:create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_tender_wizard_form_all_good_authenticated(self):
        tenders_step_data = self._generate_fake_data_form()
        self.client.force_login(self.user_buyer)
        final_response = self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))
        tender = Tender.objects.get(title=tenders_step_data[0].get("general-title"))
        self.assertIsNotNone(tender)
        self.assertIsInstance(tender, Tender)
        messages = list(get_messages(final_response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            TenderCreateMultiStepView.get_success_message(
                TenderCreateMultiStepView, tenders_step_data, tender, is_draft=False
            ),
        )

    def test_tender_wizard_form_not_created(self):
        self.client.force_login(self.user_buyer)
        tenders_step_data = self._generate_fake_data_form()
        # remove required field in survey
        tenders_step_data[3].pop("survey-scale_marche_useless")
        with self.assertRaises(AssertionError):
            self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))

    def test_tender_wizard_form_all_good_anonymous(self):
        tenders_step_data = self._generate_fake_data_form()
        final_response = self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))
        tender = Tender.objects.get(title=tenders_step_data[0].get("general-title"))
        self.assertIsNotNone(tender)
        self.assertIsInstance(tender, Tender)
        self.assertEqual(tender.status, Tender.STATUS_PUBLISHED)
        self.assertIsNotNone(tender.published_at)
        messages = list(get_messages(final_response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            TenderCreateMultiStepView.get_success_message(
                TenderCreateMultiStepView, tenders_step_data, tender, is_draft=False
            ),
        )

    def test_tender_wizard_form_all_good_perimeters(self):
        self.client.force_login(self.user_buyer)
        tenders_step_data = self._generate_fake_data_form()
        self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))
        tender: Tender = Tender.objects.get(title=tenders_step_data[0].get("general-title"))
        self.assertIsNotNone(tender)
        self.assertIsInstance(tender, Tender)
        self.assertEqual(tender.location.slug, self.location_slug)
        tender_list_perimeter_id = [perimeter.slug for perimeter in tender.perimeters.all()]
        self.assertEqual(len(tender_list_perimeter_id), 1)
        self.assertEqual(tender_list_perimeter_id, [self.location_slug])
        tenders_sectors = tender.sectors.all()
        tender_list_sector_slug = [sector.slug for sector in tenders_sectors]
        self.assertEqual(len(tender_list_sector_slug), tenders_sectors.count())
        self.assertEqual(tender_list_sector_slug.sort(), self.sectors.sort())

    def test_tender_wizard_form_draft(self):
        tenders_step_data = self._generate_fake_data_form(_step_5={"is_draft": "1"})
        final_response = self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))
        tender: Tender = Tender.objects.get(title=tenders_step_data[0].get("general-title"))
        self.assertIsNotNone(tender)
        self.assertIsInstance(tender, Tender)
        self.assertEqual(tender.status, Tender.STATUS_DRAFT)
        self.assertIsNone(tender.published_at)
        messages = list(get_messages(final_response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            TenderCreateMultiStepView.get_success_message(
                TenderCreateMultiStepView, tenders_step_data, tender, is_draft=True
            ),
        )

    def test_tender_wizard_form_questions_list(self):
        initial_data_questions_list = [
            {"text": "Avez-vous suffisamment d'effectifs ? "},
            {"text": "Êtes-vous disponible tout l'été ? "},
        ]
        tenders_step_data = self._generate_fake_data_form(
            _step_2={"description-questions_list": json.dumps(initial_data_questions_list)}  # json field
        )

        self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))
        tender: Tender = Tender.objects.get(title=tenders_step_data[0].get("general-title"))
        self.assertIsNotNone(tender)
        self.assertIsInstance(tender, Tender)
        self.assertEqual(tender.questions.count(), len(initial_data_questions_list))  # count is 2
        self.assertEqual(tender.questions_list()[0].get("text"), initial_data_questions_list[0].get("text"))


class TenderMatchingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
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

    def test_matching_siae_presta_type(self):
        tender = TenderFactory(presta_type=[], sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 2)
        tender = TenderFactory(
            presta_type=[siae_constants.PRESTA_BUILD], sectors=self.sectors, perimeters=self.perimeters
        )
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 2)
        tender = TenderFactory(
            presta_type=[siae_constants.PRESTA_PREST], sectors=self.sectors, perimeters=self.perimeters
        )
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 1)

    def test_matching_siae_kind(self):
        tender = TenderFactory(siae_kind=[], sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 2)
        tender = TenderFactory(siae_kind=[siae_constants.KIND_AI], sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 1)
        tender = TenderFactory(
            siae_kind=[siae_constants.KIND_ESAT, siae_constants.KIND_AI],
            sectors=self.sectors,
            perimeters=self.perimeters,
        )
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 2)
        tender = TenderFactory(siae_kind=[siae_constants.KIND_SEP], sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 0)

    def test_matching_siae_sectors(self):
        tender = TenderFactory(sectors=self.sectors)
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 2)

    def test_matching_siae_perimeters_custom(self):
        # add Siae with geo_range_country
        siae_country = SiaeFactory(is_active=True, geo_range=siae_constants.GEO_RANGE_COUNTRY)
        siae_country.sectors.add(self.sectors[0])
        # tender perimeter custom with include_country_area = False
        tender_1 = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender(tender_1)
        self.assertEqual(len(siae_found_list), 2 + 0)
        # tender perimeter custom with include_country_area = True
        tender_2 = TenderFactory(sectors=self.sectors, perimeters=self.perimeters, include_country_area=True)
        siae_found_list = Siae.objects.filter_with_tender(tender_2)
        self.assertEqual(len(siae_found_list), 2 + 1)

    def test_matching_siae_perimeters_custom_2(self):
        # add Siae with geo_range_department (75)
        siae_department = SiaeFactory(is_active=True, department="75", geo_range=siae_constants.GEO_RANGE_DEPARTMENT)
        siae_department.sectors.add(self.sectors[0])
        # tender perimeter custom
        tender = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 2 + 1)

    def test_matching_siae_perimeters_france(self):
        # tender france
        tender = TenderFactory(sectors=self.sectors, is_country_area=True)
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 0)
        # add Siae with geo_range_country
        siae_country = SiaeFactory(is_active=True, geo_range=siae_constants.GEO_RANGE_COUNTRY)
        siae_country.sectors.add(self.sectors[0])
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 1)

    def test_no_siaes(self):
        # tender with empty sectors list
        tender = TenderFactory(sectors=[SectorFactory()], perimeters=self.perimeters)
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 0)
        # tender near Marseille
        tender_marseille = TenderFactory(sectors=self.sectors, perimeters=[self.perimeter_marseille])
        siae_found_list_marseille = Siae.objects.filter_with_tender(tender_marseille)
        self.assertEqual(len(siae_found_list_marseille), 0)

    def test_with_no_contact_email(self):
        tender = TenderFactory(sectors=self.sectors, perimeters=self.perimeters)
        SiaeFactory(
            is_active=True, geo_range=siae_constants.GEO_RANGE_COUNTRY, contact_email="", sectors=[self.sectors[0]]
        )
        siae_found_list = Siae.objects.filter_with_tender(tender)
        self.assertEqual(len(siae_found_list), 2 + 0)

    # def test_number_queries(self):
    #     tender = TenderFactory(sectors=self.sectors)
    #     with self.assertNumQueries(8):
    #         siae_found_list = Siae.objects.filter_with_tender(tender)
    #     self.assertEqual(len(siae_found_list), 2)


class TenderListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        perimeter = PerimeterFactory(post_codes=["43705"], insee_code="06", name="Auvergne-Rhône-Alpes")
        cls.siae_user_1 = UserFactory(kind=User.KIND_SIAE)
        cls.siae_1 = SiaeFactory()
        cls.siae_2 = SiaeFactory(post_code=perimeter.post_codes[0])
        cls.siae_user_2 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae_1])
        cls.user_buyer_1 = UserFactory(kind=User.KIND_BUYER)
        cls.user_buyer_2 = UserFactory(kind=User.KIND_BUYER)
        cls.user_partner = UserFactory(kind=User.KIND_PARTNER)
        cls.tender = TenderFactory(author=cls.user_buyer_1, validated_at=timezone.now(), perimeters=[perimeter])
        cls.tender_2 = TenderFactory(
            author=cls.user_buyer_1, deadline_date=timezone.now() - timedelta(days=5), perimeters=[perimeter]
        )
        cls.tender_3 = TenderFactory(
            author=cls.user_buyer_1,
            validated_at=timezone.now(),
            deadline_date=timezone.now() - timedelta(days=5),
            perimeters=[perimeter],
        )
        cls.tendersiae_3_1 = TenderSiae.objects.create(
            tender=cls.tender_3, siae=cls.siae_1, email_send_date=timezone.now()
        )
        cls.tendersiae_3_2 = TenderSiae.objects.create(
            tender=cls.tender_3,
            siae=cls.siae_2,
            email_send_date=timezone.now(),
            detail_contact_click_date=timezone.now(),
        )

    def test_anonymous_user_cannot_list_tenders(self):
        url = reverse("tenders:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_siae_user_should_see_matching_tenders(self):
        # TODO: add more matching tests
        # user without siae
        self.client.force_login(self.siae_user_1)
        url = reverse("tenders:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tenders"]), 0)
        # user with siae
        self.client.force_login(self.siae_user_2)
        url = reverse("tenders:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tenders"]), 1)
        self.assertNotContains(response, "2 prestataires ciblés")  # tender_3, but only visible to author
        self.assertNotContains(response, "1 prestataire intéressé")  # tender_3, but only visible to author

    def test_buyer_user_should_only_see_his_tenders(self):
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tenders"]), 3)
        self.assertContains(response, "2 prestataires ciblés")  # tender_3
        self.assertContains(response, "1 prestataire intéressé")  # tender_3
        self.assertNotContains(response, "Demandes reçues")
        self.assertNotContains(response, '<span class="badge badge-sm badge-pill badge-important">Nouveau</span>')

    def test_other_user_without_tender_should_not_see_any_tenders(self):
        self.client.force_login(self.user_partner)
        url = reverse("tenders:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tenders"]), 0)

    def test_viewing_tender_list_should_update_stats(self):
        self.assertIsNone(self.siae_user_1.tender_list_last_seen_date)
        self.client.force_login(self.siae_user_1)
        url = reverse("tenders:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.get(id=self.siae_user_1.id).tender_list_last_seen_date)

    def test_siae_user_should_see_unread_badge(self):
        self.client.force_login(self.siae_user_2)
        url = reverse("tenders:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tenders"]), 1)
        # The badge in header
        self.assertContains(response, 'Demandes reçues <span class="badge badge-pill badge-important fs-xs">1</span>')
        # The badge in tender list
        self.assertContains(response, '<span class="badge badge-sm badge-pill badge-important">Nouveau</span>')

        # Open tender detail page
        detail_url = reverse("tenders:detail", kwargs={"slug": self.tender_3.slug})
        self.client.get(detail_url)

        # The badges have disappeared
        response = self.client.get(url)
        self.assertNotContains(
            response, 'Demandes reçues <span class="badge badge-pill badge-important fs-xs">1</span>'
        )
        self.assertNotContains(response, '<span class="badge badge-sm badge-pill badge-important">Nouveau</span>')


class TenderDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_1 = SiaeFactory(name="ZZ ESI")
        cls.siae_2 = SiaeFactory(name="ABC Insertion")
        cls.siae_user_1 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae_1])
        cls.siae_user_2 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae_2])
        cls.siae_user_3 = UserFactory(kind=User.KIND_SIAE)
        cls.user_buyer_1 = UserFactory(kind=User.KIND_BUYER, company_name="Entreprise Buyer")
        cls.user_buyer_2 = UserFactory(kind=User.KIND_BUYER)
        cls.user_partner = UserFactory(kind=User.KIND_PARTNER)
        cls.user_admin = UserFactory(kind=User.KIND_ADMIN)
        sector_1 = SectorFactory(name="Bricolage")
        grenoble_perimeter = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
            # coords=Point(5.7301, 45.1825),
        )
        cls.tender_1 = TenderFactory(
            kind=tender_constants.KIND_TENDER,
            author=cls.user_buyer_1,
            amount=tender_constants.AMOUNT_RANGE_100_150,
            accept_share_amount=True,
            response_kind=[Tender.RESPONSE_KIND_EMAIL],
            sectors=[sector_1],
            location=grenoble_perimeter,
        )
        cls.tendersiae_1_1 = TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_1,
            source="EMAIL",
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
            detail_contact_click_date=timezone.now(),
        )
        TenderQuestionFactory(tender=cls.tender_1)
        cls.tender_2 = TenderFactory(author=cls.user_buyer_1, contact_company_name="Another company")

    def test_anyone_can_view_validated_tenders(self):
        # anonymous
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Voir l'appel d'offres")
        # users
        for user in User.objects.all():
            self.client.force_login(user)
            url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_only_author_or_admin_can_view_non_validated_tender(self):
        tender_draft = TenderFactory(author=self.user_buyer_1, status=tender_constants.STATUS_DRAFT)
        tender_published = TenderFactory(
            author=self.user_buyer_1, status=tender_constants.STATUS_PUBLISHED, published_at=timezone.now()
        )
        for tender in [tender_draft, tender_published]:
            # anonymous
            url = reverse("tenders:detail", kwargs={"slug": tender.slug})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            # self.assertContains(response.url, "/accounts/login/?next=/besoins/")
            # author & admin
            for user in [self.user_buyer_1, self.user_admin]:
                self.client.force_login(user)
                url = reverse("tenders:detail", kwargs={"slug": tender.slug})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
            # other users
            for user in [self.siae_user_1, self.user_buyer_2, self.user_partner]:
                self.client.force_login(user)
                url = reverse("tenders:detail", kwargs={"slug": tender.slug})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, "/")

    def test_tender_basic_fields_display(self):
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # sector
        self.assertContains(response, "Bricolage")
        # localisation
        self.assertContains(response, "Grenoble")
        # company_name
        self.assertContains(response, "Entreprise Buyer")  # tender.author.company_name
        url = reverse("tenders:detail", kwargs={"slug": self.tender_2.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Another company")  # tender.contact_company_name

    def test_tender_questions_display(self):
        # tender with questions: section should be visible
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Questions du client")
        # author has different wording
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Questions à poser aux prestataires ciblés")
        # tender without questions: section should be hidden
        tender_2 = TenderFactory(author=self.user_buyer_2, constraints="")
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Questions à poser aux prestataires ciblés")
        self.assertNotContains(response, "Questions du client")

    def test_tender_constraints_display(self):
        # tender with constraints: section should be visible
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contraintes techniques spécifiques")
        # tender without constraints: section should be hidden
        tender_2 = TenderFactory(author=self.user_buyer_2, constraints="")
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Contraintes techniques spécifiques")

    def test_tender_amount_display(self):
        # tender with amount + accept_share_amount: section should be visible
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Budget du client")
        # author has different wording
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Montant du marché")
        self.assertContains(response, Tender.TENDER_ACCEPT_SHARE_AMOUNT_TRUE)
        # tender with amount + !accept_share_amount: section should be hidden
        tender_2 = TenderFactory(
            author=self.user_buyer_2, amount=tender_constants.AMOUNT_RANGE_100_150, accept_share_amount=False
        )
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Montant du marché")
        self.assertNotContains(response, "Budget du client")
        # author has section
        self.client.force_login(self.user_buyer_2)
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertContains(response, "Montant du marché")
        self.assertContains(response, Tender.TENDER_ACCEPT_SHARE_AMOUNT_FALSE)

    def test_tender_deadline_date_display(self):
        # tender is not outdated by default
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "Clôturé")
        # new tender with outdated deadline_date
        tender_2 = TenderFactory(deadline_date=timezone.now() - timedelta(days=1))
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertContains(response, "Clôturé")

    def test_tender_author_has_additional_stats(self):
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "1 prestataire ciblé")
        self.assertContains(response, "1 prestataire intéressé")
        # but hidden for non-author
        self.client.force_login(self.user_buyer_2)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "1 prestataire ciblé")
        self.assertNotContains(response, "1 prestataire intéressé")

    def test_update_tendersiae_stats_on_tender_view(self):
        self.tender_1.siaes.add(self.siae_2)
        self.assertEqual(self.tender_1.tendersiae_set.count(), 1 + 1)
        self.assertEqual(self.tender_1.tendersiae_set.first().siae, self.siae_2)
        self.assertEqual(self.tender_1.tendersiae_set.last().siae, self.siae_1)
        self.assertIsNone(self.tender_1.tendersiae_set.first().email_link_click_date)
        self.assertIsNone(self.tender_1.tendersiae_set.first().detail_display_date)
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().email_link_click_date)  # siae_1
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().detail_display_date)
        # first load anonymous
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Déjà 1 prestataire inclusif")
        # reload anonymous with ?siae_id=
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug}) + f"?siae_id={self.siae_2.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        siae_2_email_link_click_date = self.tender_1.tendersiae_set.first().email_link_click_date
        self.assertIsNotNone(siae_2_email_link_click_date)
        self.assertIsNone(self.tender_1.tendersiae_set.first().detail_display_date)
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().detail_display_date)
        self.assertContains(response, "Déjà 2 prestataires inclusifs")
        self.assertNotContains(response, "contactez dès maintenant le client")
        # reload logged in (doesn't update email_link_click_date)
        self.client.force_login(self.siae_user_2)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug}) + f"?siae_id={self.siae_2.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tender_1.tendersiae_set.first().email_link_click_date, siae_2_email_link_click_date)
        siae_2_detail_display_date = self.tender_1.tendersiae_set.first().detail_display_date
        self.assertIsNotNone(siae_2_detail_display_date)
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().detail_display_date)
        self.assertContains(response, "Déjà 2 prestataires inclusifs")
        self.assertNotContains(response, "contactez dès maintenant le client")
        # reload (doesn't update detail_display_date)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tender_1.tendersiae_set.first().detail_display_date, siae_2_detail_display_date)
        self.assertContains(response, "Déjà 2 prestataires inclusifs")
        self.assertNotContains(response, "contactez dès maintenant le client")

    def test_create_tendersiae_stats_on_tender_view_by_new_siae(self):
        # self.tender_1.siaes.add(self.siae_2)
        self.assertEqual(self.tender_1.tendersiae_set.count(), 1)
        self.assertEqual(self.tender_1.tendersiae_set.first().siae, self.siae_1)
        self.assertIsNotNone(self.tender_1.tendersiae_set.first().detail_display_date)  # siae_1
        # first load anonymous
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Déjà 1 prestataire inclusif")
        # first load
        self.client.force_login(self.siae_user_2)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tender_1.tendersiae_set.count(), 1 + 1)
        self.assertEqual(self.tender_1.tendersiae_set.first().siae, self.siae_2)
        self.assertIsNotNone(self.tender_1.tendersiae_set.first().detail_display_date)
        self.assertContains(response, "Déjà 2 prestataires inclusifs")

    def test_tender_contact_display(self):
        # anonymous
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "Clôturé")
        self.assertContains(response, "Voir l'appel d'offres")
        # siae user interested
        self.client.force_login(self.siae_user_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, "Voir l'appel d'offres")
        # siae user not concerned
        self.client.force_login(self.siae_user_2)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Voir l'appel d'offres")
        # siae user without siae
        self.client.force_login(self.siae_user_3)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "veuillez d'abord vous")
        self.assertNotContains(response, "Voir l'appel d'offres")
        # author
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Coordonnées")
        self.assertNotContains(response, "Voir l'appel d'offres")

    def test_tender_outdated_contact_display(self):
        tender_2 = TenderFactory(
            kind=tender_constants.KIND_QUOTE,
            author=self.user_buyer_1,
            deadline_date=timezone.now() - timedelta(days=1),
        )
        TenderSiae.objects.create(tender=tender_2, siae=self.siae_1, detail_contact_click_date=timezone.now())
        # anonymous
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertContains(response, "Clôturé")
        self.assertNotContains(response, "Répondre à cette opportunité")
        # siae user interested
        self.client.force_login(self.siae_user_1)
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertContains(response, "Clôturé")
        self.assertNotContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, "Répondre à cette opportunité")
        # siae user not concerned
        self.client.force_login(self.siae_user_2)
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertContains(response, "Clôturé")
        self.assertNotContains(response, "Répondre à cette opportunité")
        # siae user without siae
        self.client.force_login(self.siae_user_3)
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertContains(response, "Clôturé")
        self.assertNotContains(response, "veuillez d'abord vous")
        self.assertNotContains(response, "Répondre à cette opportunité")
        # author
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertContains(response, "Clôturé")
        self.assertContains(response, "Coordonnées")
        self.assertNotContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, "Répondre à cette opportunité")

    def test_some_partners_can_display_contact_details(self):
        # this partner cannot
        self.client.force_login(self.user_partner)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "pour être mis en relation avec le client.")
        self.assertNotContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, "Voir l'appel d'offres")
        # this one can!
        user_partner_2 = UserFactory(kind=User.KIND_PARTNER, can_display_tender_contact_details=True)
        self.client.force_login(user_partner_2)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "pour être mis en relation avec le client.")
        self.assertContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, "Voir l'appel d'offres")

    def test_tender_contact_details_display(self):
        # tender_1 author
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Coordonnées")
        self.assertContains(response, self.tender_1.contact_email)  # RESPONSE_KIND_EMAIL
        self.assertNotContains(response, self.tender_1.contact_phone)
        self.assertNotContains(response, settings.TEAM_CONTACT_EMAIL)
        self.assertNotContains(response, "Voir l'appel d'offres")
        self.assertNotContains(response, "Lien partagé")
        # tender with same kind & different response_kind
        tender_2 = TenderFactory(
            kind=tender_constants.KIND_TENDER,
            author=self.user_buyer_1,
            response_kind=[Tender.RESPONSE_KIND_EMAIL, Tender.RESPONSE_KIND_EXTERNAL],
            external_link="https://example.com",
        )
        # tender_2 author
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertContains(response, "Coordonnées")
        self.assertContains(response, tender_2.contact_email)  # RESPONSE_KIND_EMAIL
        self.assertNotContains(response, tender_2.contact_phone)
        self.assertNotContains(response, settings.TEAM_CONTACT_EMAIL)
        self.assertContains(response, "Voir l'appel d'offres")  # KIND_TENDER & RESPONSE_KIND_EXTERNAL
        self.assertNotContains(response, "Lien partagé")
        # tender with different kind & response_kind
        tender_3 = TenderFactory(
            kind=tender_constants.KIND_PROJECT,
            author=self.user_buyer_2,
            response_kind=[Tender.RESPONSE_KIND_TEL, Tender.RESPONSE_KIND_EXTERNAL],
            external_link="https://example.com",
        )
        TenderSiae.objects.create(tender=tender_3, siae=self.siae_1, detail_contact_click_date=timezone.now())
        # tender_3 author
        self.client.force_login(self.user_buyer_2)
        url = reverse("tenders:detail", kwargs={"slug": tender_3.slug})
        response = self.client.get(url)
        self.assertContains(response, "Coordonnées")
        self.assertNotContains(response, tender_3.contact_email)
        self.assertContains(response, tender_3.contact_phone)  # RESPONSE_KIND_TEL
        self.assertNotContains(response, settings.TEAM_CONTACT_EMAIL)
        self.assertNotContains(response, "Voir l'appel d'offres")
        self.assertContains(response, "Lien partagé")  # !KIND_TENDER & RESPONSE_KIND_EXTERNAL
        # tender_3 siae user interested
        self.client.force_login(self.siae_user_1)
        url = reverse("tenders:detail", kwargs={"slug": tender_3.slug})
        response = self.client.get(url)
        self.assertContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, tender_3.contact_email)
        self.assertContains(response, tender_3.contact_phone)
        self.assertContains(response, settings.TEAM_CONTACT_EMAIL)
        self.assertNotContains(response, "Voir l'appel d'offres")
        self.assertContains(response, "Lien partagé")
        # tender with different response_kind
        tender_4 = TenderFactory(
            kind=tender_constants.KIND_PROJECT,
            author=self.user_buyer_2,
            response_kind=[Tender.RESPONSE_KIND_EXTERNAL],
            external_link="https://example.com",
        )
        TenderSiae.objects.create(tender=tender_4, siae=self.siae_1, detail_contact_click_date=timezone.now())
        # tender_4 author
        self.client.force_login(self.user_buyer_2)
        url = reverse("tenders:detail", kwargs={"slug": tender_4.slug})
        response = self.client.get(url)
        self.assertContains(response, "Coordonnées")
        self.assertNotContains(response, tender_4.contact_email)
        self.assertNotContains(response, tender_4.contact_phone)
        self.assertNotContains(response, settings.TEAM_CONTACT_EMAIL)
        self.assertNotContains(response, "Voir l'appel d'offres")
        self.assertContains(response, "Lien partagé")  # !KIND_TENDER & RESPONSE_KIND_EXTERNAL
        # tender_4 siae user interested
        self.client.force_login(self.siae_user_1)
        url = reverse("tenders:detail", kwargs={"slug": tender_4.slug})
        response = self.client.get(url)
        self.assertContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, tender_4.contact_email)
        self.assertNotContains(response, tender_4.contact_phone)
        self.assertNotContains(response, settings.TEAM_CONTACT_EMAIL)
        self.assertNotContains(response, "Voir l'appel d'offres")
        self.assertContains(response, "Lien partagé")
        # tender_4 siae user interested but logged out (with siae_id parameter)
        self.client.logout()
        url = reverse("tenders:detail", kwargs={"slug": tender_4.slug}) + f"?siae_id={self.siae_1.id}"
        response = self.client.get(url)
        self.assertContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, tender_4.contact_email)
        self.assertNotContains(response, tender_4.contact_phone)
        self.assertNotContains(response, settings.TEAM_CONTACT_EMAIL)
        self.assertNotContains(response, "Voir l'appel d'offres")
        self.assertContains(response, "Lien partagé")


class TenderDetailContactClickStatViewViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory(name="ZZ ESI")
        cls.siae_user_1 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae])
        cls.siae_user_2 = UserFactory(kind=User.KIND_SIAE)
        cls.user_buyer_1 = UserFactory(kind=User.KIND_BUYER)
        cls.user_buyer_2 = UserFactory(kind=User.KIND_BUYER)
        cls.user_partner = UserFactory(kind=User.KIND_PARTNER)
        cls.user_admin = UserFactory(kind=User.KIND_ADMIN)
        cls.tender = TenderFactory(kind=tender_constants.KIND_TENDER, author=cls.user_buyer_1, siaes=[cls.siae])

    def test_anonymous_user_cannot_call_tender_contact_click(self):
        url = reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_only_siae_user_or_with_siae_id_param_can_call_tender_contact_click(self):
        # forbidden
        for user in [self.user_buyer_1, self.user_buyer_2, self.user_partner, self.user_admin]:
            self.client.force_login(user)
            url = reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug})
            response = self.client.post(url, data={"detail_contact_click_confirm": "false"})
            self.assertEqual(response.status_code, 403)
        # authorized
        for user in [self.siae_user_1, self.siae_user_2]:
            self.client.force_login(user)
            url = reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug})
            response = self.client.post(url, data={"detail_contact_click_confirm": "false"})
            self.assertEqual(response.status_code, 302)
        # authorized with siae_id parameter
        self.client.logout()
        url = (
            reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug})
            + f"?siae_id={self.siae.id}"
        )
        response = self.client.post(url, data={"detail_contact_click_confirm": "false"})
        self.assertEqual(response.status_code, 302)
        # forbidden because wrong siae_id parameter
        self.client.logout()
        url = reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug}) + "?siae_id=test"
        response = self.client.post(url, data={"detail_contact_click_confirm": "false"})
        self.assertEqual(response.status_code, 403)

    def test_update_tendersiae_stats_on_tender_contact_click(self):
        siae_2 = SiaeFactory(name="ABC Insertion")
        self.siae_user_2.siaes.add(siae_2)
        self.tender.siaes.add(siae_2)
        self.assertEqual(self.tender.tendersiae_set.count(), 2)
        self.assertEqual(self.tender.tendersiae_set.first().siae, siae_2)
        self.assertEqual(self.tender.tendersiae_set.last().siae, self.siae)
        self.assertIsNone(self.tender.tendersiae_set.first().detail_contact_click_date)
        self.assertIsNone(self.tender.tendersiae_set.last().detail_contact_click_date)
        # first load
        self.client.force_login(self.siae_user_2)
        url = reverse("tenders:detail", kwargs={"slug": self.tender.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "contactez dès maintenant le client")
        # click on button
        url = reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug})
        response = self.client.post(url, data={"detail_contact_click_confirm": "true"})
        self.assertEqual(response.status_code, 302)
        siae_2_detail_contact_click_date = self.tender.tendersiae_set.first().detail_contact_click_date
        self.assertNotEqual(siae_2_detail_contact_click_date, None)
        self.assertEqual(self.tender.tendersiae_set.last().detail_contact_click_date, None)
        # reload page
        url = reverse("tenders:detail", kwargs={"slug": self.tender.slug})
        response = self.client.get(url)
        self.assertContains(response, "contactez dès maintenant le client")
        # clicking again on the button doesn't update detail_contact_click_date
        # Note: button will disappear on reload anyway
        url = reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug})
        response = self.client.post(url, data={"detail_contact_click_confirm": "false"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.tender.tendersiae_set.first().detail_contact_click_date, siae_2_detail_contact_click_date
        )

    def test_update_tendersiae_stats_on_tender_contact_click_with_siae_id_param(self):
        siae_2 = SiaeFactory(name="ABC Insertion")
        self.siae_user_2.siaes.add(siae_2)
        self.tender.siaes.add(siae_2)
        self.assertEqual(self.tender.tendersiae_set.count(), 2)
        self.assertEqual(self.tender.tendersiae_set.first().siae, siae_2)
        self.assertEqual(self.tender.tendersiae_set.last().siae, self.siae)
        self.assertIsNone(self.tender.tendersiae_set.first().detail_contact_click_date)
        self.assertIsNone(self.tender.tendersiae_set.last().detail_contact_click_date)
        # first load
        url = reverse("tenders:detail", kwargs={"slug": self.tender.slug}) + f"?siae_id={siae_2.id}"
        response = self.client.get(url)
        self.assertNotContains(response, "contactez dès maintenant le client")
        # click on button
        url = reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug}) + f"?siae_id={siae_2.id}"
        response = self.client.post(url, data={"detail_contact_click_confirm": "true"})
        self.assertEqual(response.status_code, 302)
        siae_2_detail_contact_click_date = self.tender.tendersiae_set.first().detail_contact_click_date
        self.assertNotEqual(siae_2_detail_contact_click_date, None)
        self.assertEqual(self.tender.tendersiae_set.last().detail_contact_click_date, None)
        # reload page
        url = reverse("tenders:detail", kwargs={"slug": self.tender.slug}) + f"?siae_id={siae_2.id}"
        response = self.client.get(url)
        self.assertContains(response, "contactez dès maintenant le client")
        # clicking again on the button doesn't update detail_contact_click_date
        # Note: button will disappear on reload anyway
        url = reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug}) + f"?siae_id={siae_2.id}"
        response = self.client.post(url, data={"detail_contact_click_confirm": "false"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.tender.tendersiae_set.first().detail_contact_click_date, siae_2_detail_contact_click_date
        )


# TODO: this test doesn't work anymore. find a way to test logging post-email in non-prod environments?
# class TenderTasksTest(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         cls.tender = TenderFactory()

#     def test_send_email_for_feedbacks_set_log(self):
#         self.assertEqual(len(self.tender.logs), 0)
#         send_tenders_author_30_days(self.tender, kind="feedback")
#         # fetch tender to be sure to have the last version of tender
#         tender: Tender = Tender.objects.get(pk=self.tender.pk)
#         self.assertEqual(len(tender.logs), 1)
#         self.assertEqual(tender.logs[0]["action"], "email_feedback_30d_sent")


class TenderSiaeListView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_1 = SiaeFactory(
            name="ZZ ESI",
            kind=siae_constants.KIND_EI,
            is_qpv=True,
            city="Grenoble",
            post_code="38100",
            employees_insertion_count=103,
        )
        cls.siae_2 = SiaeFactory(
            name="ABC Insertion", kind=siae_constants.KIND_EI, city="Grenoble", post_code="38000", ca=276000
        )
        cls.siae_3 = SiaeFactory(
            name="Une autre structure", kind=siae_constants.KIND_ETTI, employees_insertion_count=53
        )
        cls.siae_4 = SiaeFactory(name="Une dernière structure", kind=siae_constants.KIND_ETTI)
        cls.siae_user_1 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae_1, cls.siae_2])
        cls.siae_user_2 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae_3])
        cls.user_buyer_1 = UserFactory(kind=User.KIND_BUYER)
        cls.user_buyer_2 = UserFactory(kind=User.KIND_BUYER)
        cls.user_partner = UserFactory(kind=User.KIND_PARTNER)
        cls.tender_1 = TenderFactory(author=cls.user_buyer_1)
        cls.tender_2 = TenderFactory(author=cls.user_buyer_2)
        cls.tendersiae_1_1 = TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_1,
            email_send_date=timezone.now(),
            detail_contact_click_date=timezone.now(),
        )
        cls.tendersiae_1_2 = TenderSiae.objects.create(
            tender=cls.tender_1, siae=cls.siae_2, email_send_date=timezone.now()
        )
        cls.tendersiae_1_3 = TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_3,
            email_send_date=timezone.now() - timedelta(hours=1),
            detail_contact_click_date=timezone.now() - timedelta(hours=1),
        )
        cls.tendersiae_1_4 = TenderSiae.objects.create(
            tender=cls.tender_1, siae=cls.siae_4, detail_contact_click_date=timezone.now() - timedelta(hours=2)
        )
        cls.tendersiae_2_1 = TenderSiae.objects.create(
            tender=cls.tender_2,
            siae=cls.siae_2,
            email_send_date=timezone.now(),
            detail_contact_click_date=timezone.now(),
        )
        cls.perimeter_city = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
            # coords=Point(5.7301, 45.1825),
        )

    def test_anonymous_user_cannot_view_tender_siae_interested_list(self):
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_only_tender_author_can_view_tender_1_siae_interested_list(self):
        # forbidden
        for user in [self.user_buyer_2, self.user_partner, self.siae_user_1, self.siae_user_2]:
            self.client.force_login(user)
            url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/besoins/")
        # authorized
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 3)  # email_send_date
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug, "status": "INTERESTED"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 3)  # detail_contact_click_date

    def test_viewing_tender_siae_interested_list_should_update_stats(self):
        self.assertIsNone(self.tender_1.siae_list_last_seen_date)
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 3)  # email_send_date
        self.assertIsNotNone(Tender.objects.get(id=self.tender_1.id).siae_list_last_seen_date)

    def test_filter_tender_siae_list(self):
        self.client.force_login(self.user_buyer_1)
        # filter by location
        url = (
            reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug})
            + f"?locations={self.perimeter_city.slug}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 2)  # email_send_date & located in Grenoble
        url = (
            reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug, "status": "INTERESTED"})
            + f"?locations={self.perimeter_city.slug}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 1)  # detail_contact_click_date & located in Grenoble
        # filter by kind
        url = (
            reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug})
            + f"?kind={siae_constants.KIND_ETTI}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 1)  # email_send_date & ETTI
        url = (
            reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug, "status": "INTERESTED"})
            + f"?kind={siae_constants.KIND_ETTI}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 2)  # detail_contact_click_date & ETTI
        # filter by territory
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug}) + "?territory=QPV"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 1)  # email_send_date & QPV
        # filter by count of employees
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug}) + "?employees=50-99"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 1)
        self.assertEqual(response.context["siaes"][0].id, self.siae_3.id)
        # filter by ca
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug}) + "?ca=100000-500000"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 1)
        self.assertEqual(response.context["siaes"][0].id, self.siae_2.id)

    def test_order_tender_siae_by_last_detail_contact_click_date(self):
        # TenderSiae are ordered by -created_at by default
        self.assertEqual(self.tender_1.tendersiae_set.first().id, self.tendersiae_1_4.id)
        # but TenderSiaeListView are ordered by -detail_contact_click_date
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug, "status": "INTERESTED"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 3)  # detail_contact_click_date
        self.assertEqual(response.context["siaes"][0].id, self.tendersiae_1_1.siae.id)


class TenderDetailSurveyTransactionedViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory(name="ZZ ESI")
        cls.siae_user_1 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae])
        cls.siae_user_2 = UserFactory(kind=User.KIND_SIAE)
        cls.user_buyer_1 = UserFactory(kind=User.KIND_BUYER)
        cls.user_buyer_2 = UserFactory(kind=User.KIND_BUYER)
        cls.user_partner = UserFactory(kind=User.KIND_PARTNER)
        cls.user_admin = UserFactory(kind=User.KIND_ADMIN)
        cls.tender = TenderFactory(kind=tender_constants.KIND_TENDER, author=cls.user_buyer_1, siaes=[cls.siae])

    def test_anonymous_user_cannot_call_tender_survey_transactioned(self):
        url = reverse("tenders:detail-survey-transactioned", kwargs={"slug": self.tender.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_only_tender_author_with_sesame_token_can_call_tender_survey_transactioned(self):
        # forbidden
        for user in [
            self.siae_user_1,
            self.siae_user_2,
            self.user_buyer_1,
            self.user_buyer_2,
            self.user_partner,
            self.user_admin,
        ]:
            self.client.force_login(user)
            url = reverse("tenders:detail-survey-transactioned", kwargs={"slug": self.tender.slug})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)
        # logout the last user to be sure
        self.client.logout()
        # authorized
        user_sesame_query_string = sesame_get_query_string(self.user_buyer_1)
        url = (
            reverse("tenders:detail-survey-transactioned", kwargs={"slug": self.tender.slug})
            + user_sesame_query_string
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        # but the user is not logged in !
        url = reverse("dashboard:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/profil/")

    def test_update_tender_stats_on_tender_survey_transactioned_answer_true(self):
        user_sesame_query_string = sesame_get_query_string(self.user_buyer_1)
        self.assertEqual(self.tender.survey_transactioned_answer, None)
        # load without answer
        url = (
            reverse("tenders:detail-survey-transactioned", kwargs={"slug": self.tender.slug})
            + user_sesame_query_string
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertEqual(Tender.objects.get(id=self.tender.id).survey_transactioned_answer, None)
        # load with answer
        url = (
            reverse("tenders:detail-survey-transactioned", kwargs={"slug": self.tender.slug})
            + user_sesame_query_string
            + "&answer=True"
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Merci pour vote réponse")
        self.assertEqual(Tender.objects.get(id=self.tender.id).survey_transactioned_answer, True)
        # reload with answer, ignore changes
        url = (
            reverse("tenders:detail-survey-transactioned", kwargs={"slug": self.tender.slug})
            + user_sesame_query_string
            + "&answer=False"
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Votre réponse a déjà été prise en compte")
        self.assertEqual(Tender.objects.get(id=self.tender.id).survey_transactioned_answer, True)

    def test_update_tender_stats_on_tender_survey_transactioned_answer_false(self):
        user_sesame_query_string = sesame_get_query_string(self.user_buyer_1)
        self.assertEqual(self.tender.survey_transactioned_answer, None)
        # load without answer
        url = (
            reverse("tenders:detail-survey-transactioned", kwargs={"slug": self.tender.slug})
            + user_sesame_query_string
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertEqual(Tender.objects.get(id=self.tender.id).survey_transactioned_answer, None)
        # load with answer
        url = (
            reverse("tenders:detail-survey-transactioned", kwargs={"slug": self.tender.slug})
            + user_sesame_query_string
            + "&answer=False"
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Merci pour vote réponse")
        self.assertEqual(Tender.objects.get(id=self.tender.id).survey_transactioned_answer, False)
        # reload with answer, ignore changes
        url = (
            reverse("tenders:detail-survey-transactioned", kwargs={"slug": self.tender.slug})
            + user_sesame_query_string
            + "&answer=True"
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Votre réponse a déjà été prise en compte")
        self.assertEqual(Tender.objects.get(id=self.tender.id).survey_transactioned_answer, False)
