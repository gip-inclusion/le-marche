import csv
import json
from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

import openpyxl
from django.conf import settings
from django.contrib.messages import get_messages
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from sesame.utils import get_query_string as sesame_get_query_string
from sib_api_v3_sdk.models.create_update_contact_model import CreateUpdateContactModel

from lemarche.conversations.factories import TemplateTransactionalFactory
from lemarche.conversations.models import EmailGroup
from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeActivityFactory, SiaeFactory
from lemarche.tenders import constants as tender_constants
from lemarche.tenders.enums import SurveyDoesNotExistQuestionChoices, SurveyScaleQuestionChoices
from lemarche.tenders.factories import QuestionAnswerFactory, TenderFactory, TenderQuestionFactory, TenderSiaeFactory
from lemarche.tenders.models import QuestionAnswer, Tender, TenderSiae, TenderStepsData
from lemarche.users.factories import UserFactory
from lemarche.users.models import User
from lemarche.utils import constants
from lemarche.www.tenders.views import TenderCreateMultiStepView


class TenderCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER, company_name="Entreprise Buyer")
        cls.sectors = [SectorFactory().slug for _ in range(3)]
        cls.location_slug = PerimeterFactory(insee_code="06195").slug

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
            "general-description": tender_not_saved.description,
            "general-sectors": cls.sectors,
            "general-location": cls.location_slug,
            "general-is_country_area": tender_not_saved.is_country_area,
        } | _step_1
        step_2 = {
            "tender_create_multi_step_view-current_step": "detail",
            "detail-start_working_date": tender_not_saved.start_working_date,
            "detail-deadline_date": tender_not_saved.deadline_date,
            "detail-external_link": tender_not_saved.external_link,
            "detail-amount": tender_constants.AMOUNT_RANGE_1000_MORE,
        } | _step_2
        step_3 = {
            "tender_create_multi_step_view-current_step": "contact",
            "contact-contact_first_name": tender_not_saved.contact_first_name,
            "contact-contact_last_name": tender_not_saved.contact_last_name,
            "contact-contact_email": tender_not_saved.contact_email,
            "contact-contact_phone": "0123456789",
            "contact-contact_company_name": "TEST",
            "contact-response_kind": [tender_constants.RESPONSE_KIND_EMAIL],
        } | _step_3
        step_4 = {
            "tender_create_multi_step_view-current_step": "survey",
            "survey-scale_marche_useless": SurveyScaleQuestionChoices.NON,
            "survey-le_marche_doesnt_exist_how_to_find_siae": SurveyDoesNotExistQuestionChoices.INTERNET_SEARCH,
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
                # has the step datas been cleaned ?
                self.assertEqual(TenderStepsData.objects.count(), 0)
                return response
            else:
                self.assertEqual(response.status_code, 200)
                current_errors = response.context_data["form"].errors
                self.assertEqual(current_errors, {})

                # Is the step data stored correctly ?
                tender_step_data = TenderStepsData.objects.first()
                self.assertEqual(
                    data_step["tender_create_multi_step_view-current_step"],
                    tender_step_data.steps_data[-1]["tender_create_multi_step_view-current_step"],
                )

    @patch("lemarche.www.tenders.views.get_or_create_user")
    def setup_mock_user_and_tender_creation(self, mock_get_user, user=None, title="Test Tender Form"):
        """Helper method to setup mock user"""
        user = user if user else self.user
        mock_get_user.return_value = user

        tenders_step_data = self._generate_fake_data_form({"general-title": title})
        self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))
        tender = Tender.objects.get(title=title)

        return tender, user

    def test_anyone_can_access_create_tender(self):
        # anonymous user
        url = reverse("tenders:create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # user buyer
        self.client.force_login(self.user_buyer)
        url = reverse("tenders:create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # user siae
        self.client.force_login(self.user_siae)
        url = reverse("tenders:create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @patch("lemarche.www.tenders.views.add_to_contact_list", lambda user, type, tender: None)
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
        self.assertEqual(tender.contact_first_name, self.user_buyer.first_name)
        self.assertEqual(tender.contact_last_name, self.user_buyer.last_name)
        self.assertEqual(tender.contact_email, self.user_buyer.email)
        self.assertEqual(tender.contact_phone_display, self.user_buyer.phone_display)
        self.assertEqual(tender.scale_marche_useless, tenders_step_data[3].get("survey-scale_marche_useless"))
        self.assertEqual(
            tender.le_marche_doesnt_exist_how_to_find_siae,
            tenders_step_data[3].get("survey-le_marche_doesnt_exist_how_to_find_siae"),
        )

    def test_tender_wizard_form_not_created(self):
        self.client.force_login(self.user_buyer)
        tenders_step_data = self._generate_fake_data_form()
        # remove required field in survey
        tenders_step_data[3].pop("survey-scale_marche_useless")
        with self.assertRaises(AssertionError):
            self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))

    def test_tender_wizard_form_external_link_validation(self):
        self.client.force_login(self.user_buyer)
        tenders_step_data = self._generate_fake_data_form(_step_1={"general-kind": tender_constants.KIND_TENDER})
        # set a wrong external_link (should be a valid url)
        tenders_step_data[1]["detail-external_link"] = "test"
        with self.assertRaises(AssertionError):
            self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))

    def test_tender_wizard_form_tender_with_external_link_response_kind_validation(self):
        self.client.force_login(self.user_buyer)
        tenders_step_data = self._generate_fake_data_form(_step_1={"general-kind": tender_constants.KIND_TENDER})
        tenders_step_data[1]["detail-external_link"] = "example.com"
        # set a wrong reponse_kind (should have RESPONSE_KIND_EXTERNAL)
        tenders_step_data[2]["contact-response_kind"] = []
        with self.assertRaises(AssertionError):
            self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))

    def test_tender_wizard_form_external_link_required_for_tender(self):
        self.client.force_login(self.user_buyer)
        tenders_step_data = self._generate_fake_data_form(_step_1={"general-kind": tender_constants.KIND_TENDER})
        # remove required field in survey
        tenders_step_data[1].pop("detail-external_link")
        with self.assertRaises(AssertionError):
            self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))

    def test_tender_wizard_form_contact_response_required_for_project(self):
        self.client.force_login(self.user_buyer)
        tenders_step_data = self._generate_fake_data_form(_step_1={"general-kind": tender_constants.KIND_PROJECT})
        # remove required field in survey
        tenders_step_data[2].pop("contact-response_kind")
        with self.assertRaises(AssertionError):
            self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))

    @patch("lemarche.www.tenders.views.add_to_contact_list", lambda user, type, tender: None)
    def test_tender_wizard_form_all_good_anonymous(self):
        tenders_step_data = self._generate_fake_data_form()
        final_response = self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))
        tender = Tender.objects.get(title=tenders_step_data[0].get("general-title"))
        self.assertIsNotNone(tender)
        self.assertIsInstance(tender, Tender)
        self.assertEqual(tender.status, tender_constants.STATUS_SUBMITTED)
        self.assertIsNotNone(tender.published_at)
        messages = list(get_messages(final_response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            TenderCreateMultiStepView.get_success_message(
                TenderCreateMultiStepView, tenders_step_data, tender, is_draft=False
            ),
        )

    @patch("lemarche.www.tenders.views.add_to_contact_list", lambda user, type, tender: None)
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

    @patch("lemarche.www.tenders.views.add_to_contact_list", lambda user, type, tender: None)
    def test_tender_wizard_form_draft(self):
        tenders_step_data = self._generate_fake_data_form(_step_5={"is_draft": "1"})
        final_response = self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))
        tender: Tender = Tender.objects.get(title=tenders_step_data[0].get("general-title"))
        self.assertIsNotNone(tender)
        self.assertIsInstance(tender, Tender)
        self.assertEqual(tender.status, tender_constants.STATUS_DRAFT)
        self.assertIsNone(tender.published_at)
        messages = list(get_messages(final_response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            TenderCreateMultiStepView.get_success_message(
                TenderCreateMultiStepView, tenders_step_data, tender, is_draft=True
            ),
        )

    @patch("lemarche.www.tenders.views.add_to_contact_list", lambda user, type, tender: None)
    def test_tender_wizard_form_questions_list(self):
        initial_data_questions_list = [
            {"text": "Avez-vous suffisamment d'effectifs ? "},
            {"text": "Êtes-vous disponible tout l'été ? "},
        ]
        tenders_step_data = self._generate_fake_data_form(
            _step_2={"detail-questions_list": json.dumps(initial_data_questions_list)}  # json field
        )

        self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))
        tender: Tender = Tender.objects.get(title=tenders_step_data[0].get("general-title"))
        self.assertIsNotNone(tender)
        self.assertIsInstance(tender, Tender)
        self.assertEqual(tender.questions.count(), len(initial_data_questions_list))  # count is 2
        self.assertEqual(tender.questions_list()[0].get("text"), initial_data_questions_list[0].get("text"))

    @patch("lemarche.www.tenders.views.add_to_contact_list")
    def test_args_in_add_to_contact_list_call(self, mock_add_to_contact_list):
        """Test arguments in `add_to_contact_list` call"""
        tender, user = self.setup_mock_user_and_tender_creation()

        mock_add_to_contact_list.assert_called_once()
        args, kwargs = mock_add_to_contact_list.call_args

        # Check arguments like user, type, and source
        self.assertEqual(kwargs["user"], user)
        self.assertEqual(kwargs["type"], "signup")
        # Verify that `tender` is an instance of Tender
        self.assertIsInstance(
            kwargs.get("tender"), Tender, "Expected an instance of Tender for the 'tender' argument."
        )

    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.api.contacts_api.ContactsApi.create_contact")
    @patch("lemarche.utils.apis.api_brevo.sib_api_v3_sdk.CreateContact")
    def test_create_contact_call_has_user_buyer_attributes(self, mock_create_contact, mock_api_create_contact):
        """Test CreateContact call contains user buyer attributes"""
        mock_api_create_contact.return_value = CreateUpdateContactModel(id=123)
        tender, user = self.setup_mock_user_and_tender_creation(user=self.user_buyer)
        tender.save()

        mock_create_contact.assert_called_once()
        args, kwargs = mock_create_contact.call_args
        attributes = kwargs["attributes"]

        self.assertEqual(kwargs["email"], user.email)
        self.assertIn(settings.BREVO_CL_SIGNUP_BUYER_ID, kwargs["list_ids"])
        self.assertEqual(attributes["MONTANT_BESOIN_ACHETEUR"], tender.amount_int)
        self.assertEqual(attributes["TYPE_BESOIN_ACHETEUR"], tender.kind)
        self.assertIsNone(
            attributes["TYPE_VERTICALE_ACHETEUR"], "Expected TYPE_VERTICALE_ACHETEUR to be None for non-TALLY sources"
        )

    @patch("lemarche.www.tenders.views.add_to_contact_list", lambda user, type, tender: None)
    def test_send_tender_author_modification_request(self):
        """Test the tender updae url in 'send_tender_author_modification_request' function"""
        tender, _ = self.setup_mock_user_and_tender_creation(user=self.user_buyer)
        tender_update_url = reverse("tenders:update", kwargs={"slug": tender.slug})
        expected_url = f"/besoins/modifier/{tender.slug}"

        self.assertEqual(tender_update_url, expected_url)

    @patch("lemarche.www.tenders.views.add_to_contact_list", lambda user, type, tender: None)
    def test_reset_modification_request(self):
        """Test 'reset_modification_request' method to check tender fields updates"""
        tender, _ = self.setup_mock_user_and_tender_creation(user=self.user_buyer)
        tender.reset_modification_request()
        tender.save()

        self.assertEqual(tender.status, tender_constants.STATUS_SUBMITTED)
        self.assertEqual(tender.email_sent_for_modification, False)

    def test_create_tender_with_attachment(self):
        """Test create tender with attachments"""

        title = "Test Tender with Attachments"
        attachment_one = SimpleUploadedFile(
            name="document.pdf", content=b"file_content", content_type="application/pdf"
        )
        attachment_two = SimpleUploadedFile(
            name="specs.doc", content=b"specifications content", content_type="application/msword"
        )

        tenders_step_data = self._generate_fake_data_form(
            _step_1={"general-title": title},
            _step_2={"detail-attachment_one": attachment_one, "detail-attachment_two": attachment_two},
        )

        self.client.force_login(self.user_buyer)

        self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))

        tender = Tender.objects.get(title=title)
        self.assertTrue(tender.attachment_one)
        self.assertTrue(hasattr(tender.attachment_one, "file"))
        self.assertTrue(tender.attachment_two)
        self.assertTrue(hasattr(tender.attachment_two, "file"))
        self.assertFalse(tender.attachment_three)

        self.assertTrue(tender.attachment_one.name.lower().endswith(".pdf"))
        self.assertTrue(tender.attachment_two.name.lower().endswith(".doc"))

        self.assertTrue(default_storage.exists(tender.attachment_one.name))
        self.assertTrue(default_storage.exists(tender.attachment_two.name))

    def test_create_tender_with_attachment_error(self):
        """Test create tender with attachments"""
        attachment_one = SimpleUploadedFile(
            name="specs.txt", content=b"specifications content", content_type="text/plain"
        )

        tenders_step_data = self._generate_fake_data_form(
            _step_2={"detail-attachment_one": attachment_one},
        )

        self.client.force_login(self.user_buyer)
        try:
            self._check_every_step(tenders_step_data, final_redirect_page=reverse("siae:search_results"))
        except AssertionError as e:
            if "{'attachment_one': ['Format de fichier non[63 chars]DS']} != {}" in str(e):
                # handle the specific assertion error
                pass
            else:
                raise e


class TenderListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        perimeter = PerimeterFactory(post_codes=["43705"], insee_code="06", name="Auvergne-Rhône-Alpes")
        cls.siae_user_1 = UserFactory(kind=User.KIND_SIAE)
        cls.siae_1 = SiaeFactory()
        cls.siae_2 = SiaeFactory(post_code=perimeter.post_codes[0])
        cls.siae_user_2 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae_1])
        cls.user_buyer_1 = UserFactory(kind=User.KIND_BUYER, company_name="Entreprise Buyer")
        cls.user_buyer_2 = UserFactory(kind=User.KIND_BUYER)
        cls.user_partner = UserFactory(kind=User.KIND_PARTNER)
        cls.tender = TenderFactory(author=cls.user_buyer_1, perimeters=[perimeter])
        cls.tender_2 = TenderFactory(
            author=cls.user_buyer_1, deadline_date=timezone.now() - timedelta(days=5), perimeters=[perimeter]
        )
        cls.tender_3 = TenderFactory(
            author=cls.user_buyer_1,
            amount=tender_constants.AMOUNT_RANGE_100_150,
            accept_share_amount=False,
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
        cls.tender_4 = TenderFactory(
            author=cls.user_buyer_1, perimeters=[perimeter], kind=tender_constants.KIND_TENDER
        )
        cls.tendersiae_4_1 = TenderSiae.objects.create(
            tender=cls.tender_4, siae=cls.siae_1, email_send_date=timezone.now()
        )
        cls.tender_5 = TenderFactory(
            author=cls.user_buyer_1,
            perimeters=[perimeter],
            kind=tender_constants.KIND_TENDER,
            status=tender_constants.STATUS_REJECTED,
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
        self.assertEqual(len(response.context["tenders"]), 2)
        self.assertContains(response, self.tender_3.title)
        self.assertContains(response, self.tender_4.title)
        self.assertContains(response, "Entreprise Buyer")
        self.assertNotContains(response, "K€")  # !accept_share_amount
        self.assertNotContains(response, "2 prestataires ciblés")  # tender_3, but only visible to author
        self.assertNotContains(response, "1 prestataire intéressé")  # tender_3, but only visible to author

    def test_buyer_user_should_only_see_his_tenders(self):
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tenders"]), 5)
        self.assertContains(response, "2 prestataires ciblés")  # tender_3
        self.assertContains(response, "1 prestataire intéressé")  # tender_3
        self.assertNotContains(response, "Demandes reçues")
        self.assertNotContains(response, '<p class="fr-badge fr-badge--sm fr-badge--green-emeraude">Nouveau</p>')

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
        self.assertEqual(len(response.context["tenders"]), 2)
        # The badge in header, only one because one is outdated
        self.assertContains(
            response,
            'Demandes reçues&nbsp;<span class="fr-badge fr-badge--sm fr-ml-2v fr-badge--green-emeraude">1</span>',
        )
        # The badge in tender list
        self.assertContains(response, '<p class="fr-badge fr-badge--sm fr-badge--green-emeraude">Nouveau</p>', 1)

        # Open tender detail page
        detail_url = reverse("tenders:detail", kwargs={"slug": self.tender_4.slug})
        self.client.get(detail_url)

        # The badges have disappeared
        response = self.client.get(url)
        self.assertNotContains(
            response, 'Demandes reçues&nbsp;<span class="fr-badge fr-badge--sm fr-badge--green-emeraude">1</span>'
        )
        self.assertNotContains(response, '<p class="fr-badge fr-badge--sm fr-badge--green-emeraude">Nouveau</p>')

    def test_siae_user_should_only_see_filtered_kind(self):
        self.client.force_login(self.siae_user_2)
        url = reverse("tenders:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tenders"]), 2)
        self.assertContains(
            response,
            f'<option value="{tender_constants.KIND_QUOTE}">{tender_constants.KIND_QUOTE_DISPLAY}</option>',
            1,
            html=True,
        )
        self.assertContains(
            response,
            f'<option value="{tender_constants.KIND_TENDER}">{tender_constants.KIND_TENDER_DISPLAY} (1)</option>',
            1,
            html=True,
        )

        url = reverse("tenders:list")
        response = self.client.get(f"{url}?kind={tender_constants.KIND_TENDER}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tenders"]), 1)
        self.assertEqual(response.context["tenders"][0], self.tender_4)
        expected_option = (
            f'<option value="{tender_constants.KIND_TENDER}" selected>'
            f"{tender_constants.KIND_TENDER_DISPLAY} (1)</option>"
        )
        self.assertContains(response, expected_option, 1, html=True)

    def test_buyer_user_should_see_rejected_tenders(self):
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tenders"]), 5)
        self.assertContains(response, self.tender_5.title)
        self.assertContains(response, "Rejeté")


class TenderDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_1 = SiaeFactory(name="ZZ ESI")
        cls.siae_2 = SiaeFactory(name="ABC Insertion")
        cls.siae_3 = SiaeFactory(name="ABC Insertion bis")
        cls.siae_4 = SiaeFactory(name="ESAT 4")
        cls.siae_5 = SiaeFactory(name="ESAT 5")
        cls.siae_6 = SiaeFactory(name="ESAT 6")
        cls.siae_user_1 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae_1])
        cls.siae_user_2 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae_2, cls.siae_3])
        cls.siae_user_4 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae_4])
        cls.siae_user_5 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae_5])
        cls.siae_user_6 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae_6])
        cls.siae_user_without_siae = UserFactory(kind=User.KIND_SIAE)
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
            response_kind=[tender_constants.RESPONSE_KIND_EMAIL],
            sectors=[sector_1],
            location=grenoble_perimeter,
            status=tender_constants.STATUS_SENT,
            first_sent_at=timezone.now(),
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
        cls.tendersiae_1_4 = TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_4,
            source="EMAIL",
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
        )
        cls.tendersiae_1_5 = TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_5,
            source="EMAIL",
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
            detail_not_interested_click_date=timezone.now(),
        )
        TenderQuestionFactory(tender=cls.tender_1)
        cls.tender_2 = TenderFactory(
            author=cls.user_buyer_1,
            contact_company_name="Another company",
            status=tender_constants.STATUS_SENT,
            first_sent_at=timezone.now(),
        )
        cls.tender_3_response_is_anonymous = TenderFactory(
            kind=tender_constants.KIND_TENDER,
            author=cls.user_buyer_1,
            contact_company_name="Another company",
            status=tender_constants.STATUS_SENT,
            first_sent_at=timezone.now(),
            response_is_anonymous=True,
        )
        cls.tendersiae_3_1 = TenderSiae.objects.create(
            tender=cls.tender_3_response_is_anonymous,
            siae=cls.siae_1,
            source="EMAIL",
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
            detail_contact_click_date=timezone.now(),
        )
        cls.tendersiae_3_4 = TenderSiae.objects.create(
            tender=cls.tender_3_response_is_anonymous,
            siae=cls.siae_4,
            source="EMAIL",
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
        )
        cls.tendersiae_3_5 = TenderSiae.objects.create(
            tender=cls.tender_3_response_is_anonymous,
            siae=cls.siae_5,
            source="EMAIL",
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
            detail_not_interested_click_date=timezone.now(),
        )
        cls.tender_5 = TenderFactory(
            kind=tender_constants.KIND_TENDER,
            author=cls.user_buyer_1,
            status=tender_constants.STATUS_REJECTED,
        )

    def test_anyone_can_view_sent_tenders(self):
        for tender in Tender.objects.exclude(status=tender_constants.STATUS_REJECTED):
            # anonymous user
            url = reverse("tenders:detail", kwargs={"slug": tender.slug})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, tender.title)
            # users
            for user in User.objects.all():
                self.client.force_login(user)
                url = reverse("tenders:detail", kwargs={"slug": tender.slug})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_only_author_or_admin_can_view_non_sent_tender(self):
        tender_draft = TenderFactory(author=self.user_buyer_1, status=tender_constants.STATUS_DRAFT)
        tender_submitted = TenderFactory(
            author=self.user_buyer_1, status=tender_constants.STATUS_SUBMITTED, published_at=timezone.now()
        )
        tender_validated_but_not_sent = TenderFactory(
            author=self.user_buyer_1,
            status=tender_constants.STATUS_VALIDATED,
            published_at=timezone.now(),
            validated_at=timezone.now(),
        )
        for tender in [tender_draft, tender_submitted, tender_validated_but_not_sent]:
            # anonymous user
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

    def test_tender_unknown_should_return_404(self):
        url = reverse("tenders:detail", kwargs={"slug": f"{self.tender_1.slug}-bug"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

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

    def test_tender_attachment_display(self):
        self.tender_1.attachment_one = SimpleUploadedFile(
            name="specs.pdf", content=b"specifications content", content_type="application/pdf"
        )
        self.tender_1.attachment_two = SimpleUploadedFile(
            name="specs.doc", content=b"specifications content", content_type="application/msword"
        )
        self.tender_1.save()

        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Télécharger le document 1")
        self.assertContains(response, "Télécharger le document 2")
        self.assertNotContains(response, "Télécharger le document 3")

    def test_tender_constraints_display(self):
        # tender with constraints: section should be visible
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Comment répondre à cette demande ?")
        # tender without constraints: section should be hidden
        tender_2 = TenderFactory(author=self.user_buyer_2, constraints="")
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Comment répondre à cette demande ?")

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
        self.assertContains(response, tender_constants.ACCEPT_SHARE_AMOUNT_TRUE)
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
        self.assertContains(response, tender_constants.ACCEPT_SHARE_AMOUNT_FALSE)

    def test_tender_author_has_additional_stats(self):
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "3 prestataires ciblés")
        self.assertContains(response, "1 prestataire intéressé")
        # but hidden for non-author
        self.client.force_login(self.user_buyer_2)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "3 prestataires ciblés")
        self.assertNotContains(response, "1 prestataire intéressé")

    def test_admin_has_extra_info(self):
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        # anonymous user
        response = self.client.get(url)
        self.assertNotContains(response, "Informations Admin")
        # other users
        for user in [self.user_buyer_1, self.user_partner, self.siae_user_1]:
            self.client.force_login(user)
            response = self.client.get(url)
            self.assertNotContains(response, "Informations Admin")
        # admin
        self.client.force_login(self.user_admin)
        response = self.client.get(url)
        self.assertContains(response, "Informations Admin")

    def test_tender_contact_display(self):
        # anonymous user
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Cet appel d'offres vous intéresse ?")
        self.assertContains(response, "Cette demande ne vous intéresse pas ?")
        # siae user interested
        self.client.force_login(self.siae_user_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "Cet appel d'offres vous intéresse ?")
        self.assertContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, "votre intérêt a bien été signalé au client")
        self.assertNotContains(response, "Cette demande ne vous intéresse pas ?")
        # siae user not interested
        self.client.force_login(self.siae_user_5)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "Cet appel d'offres vous intéresse ?")
        self.assertNotContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, "Cette demande ne vous intéresse pas ?")
        self.assertContains(response, "Vous n'êtes pas intéressé par ce besoin")
        # siae user not concerned
        self.client.force_login(self.siae_user_6)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Cet appel d'offres vous intéresse ?")
        self.assertContains(response, "Cette demande ne vous intéresse pas ?")
        # siae user without siae
        self.client.force_login(self.siae_user_without_siae)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "veuillez d'abord vous")
        self.assertNotContains(response, "Cet appel d'offres vous intéresse ?")
        self.assertNotContains(response, "Cette demande ne vous intéresse pas ?")
        # author
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Coordonnées")
        self.assertNotContains(response, "Cet appel d'offres vous intéresse ?")
        self.assertNotContains(response, "Cette demande ne vous intéresse pas ?")

    def test_tender_response_is_anonymous_contact_display(self):
        # anonymous user
        url = reverse("tenders:detail", kwargs={"slug": self.tender_3_response_is_anonymous.slug})
        response = self.client.get(url)
        self.assertContains(response, "Cet appel d'offres vous intéresse ?")
        self.assertContains(response, "Cette demande ne vous intéresse pas ?")
        # siae user interested
        self.client.force_login(self.siae_user_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_3_response_is_anonymous.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "Cet appel d'offres vous intéresse ?")
        self.assertNotContains(response, "Contactez le client dès maintenant")
        self.assertContains(response, "Votre intérêt a été signalé au client")
        self.assertNotContains(response, "Cette demande ne vous intéresse pas ?")
        # siae user not interested
        self.client.force_login(self.siae_user_5)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_3_response_is_anonymous.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "Cet appel d'offres vous intéresse ?")
        self.assertNotContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, "Cette demande ne vous intéresse pas ?")
        self.assertContains(response, "Vous n'êtes pas intéressé par ce besoin")
        # siae user not concerned
        self.client.force_login(self.siae_user_6)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_3_response_is_anonymous.slug})
        response = self.client.get(url)
        self.assertContains(response, "Cet appel d'offres vous intéresse ?")
        self.assertContains(response, "Cette demande ne vous intéresse pas ?")
        # siae user without siae
        self.client.force_login(self.siae_user_without_siae)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_3_response_is_anonymous.slug})
        response = self.client.get(url)
        self.assertContains(response, "veuillez d'abord vous")
        self.assertNotContains(response, "Cet appel d'offres vous intéresse ?")
        # author
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_3_response_is_anonymous.slug})
        response = self.client.get(url)
        self.assertContains(response, "Coordonnées")
        self.assertNotContains(response, "Cet appel d'offres vous intéresse ?")

    def test_tender_outdated_contact_display(self):
        tender_2 = TenderFactory(
            kind=tender_constants.KIND_QUOTE,
            author=self.user_buyer_1,
            deadline_date=timezone.now() - timedelta(days=1),
        )
        TenderSiae.objects.create(tender=tender_2, siae=self.siae_1, detail_contact_click_date=timezone.now())
        # anonymous user
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "Répondre à cette opportunité")
        # siae user interested
        self.client.force_login(self.siae_user_1)
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, "Répondre à cette opportunité")
        # siae user not concerned
        self.client.force_login(self.siae_user_6)
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "Répondre à cette opportunité")
        # siae user without siae
        self.client.force_login(self.siae_user_without_siae)
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "veuillez d'abord vous")
        self.assertNotContains(response, "Répondre à cette opportunité")
        # author
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": tender_2.slug})
        response = self.client.get(url)
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
        self.assertNotContains(response, "Cet appel d'offres vous intéresse ?")
        # this one can!
        user_partner_2 = UserFactory(kind=User.KIND_PARTNER, can_display_tender_contact_details=True)
        self.client.force_login(user_partner_2)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertNotContains(response, "pour être mis en relation avec le client.")
        self.assertContains(response, "Contactez le client dès maintenant")
        self.assertNotContains(response, "Cet appel d'offres vous intéresse ?")

    def test_tender_contact_details_display(self):
        # tender_1 author
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Coordonnées")
        self.assertContains(response, self.tender_1.contact_email)  # RESPONSE_KIND_EMAIL
        self.assertNotContains(response, self.tender_1.contact_phone)
        self.assertNotContains(response, settings.TEAM_CONTACT_EMAIL)
        self.assertNotContains(response, "Cet appel d'offres vous intéresse ?")
        self.assertNotContains(response, "Lien partagé")
        # tender with same kind & different response_kind
        tender_2 = TenderFactory(
            kind=tender_constants.KIND_TENDER,
            author=self.user_buyer_1,
            response_kind=[tender_constants.RESPONSE_KIND_EMAIL, tender_constants.RESPONSE_KIND_EXTERNAL],
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
            response_kind=[tender_constants.RESPONSE_KIND_TEL, tender_constants.RESPONSE_KIND_EXTERNAL],
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
            response_kind=[tender_constants.RESPONSE_KIND_EXTERNAL],
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

    def test_update_tendersiae_stats_on_tender_view_with_siae_id(self):
        self.tender_1.siaes.add(self.siae_2)  # create new tendersiae
        self.assertEqual(self.tender_1.tendersiae_set.count(), 3 + 1)
        self.assertEqual(self.tender_1.tendersiae_set.first().siae, self.siae_2)
        self.assertIsNone(self.tender_1.tendersiae_set.first().user)
        self.assertIsNone(self.tender_1.tendersiae_set.first().email_link_click_date)
        self.assertIsNone(self.tender_1.tendersiae_set.first().detail_display_date)
        self.assertEqual(self.tender_1.tendersiae_set.last().siae, self.siae_1)
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().email_link_click_date)
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().detail_display_date)
        # first load anonymous user
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Déjà 3 prestataires inclusifs")
        # reload anonymous user with siae_id (already in tendersiae)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug}) + f"?siae_id={self.siae_2.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tender_1.tendersiae_set.count(), 4)  # unchanged
        siae_2_email_link_click_date = self.tender_1.tendersiae_set.first().email_link_click_date
        self.assertIsNotNone(siae_2_email_link_click_date)  # email_link_click_date updated
        self.assertIsNone(self.tender_1.tendersiae_set.first().user)
        self.assertIsNone(self.tender_1.tendersiae_set.first().detail_display_date)
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().detail_display_date)
        self.assertContains(response, "Déjà 4 prestataires inclusifs")
        self.assertNotContains(response, "contactez dès maintenant le client")
        # reload logged in user with siae_id (updates detail_display_date, but not email_link_click_date)
        self.client.force_login(self.siae_user_2)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug}) + f"?siae_id={self.siae_2.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tender_1.tendersiae_set.count(), 4)  # unchanged
        self.assertEqual(self.tender_1.tendersiae_set.first().email_link_click_date, siae_2_email_link_click_date)
        siae_2_detail_display_date = self.tender_1.tendersiae_set.first().detail_display_date
        self.assertIsNotNone(siae_2_detail_display_date)  # detail_display_date updated
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().detail_display_date)
        self.assertContains(response, "Déjà 4 prestataires inclusifs")
        self.assertNotContains(response, "contactez dès maintenant le client")
        # reload (doesn't update detail_display_date)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tender_1.tendersiae_set.count(), 4)  # unchanged
        self.assertEqual(self.tender_1.tendersiae_set.first().detail_display_date, siae_2_detail_display_date)
        self.assertContains(response, "Déjà 4 prestataires inclusifs")
        self.assertNotContains(response, "contactez dès maintenant le client")

    def test_update_tendersiae_stats_on_tender_view_with_siae_id_and_user_id(self):
        self.tender_1.siaes.add(self.siae_2)  # create new tendersiae
        self.assertEqual(self.tender_1.tendersiae_set.count(), 3 + 1)
        self.assertEqual(self.tender_1.tendersiae_set.first().siae, self.siae_2)
        self.assertIsNone(self.tender_1.tendersiae_set.first().user)
        self.assertIsNone(self.tender_1.tendersiae_set.first().email_link_click_date)
        self.assertIsNone(self.tender_1.tendersiae_set.first().detail_display_date)
        self.assertEqual(self.tender_1.tendersiae_set.last().siae, self.siae_1)
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().email_link_click_date)
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().detail_display_date)
        # first load anonymous user
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Déjà 3 prestataires inclusifs")
        # reload anonymous user with siae_id & user_id (already in tendersiae)
        url = (
            reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
            + f"?siae_id={self.siae_2.id}&user_id={self.siae_user_2.id}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tender_1.tendersiae_set.count(), 4)  # unchanged
        siae_2_email_link_click_date = self.tender_1.tendersiae_set.first().email_link_click_date
        self.assertIsNotNone(siae_2_email_link_click_date)  # email_link_click_date updated
        self.assertIsNotNone(self.tender_1.tendersiae_set.first().user)  # user updated
        self.assertIsNone(self.tender_1.tendersiae_set.first().detail_display_date)
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().detail_display_date)
        self.assertContains(response, "Déjà 4 prestataires inclusifs")
        self.assertNotContains(response, "contactez dès maintenant le client")

    def test_create_tendersiae_stats_on_tender_view_by_existing_user(self):
        self.tender_1.siaes.add(self.siae_2)
        self.assertEqual(self.tender_1.tendersiae_set.count(), 3 + 1)
        self.assertEqual(self.tender_1.tendersiae_set.first().siae, self.siae_2)
        self.assertIsNone(self.tender_1.tendersiae_set.first().email_link_click_date)
        self.assertIsNone(self.tender_1.tendersiae_set.first().detail_display_date)
        self.assertEqual(self.tender_1.tendersiae_set.last().siae, self.siae_1)
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().email_link_click_date)
        self.assertIsNotNone(self.tender_1.tendersiae_set.last().detail_display_date)
        # first load anonymous user
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Déjà 3 prestataires inclusifs")
        # first load, new user has already 1 siae contacted, we update only this one
        self.client.force_login(self.siae_user_2)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tender_1.tendersiae_set.count(), 3 + 1)
        self.assertEqual(self.tender_1.tendersiae_set.first().siae, self.siae_2)
        self.assertIsNone(self.tender_1.tendersiae_set.first().email_link_click_date)
        self.assertIsNotNone(self.tender_1.tendersiae_set.first().detail_display_date)
        self.assertContains(response, "Déjà 4 prestataires inclusifs")

    def test_create_tendersiae_stats_on_tender_view_by_new_user(self):
        self.assertEqual(self.tender_1.tendersiae_set.count(), 3)
        self.assertEqual(self.tender_1.tendersiae_set.first().siae, self.siae_5)
        self.assertIsNotNone(self.tender_1.tendersiae_set.first().detail_display_date)  # siae_5
        # first load anonymous user
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertContains(response, "Déjà 3 prestataires inclusifs")
        # first load, new user has 2 siaes
        self.client.force_login(self.siae_user_2)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tender_1.tendersiae_set.count(), 3 + 2)  # adds both siae_2 & siae_3
        self.assertEqual(self.tender_1.tendersiae_set.first().siae, self.siae_3)
        self.assertIsNone(self.tender_1.tendersiae_set.first().email_link_click_date)
        self.assertIsNotNone(self.tender_1.tendersiae_set.first().detail_display_date)
        self.assertContains(response, "Déjà 5 prestataires inclusifs")

    def test_badge_is_new_for_siaes(self):
        # assert the new badge is here
        tender_outdated = TenderFactory(
            kind=tender_constants.KIND_QUOTE,
            author=self.user_buyer_1,
            deadline_date=timezone.now() - timedelta(days=1),
        )
        self.client.force_login(self.siae_user_1)
        url = reverse("tenders:detail", kwargs={"slug": tender_outdated.slug})
        response = self.client.get(url)
        self.assertNotContains(response, '<p class="fr-badge fr-badge--sm fr-badge--green-emeraude">Nouveau</p>')

        tender_new = TenderFactory(
            kind=tender_constants.KIND_QUOTE,
            author=self.user_buyer_1,
            deadline_date=timezone.now() + timedelta(days=1),
        )
        self.client.force_login(self.siae_user_1)
        url = reverse("tenders:detail", kwargs={"slug": tender_new.slug})
        response = self.client.get(url)
        self.assertContains(response, '<p class="fr-badge fr-badge--sm fr-badge--green-emeraude">Nouveau</p>', 1)

        response = self.client.get(url)
        self.assertNotContains(response, '<p class="fr-badge fr-badge--sm fr-badge--green-emeraude">Nouveau</p>')

    def test_buyer_user_should_see_rejected_tender_in_detail_view(self):
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail", kwargs={"slug": self.tender_5.slug})
        response = self.client.get(url)
        self.assertContains(response, " a été rejeté.")


class TenderDetailContactClickStatViewTest(TestCase):
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
        cls.cta_message = "Cet appel d'offres vous intéresse ?"
        cls.cta_message_success = "contactez dès maintenant le client"
        cls.tender_detail_url = reverse("tenders:detail", kwargs={"slug": cls.tender.slug})
        cls.tender_contact_click_stat_url = reverse(
            "tenders:detail-contact-click-stat", kwargs={"slug": cls.tender.slug}
        )
        EmailGroup.objects.all().delete()  # to avoid duplicate key error
        TemplateTransactionalFactory(code="TENDERS_AUTHOR_SIAE_INTERESTED_1")

    def test_anonymous_user_cannot_notify_interested(self):
        response = self.client.get(self.tender_detail_url)
        self.assertContains(response, self.cta_message)
        self.assertContains(response, 'id="login_or_signup_siae_tender_modal"')
        self.assertNotContains(response, 'id="detail_contact_click_confirm_modal"')
        self.assertNotContains(response, self.cta_message_success)
        # anonymous user
        response = self.client.post(self.tender_contact_click_stat_url, data={})
        self.assertEqual(response.status_code, 403)

    def test_only_siae_user_or_with_siae_id_param_can_call_tender_contact_click(self):
        # forbidden
        for user in [self.user_buyer_1, self.user_buyer_2, self.user_partner, self.user_admin]:
            self.client.force_login(user)
            response = self.client.post(
                self.tender_contact_click_stat_url,
            )
            self.assertEqual(response.status_code, 403)
        # authorized
        for user in [self.siae_user_1, self.siae_user_2]:
            self.client.force_login(user)
            response = self.client.post(
                self.tender_contact_click_stat_url,
            )
            self.assertEqual(response.status_code, 302)
        # authorized with siae_id parameter
        self.client.logout()
        response = self.client.post(
            f"{self.tender_contact_click_stat_url}?siae_id={self.siae.id}",
        )
        self.assertEqual(response.status_code, 302)
        # forbidden because wrong siae_id parameter
        self.client.logout()
        response = self.client.post(
            f"{self.tender_contact_click_stat_url}?siae_id=test",
        )
        self.assertEqual(response.status_code, 403)

    def test_update_tendersiae_stats_on_tender_contact_click_with_authenticated_user(self):
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
        response = self.client.get(self.tender_detail_url)
        self.assertContains(response, self.cta_message)
        self.assertNotContains(response, 'id="login_or_signup_siae_tender_modal"')
        self.assertNotContains(response, self.cta_message_success)
        # click on button
        response = self.client.post(
            self.tender_contact_click_stat_url,
            data={
                # No questions from buyer
                "form-TOTAL_FORMS": 0,
                "form-INITIAL_FORMS": 0,
                "form-MIN_NUM_FORMS": 0,
                "form-MAX_NUM_FORMS": 1000,
            },
        )
        self.assertEqual(response.status_code, 302)
        siae_2_detail_contact_click_date = self.tender.tendersiae_set.first().detail_contact_click_date
        self.assertIsNotNone(siae_2_detail_contact_click_date)
        self.assertIsNone(self.tender.tendersiae_set.last().detail_contact_click_date)
        # reload page
        response = self.client.get(self.tender_detail_url)
        self.assertNotContains(response, self.cta_message)
        self.assertNotContains(response, 'id="login_or_signup_siae_tender_modal"')
        self.assertNotContains(response, 'id="detail_contact_click_confirm_modal"')
        self.assertContains(response, self.cta_message_success)
        # clicking again on the button doesn't update detail_contact_click_date
        # Note: button will disappear on reload anyway
        response = self.client.post(self.tender_contact_click_stat_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.tender.tendersiae_set.first().detail_contact_click_date, siae_2_detail_contact_click_date
        )

    def test_update_tendersiae_stats_on_tender_contact_click_with_siae_id(self):
        siae_2 = SiaeFactory(name="ABC Insertion")
        self.siae_user_2.siaes.add(siae_2)
        self.tender.siaes.add(siae_2)
        self.assertEqual(self.tender.tendersiae_set.count(), 2)
        self.assertEqual(self.tender.tendersiae_set.first().siae, siae_2)
        self.assertEqual(self.tender.tendersiae_set.last().siae, self.siae)
        self.assertIsNone(self.tender.tendersiae_set.first().detail_contact_click_date)
        self.assertIsNone(self.tender.tendersiae_set.last().detail_contact_click_date)
        # first load
        response = self.client.get(f"{self.tender_detail_url}?siae_id={siae_2.id}")
        self.assertNotContains(response, self.cta_message_success)
        # click on button
        response = self.client.post(
            f"{self.tender_contact_click_stat_url}?siae_id={siae_2.id}",
            data={
                # No questions from buyer
                "form-TOTAL_FORMS": 0,
                "form-INITIAL_FORMS": 0,
                "form-MIN_NUM_FORMS": 0,
                "form-MAX_NUM_FORMS": 1000,
            },
        )
        self.assertEqual(response.status_code, 302)
        siae_2_detail_contact_click_date = self.tender.tendersiae_set.first().detail_contact_click_date
        self.assertIsNotNone(siae_2_detail_contact_click_date)
        self.assertIsNone(self.tender.tendersiae_set.last().detail_contact_click_date)
        # reload page
        response = self.client.get(f"{self.tender_detail_url}?siae_id={siae_2.id}")
        self.assertContains(response, self.cta_message_success)
        # clicking again on the button doesn't update detail_contact_click_date
        # Note: button will disappear on reload anyway
        response = self.client.post(
            f"{self.tender_contact_click_stat_url}?siae_id={siae_2.id}",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.tender.tendersiae_set.first().detail_contact_click_date, siae_2_detail_contact_click_date
        )


class TenderDetailNotInterestedClickView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory(name="ZZ ESI")
        cls.siae_user = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae])
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER, company_name="Entreprise Buyer")
        cls.tender = TenderFactory(
            kind=tender_constants.KIND_TENDER,
            author=cls.user_buyer,
            amount=tender_constants.AMOUNT_RANGE_100_150,
            accept_share_amount=True,
            response_kind=[tender_constants.RESPONSE_KIND_EMAIL],
        )
        cls.tendersiae = TenderSiae.objects.create(
            tender=cls.tender,
            siae=cls.siae,
            source="EMAIL",
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
        )
        cls.cta_message = "Cette demande ne vous intéresse pas ?"
        cls.cta_message_success = "Vous n'êtes pas intéressé par ce besoin."
        cls.tender_detail_url = reverse("tenders:detail", kwargs={"slug": cls.tender.slug})
        cls.tender_not_interested_url = reverse(
            "tenders:detail-not-interested-click", kwargs={"slug": cls.tender.slug}
        )

    def test_anonymous_user_cannot_notify_not_interested(self):
        response = self.client.get(self.tender_detail_url)
        self.assertContains(response, self.cta_message)
        self.assertContains(response, 'id="login_or_signup_siae_tender_modal"')
        self.assertNotContains(response, 'id="detail_not_interested_click_confirm_modal"')
        self.assertNotContains(response, self.cta_message_success)
        # anonymous user
        response = self.client.post(self.tender_not_interested_url, data={})
        self.assertEqual(response.status_code, 403)

    def test_user_can_notify_not_interested_wish_with_authenticated_user(self):
        self.client.force_login(self.siae_user)
        # workflow
        response = self.client.get(self.tender_detail_url)
        self.assertContains(response, self.cta_message)
        self.assertNotContains(response, 'id="login_or_signup_siae_tender_modal"')
        self.assertContains(response, 'id="detail_not_interested_click_confirm_modal"')
        self.assertNotContains(response, self.cta_message_success)
        response = self.client.post(
            self.tender_not_interested_url, data={"detail_not_interested_feedback": "reason"}, follow=True
        )
        tendersiae = TenderSiae.objects.get(tender=self.tender, siae=self.siae)
        self.assertNotContains(response, self.cta_message)
        self.assertNotContains(response, 'id="detail_not_interested_click_confirm_modal"')
        self.assertContains(response, self.cta_message_success)
        self.assertIsNotNone(tendersiae.detail_not_interested_click_date)
        self.assertEqual(tendersiae.detail_not_interested_feedback, "reason")
        response = self.client.get(self.tender_detail_url)
        self.assertNotContains(response, self.cta_message)
        self.assertNotContains(response, 'id="detail_not_interested_click_confirm_modal"')
        self.assertContains(response, self.cta_message_success)

    def test_user_can_notify_not_interested_wish_with_siae_id_in_url(self):
        # wrong siae_id
        response = self.client.post(f"{self.tender_not_interested_url}?siae_id=999999", data={}, follow=True)
        self.assertEqual(response.status_code, 404)
        # workflow
        tendersiae = TenderSiae.objects.get(tender=self.tender, siae=self.siae)
        self.assertIsNone(tendersiae.detail_not_interested_click_date)
        response = self.client.post(f"{self.tender_not_interested_url}?siae_id={self.siae.id}", data={}, follow=True)
        self.assertNotContains(response, self.cta_message)
        self.assertNotContains(response, 'id="detail_not_interested_click_confirm_modal"')
        self.assertContains(response, self.cta_message_success)
        tendersiae = TenderSiae.objects.get(tender=self.tender, siae=self.siae)
        self.assertIsNotNone(tendersiae.detail_not_interested_click_date)
        response = self.client.get(f"{self.tender_detail_url}?siae_id={self.siae.id}")
        self.assertNotContains(response, self.cta_message)
        self.assertNotContains(response, 'id="detail_not_interested_click_confirm_modal"')
        self.assertContains(response, self.cta_message_success)

    def test_user_can_notify_not_interested_wish_with_siae_id_and_answer_in_url(self):
        # wrong siae_id
        response = self.client.post(
            f"{self.tender_not_interested_url}?siae_id=999999&not_interested=True", data={}, follow=True
        )
        self.assertEqual(response.status_code, 404)
        # workflow
        tendersiae = TenderSiae.objects.get(tender=self.tender, siae=self.siae)
        self.assertIsNone(tendersiae.detail_not_interested_click_date)
        response = self.client.post(
            f"{self.tender_not_interested_url}?siae_id={self.siae.id}&not_interested=True", data={}, follow=True
        )
        self.assertNotContains(response, self.cta_message)
        self.assertNotContains(response, 'dialog id="detail_not_interested_click_confirm_modal"')
        # self.assertContains(response, 'modal-siae show" id="detail_not_interested_click_confirm_modal"')
        # self.assertNotContains(response, self.cta_message_success)
        tendersiae = TenderSiae.objects.get(tender=self.tender, siae=self.siae)
        self.assertIsNotNone(tendersiae.detail_not_interested_click_date)
        response = self.client.get(f"{self.tender_detail_url}?siae_id={self.siae.id}")
        self.assertNotContains(response, self.cta_message)
        self.assertNotContains(response, 'id="detail_not_interested_click_confirm_modal"')
        self.assertContains(response, self.cta_message_success)


# TODO: this test doesn't work anymore. find a way to test logging post-email in non-prod environments?
# class TenderTasksTest(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         cls.tender = TenderFactory()

#     def test_send_email_for_feedbacks_set_log(self):
#         self.assertEqual(len(self.tender.logs), 0)
#         send_tenders_author_feedback_or_survey(self.tender, kind="feedback_30d")
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
        cls.siae_5 = SiaeFactory(name="Une dernière structure", kind=siae_constants.KIND_ETTI)
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
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
            detail_contact_click_date=timezone.now(),
        )
        cls.tendersiae_1_2 = TenderSiae.objects.create(
            tender=cls.tender_1, siae=cls.siae_2, email_send_date=timezone.now()
        )
        cls.tendersiae_1_3 = TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_3,
            email_send_date=timezone.now() - timedelta(hours=1),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
            detail_contact_click_date=timezone.now() - timedelta(hours=1),
        )
        cls.tendersiae_1_4 = TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_3,
            detail_display_date=timezone.now(),
        )
        cls.tendersiae_1_5 = TenderSiae.objects.create(
            tender=cls.tender_1,
            siae=cls.siae_5,
            detail_display_date=timezone.now(),
            detail_contact_click_date=timezone.now() - timedelta(hours=2),
        )
        cls.tendersiae_2_1 = TenderSiae.objects.create(
            tender=cls.tender_2,
            siae=cls.siae_2,
            email_send_date=timezone.now(),
            email_link_click_date=timezone.now(),
            detail_display_date=timezone.now(),
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

    def test_only_tender_author_can_view_tender_siae_interested_list(self):
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

    def test_tender_author_viewing_tender_siae_interested_list_should_update_stats(self):
        self.assertIsNone(self.tender_1.siae_list_last_seen_date)
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(Tender.objects.get(id=self.tender_1.id).siae_list_last_seen_date)

    def test_tender_siae_tabs(self):
        self.client.force_login(self.user_buyer_1)
        # ALL
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 3)  # email_send_date
        # VIEWED
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug, "status": "VIEWED"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 4)  # email_link_click_date or detail_display_date
        # INTERESTED
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug, "status": "INTERESTED"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 3)  # detail_contact_click_date

    def test_order_tender_siae_by_last_detail_contact_click_date(self):
        # TenderSiae are ordered by -created_at by default
        self.assertEqual(self.tender_1.tendersiae_set.first().id, self.tendersiae_1_5.id)
        # but TenderSiaeListView are ordered by -detail_contact_click_date
        self.client.force_login(self.user_buyer_1)
        url = reverse("tenders:detail-siae-list", kwargs={"slug": self.tender_1.slug, "status": "INTERESTED"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["siaes"]), 3)  # detail_contact_click_date
        self.assertEqual(response.context["siaes"][0].id, self.tendersiae_1_1.siae.id)

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
        cls.user_buyer_1_sesame_query_string = sesame_get_query_string(cls.user_buyer_1)
        cls.url = reverse("tenders:detail-survey-transactioned", kwargs={"slug": cls.tender.slug})

    def test_anonymous_user_cannot_call_tender_survey_transactioned(self):
        response = self.client.post(self.url)
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
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 403)
        # logout the last user to be sure
        self.client.logout()
        # authorized
        user_sesame_query_string = sesame_get_query_string(self.user_buyer_1)
        url = self.url + user_sesame_query_string
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        # full form displayed (but should never happen)

    def test_update_tender_stats_on_tender_survey_transactioned_answer_true(self):
        t = Tender.objects.get(id=self.tender.id)
        self.assertIsNone(t.survey_transactioned_answer)
        self.assertIsNone(t.siae_transactioned)
        self.assertIsNone(t.siae_transactioned_source)
        self.assertIsNone(t.siae_transactioned_last_updated)
        # load with answer True: partial form
        url = f"{self.url}{self.user_buyer_1_sesame_query_string}&answer={constants.YES}"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        t = Tender.objects.get(id=self.tender.id)
        self.assertEqual(t.survey_transactioned_answer, constants.YES)
        self.assertTrue(t.siae_transactioned)
        self.assertEqual(
            t.siae_transactioned_source,
            tender_constants.TENDER_SIAE_TRANSACTIONED_SOURCE_AUTHOR,
        )
        self.assertIsNotNone(t.siae_transactioned_last_updated)
        # fill in form
        response = self.client.post(
            url, data={"survey_transactioned_amount": 1000, "survey_transactioned_feedback": "Feedback"}, follow=True
        )
        self.assertEqual(response.status_code, 200)  # redirect
        t = Tender.objects.get(id=self.tender.id)
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Merci pour votre réponse")
        self.assertEqual(t.survey_transactioned_answer, constants.YES)
        self.assertEqual(t.survey_transactioned_amount, 1000)
        # reload with new answer, ignore changes and redirect
        url = f"{self.url}{self.user_buyer_1_sesame_query_string}&answer={constants.NO}"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        t = Tender.objects.get(id=self.tender.id)
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Votre réponse a déjà été prise en compte")
        self.assertEqual(t.survey_transactioned_answer, constants.YES)
        self.assertTrue(t.siae_transactioned)

    def test_update_tender_stats_on_tender_survey_transactioned_answer_false(self):
        # load with answer False: partial form
        url = f"{self.url}{self.user_buyer_1_sesame_query_string}&answer={constants.NO}"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        t = Tender.objects.get(id=self.tender.id)
        self.assertEqual(t.survey_transactioned_answer, constants.NO)
        self.assertFalse(t.siae_transactioned)
        # fill in form
        response = self.client.post(url, data={"survey_transactioned_feedback": "Feedback"}, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        t = Tender.objects.get(id=self.tender.id)
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Merci pour votre réponse")
        self.assertEqual(t.survey_transactioned_answer, constants.NO)
        self.assertIsNone(t.survey_transactioned_amount)
        # reload with new answer, ignore changes
        url = f"{self.url}{self.user_buyer_1_sesame_query_string}&answer={constants.YES}"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        t = Tender.objects.get(id=self.tender.id)
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Votre réponse a déjà été prise en compte")
        self.assertEqual(t.survey_transactioned_answer, constants.NO)
        self.assertFalse(t.siae_transactioned)

    def test_update_tender_stats_on_tender_survey_transactioned_answer_dont_know(self):
        # load with answer ?: partial form
        url = f"{self.url}{self.user_buyer_1_sesame_query_string}&answer={constants.DONT_KNOW}"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        t = Tender.objects.get(id=self.tender.id)
        self.assertEqual(t.survey_transactioned_answer, constants.DONT_KNOW)
        self.assertIsNone(t.siae_transactioned)
        # fill in form
        response = self.client.post(url, data={"survey_transactioned_feedback": "Feedback"}, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        t = Tender.objects.get(id=self.tender.id)
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Merci pour votre réponse")
        self.assertEqual(t.survey_transactioned_answer, constants.DONT_KNOW)
        self.assertIsNone(t.survey_transactioned_amount)
        # reload with new answer, update
        url = f"{self.url}{self.user_buyer_1_sesame_query_string}&answer={constants.YES}"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        t = Tender.objects.get(id=self.tender.id)
        self.assertNotContains(response, "Votre réponse a déjà été prise en compte")
        self.assertEqual(t.survey_transactioned_answer, constants.YES)
        self.assertTrue(t.siae_transactioned)


class TenderDetailSiaeSurveyTransactionedViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory(name="ZZ ESI")
        cls.siae_user_1 = UserFactory(kind=User.KIND_SIAE, siaes=[cls.siae])
        cls.siae_user_2 = UserFactory(kind=User.KIND_SIAE)
        cls.user_buyer_1 = UserFactory(kind=User.KIND_BUYER)
        cls.user_buyer_2 = UserFactory(kind=User.KIND_BUYER)
        cls.user_partner = UserFactory(kind=User.KIND_PARTNER)
        cls.user_admin = UserFactory(kind=User.KIND_ADMIN)
        cls.tender = TenderFactory(kind=tender_constants.KIND_TENDER, author=cls.user_buyer_1)
        cls.tendersiae = TenderSiae.objects.create(tender=cls.tender, siae=cls.siae)
        cls.url = reverse(
            "tenders:detail-siae-survey-transactioned", kwargs={"slug": cls.tender.slug, "siae_slug": cls.siae.slug}
        )
        cls.user_siae_1_sesame_query_string = sesame_get_query_string(cls.siae_user_1)

    def test_anonymous_user_cannot_call_tender_siae_survey_transactioned(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_only_tender_author_with_sesame_token_can_call_tender_siae_survey_transactioned(self):
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
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 403)
        # logout the last user to be sure
        self.client.logout()
        # authorized
        user_sesame_query_string = sesame_get_query_string(self.siae_user_1)
        url = self.url + user_sesame_query_string
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        # full form displayed (but should never happen)

    def test_update_tender_stats_on_tender_siae_survey_transactioned_answer_true(self):
        ts = TenderSiae.objects.get(tender=self.tender, siae=self.siae)
        self.assertIsNone(ts.survey_transactioned_answer)
        self.assertIsNone(ts.transactioned)
        self.assertIsNone(ts.transactioned_source)
        self.assertIsNone(ts.tender.siae_transactioned)
        self.assertIsNone(ts.tender.siae_transactioned_source)
        self.assertIsNone(ts.tender.siae_transactioned_last_updated)
        # load with answer 'True': partial form
        url = self.url + self.user_siae_1_sesame_query_string + "&answer=True"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        ts = TenderSiae.objects.get(tender=self.tender, siae=self.siae)
        self.assertTrue(ts.survey_transactioned_answer)
        self.assertTrue(ts.transactioned)
        self.assertEqual(
            ts.transactioned_source,
            tender_constants.TENDER_SIAE_TRANSACTIONED_SOURCE_SIAE,
        )
        self.assertTrue(ts.tender.siae_transactioned)
        self.assertEqual(ts.tender.siae_transactioned_source, tender_constants.TENDER_SIAE_TRANSACTIONED_SOURCE_SIAE)
        self.assertIsNotNone(ts.tender.siae_transactioned_last_updated)
        # fill in form
        response = self.client.post(
            url, data={"survey_transactioned_amount": 1000, "survey_transactioned_feedback": "Feedback"}, follow=True
        )
        self.assertEqual(response.status_code, 200)  # redirect
        ts = TenderSiae.objects.get(tender=self.tender, siae=self.siae)
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Merci pour votre réponse")
        self.assertTrue(ts.survey_transactioned_answer)
        self.assertEqual(ts.survey_transactioned_amount, 1000)
        # reload with answer, ignore changes and redirect
        url = self.url + self.user_siae_1_sesame_query_string + "&answer=False"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        ts = TenderSiae.objects.get(tender=self.tender, siae=self.siae)
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Votre réponse a déjà été prise en compte")
        self.assertTrue(ts.survey_transactioned_answer)

    def test_update_tender_stats_on_tender_siae_survey_transactioned_answer_false(self):
        # load with answer 'False': partial form
        url = self.url + self.user_siae_1_sesame_query_string + "&answer=False"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TenderSiae.objects.get(tender=self.tender, siae=self.siae).survey_transactioned_answer)
        # fill in form
        response = self.client.post(url, data={"survey_transactioned_feedback": "Feedback"}, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Merci pour votre réponse")
        self.assertFalse(TenderSiae.objects.get(tender=self.tender, siae=self.siae).survey_transactioned_answer)
        self.assertIsNone(TenderSiae.objects.get(tender=self.tender, siae=self.siae).survey_transactioned_amount)
        # reload with answer, ignore changes
        url = self.url + self.user_siae_1_sesame_query_string + "&answer=True"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)  # redirect
        self.assertRedirects(response, reverse("tenders:detail", kwargs={"slug": self.tender.slug}))
        self.assertContains(response, "Votre réponse a déjà été prise en compte")
        self.assertFalse(TenderSiae.objects.get(tender=self.tender, siae=self.siae).survey_transactioned_answer)


class TenderQuestionAnswerTestCase(TestCase):
    """Tests for different kind of siaes answering questions made by the creator of a tender that matched the siaes"""

    def setUp(self):
        sector = SectorFactory()
        perimeter = PerimeterFactory()

        self.siae_1 = SiaeFactory()
        self.siae_2 = SiaeFactory()
        SiaeActivityFactory(siae=self.siae_1, sectors=[sector], locations=[perimeter])
        SiaeActivityFactory(siae=self.siae_2, sectors=[sector], locations=[perimeter])

        self.tender = TenderFactory(sectors=[sector], perimeters=[perimeter])
        self.q1 = TenderQuestionFactory(tender=self.tender)
        self.q2 = TenderQuestionFactory(tender=self.tender)

        other_matched_tender_siae_1 = SiaeFactory()
        other_tender = TenderFactory()

        TenderQuestionFactory(tender=other_tender)
        TenderQuestionFactory(tender=other_tender)

        # Simulate matching process
        TenderSiaeFactory(tender=self.tender, siae=self.siae_1)
        TenderSiaeFactory(tender=self.tender, siae=self.siae_2)
        TenderSiaeFactory(tender=other_tender, siae=other_matched_tender_siae_1)

        TemplateTransactionalFactory(name="gfdg", code="TENDERS_AUTHOR_SIAE_INTERESTED_1")
        TemplateTransactionalFactory(name="gfdg", code="TENDERS_AUTHOR_SIAE_INTERESTED_2")

    def test_with_authenticated_user_single_siae(self):
        url = reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug})
        user = UserFactory()
        self.siae_1.users.add(user)
        self.client.force_login(user)

        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)

        payload = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-answer": "SOMETHING",
            "form-0-question": self.q1.id,
            "form-1-answer": "ELSE",
            "form-1-question": self.q2.id,
        }
        response_post = self.client.post(url, data=payload)

        self.assertEqual(response_post.status_code, 302)

        self.assertEqual(QuestionAnswer.objects.all().count(), 2)

        self.assertEqual(QuestionAnswer.objects.get(siae=self.siae_1, question=self.q1).answer, "SOMETHING")
        self.assertEqual(QuestionAnswer.objects.get(siae=self.siae_1, question=self.q2).answer, "ELSE")

    def test_with_authenticated_user_multiple_siae(self):
        """A user has 2 Siae that matched the same tender."""
        url = reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug})

        user = UserFactory()
        self.siae_1.users.add(user)
        self.siae_2.users.add(user)
        non_matched_siae = SiaeFactory()
        non_matched_siae.users.add(user)
        self.client.force_login(user)

        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        # Only the 2 matched siae are grouped in the form, not the third that didn't match
        self.assertEqual(len(response_get.context["questions_formset"]), 2)

        payload = {
            "siae": [self.siae_1.id, self.siae_2.id],
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            # Answers for all selected Siaes
            "form-0-answer": "SOMETHING",
            "form-0-question": self.q1.id,
            "form-1-answer": "ELSE",
            "form-1-question": self.q2.id,
        }
        response_post = self.client.post(url, data=payload)

        self.assertEqual(response_post.status_code, 302)

        self.assertEqual(QuestionAnswer.objects.all().count(), 4)

        self.assertEqual(QuestionAnswer.objects.get(siae=self.siae_1, question=self.q1).answer, "SOMETHING")
        self.assertEqual(QuestionAnswer.objects.get(siae=self.siae_1, question=self.q2).answer, "ELSE")
        self.assertEqual(QuestionAnswer.objects.get(siae=self.siae_2, question=self.q1).answer, "SOMETHING")
        self.assertEqual(QuestionAnswer.objects.get(siae=self.siae_2, question=self.q2).answer, "ELSE")

        self.assertTrue(TenderSiae.objects.get(tender=self.tender, siae=self.siae_1).detail_contact_click_date)
        self.assertTrue(TenderSiae.objects.get(tender=self.tender, siae=self.siae_2).detail_contact_click_date)

    def test_with_authenticated_user_multiple_siae_only_one_selected(self):
        """A user has 2 Siae that matched the same tender, but choose to answer for only one of them
        with selecting only one in the siae select"""
        url = reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug})

        user = UserFactory()
        self.siae_1.users.add(user)
        self.siae_2.users.add(user)
        self.client.force_login(user)

        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        # Only the 2 matched siae are grouped in the form, not the third that didn't match
        self.assertEqual(len(response_get.context["questions_formset"]), 2)

        payload = {
            "siae": [self.siae_1.id],
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            # Answers for all selected Siaes
            "form-0-answer": "SOMETHING",
            "form-0-question": self.q1.id,
            "form-1-answer": "ELSE",
            "form-1-question": self.q2.id,
        }
        response_post = self.client.post(url, data=payload)

        self.assertEqual(response_post.status_code, 302)

        self.assertEqual(QuestionAnswer.objects.all().count(), 2)

        self.assertEqual(QuestionAnswer.objects.get(siae=self.siae_1, question=self.q1).answer, "SOMETHING")
        self.assertEqual(QuestionAnswer.objects.get(siae=self.siae_1, question=self.q2).answer, "ELSE")

        # Only the selected Siae have a detail_contact_click_date
        self.assertTrue(TenderSiae.objects.get(tender=self.tender, siae=self.siae_1).detail_contact_click_date)
        self.assertFalse(TenderSiae.objects.get(tender=self.tender, siae=self.siae_2).detail_contact_click_date)

    def test_with_anonymous_user_single_siae(self):
        """Unauthenticated users should also be granted the right to answers questions"""
        url = (
            reverse("tenders:detail-contact-click-stat", kwargs={"slug": self.tender.slug})
            + f"?siae_id={self.siae_1.id}"
        )

        # Assert no answers created yet
        self.assertEqual(QuestionAnswer.objects.count(), 0)

        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)

        payload = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-answer": "SOMETHING",
            "form-0-question": self.q1.id,
            "form-1-answer": "ELSE",
            "form-1-question": self.q2.id,
        }
        response_post = self.client.post(url, data=payload)

        self.assertEqual(response_post.status_code, 302)

        self.assertEqual(QuestionAnswer.objects.all().count(), 2)
        self.assertEqual(QuestionAnswer.objects.first().answer, "SOMETHING")
        self.assertEqual(QuestionAnswer.objects.last().answer, "ELSE")


class TenderSiaeDownloadViewTestCase(TestCase):

    def setUp(self):
        self.user = UserFactory(kind=User.KIND_BUYER)

        siae_1 = SiaeFactory(name="siae_1")
        siae_2 = SiaeFactory(name="siae_2")
        siae_3 = SiaeFactory(name="siae_3")

        self.tender = TenderFactory()
        # INTERESTED
        TenderSiaeFactory(
            tender=self.tender,
            siae=siae_1,
            detail_display_date=timezone.now(),
            detail_contact_click_date=timezone.now(),
        )
        TenderSiaeFactory(
            tender=self.tender,
            siae=siae_2,
            detail_display_date=timezone.now(),
            detail_contact_click_date=timezone.now(),
        )
        # VIEWED
        TenderSiaeFactory(tender=self.tender, siae=siae_3, detail_display_date=timezone.now())

        q1 = TenderQuestionFactory(tender=self.tender, text="question_1_title")
        q2 = TenderQuestionFactory(tender=self.tender, text="question_2_title")

        QuestionAnswerFactory(question=q1, siae=siae_1, answer="answer_for_q1_from_siae_1")
        QuestionAnswerFactory(question=q2, siae=siae_1, answer="answer_for_q2_from_siae_1")
        QuestionAnswerFactory(question=q1, siae=siae_2, answer="answer_for_q1_from_siae_2")
        QuestionAnswerFactory(question=q2, siae=siae_2, answer="answer_for_q2_from_siae_2")

        self.client.force_login(self.user)

    def test_filtering(self):

        with self.subTest(
            status="TARGETED"
        ):  # That status is implicit, it switches to targeted when no status is given
            response = self.client.get(
                reverse("tenders:download-siae-list", kwargs={"slug": self.tender.slug})
                + "?tendersiae_status=&format=csv"
            )
            content = response.content.decode("utf-8")
            csv_reader = csv.DictReader(content.splitlines())
            rows = list(csv_reader)
            self.assertEqual(len(rows), 0)

        with self.subTest(status="VIEWED"):
            response = self.client.get(
                reverse("tenders:download-siae-list", kwargs={"slug": self.tender.slug})
                + "?tendersiae_status=VIEWED&format=csv"
            )
            content = response.content.decode("utf-8")
            csv_reader = csv.DictReader(content.splitlines())
            rows = list(csv_reader)
            self.assertEqual(len(rows), 3)

        with self.subTest(status="INTERESTED"):
            response = self.client.get(
                reverse("tenders:download-siae-list", kwargs={"slug": self.tender.slug})
                + "?tendersiae_status=INTERESTED&format=csv"
            )
            content = response.content.decode("utf-8")
            csv_reader = csv.DictReader(content.splitlines())
            rows = list(csv_reader)
            self.assertEqual(len(rows), 2)

    def test_download_csv(self):
        response = self.client.get(
            reverse("tenders:download-siae-list", kwargs={"slug": self.tender.slug})
            + "?format=csv&tendersiae_status=INTERESTED"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="{self.tender.slug}-liste-structures-interessees.csv"',
        )

        # Parse CSV content into dict
        content = response.content.decode("utf-8")
        csv_reader = csv.DictReader(content.splitlines())
        rows = list(csv_reader)
        self.assertEqual(len(rows), 2)  # 2 siaes in the tender

        self.assertEqual(rows[0]["Raison sociale"], "siae_1")
        self.assertEqual(rows[0].get("question_1_title"), "answer_for_q1_from_siae_1")
        self.assertEqual(rows[0].get("question_2_title"), "answer_for_q2_from_siae_1")

        self.assertEqual(rows[1]["Raison sociale"], "siae_2")
        self.assertEqual(rows[1].get("question_1_title"), "answer_for_q1_from_siae_2")
        self.assertEqual(rows[1].get("question_2_title"), "answer_for_q2_from_siae_2")

    def test_download_xlsx(self):
        response = self.client.get(
            reverse("tenders:download-siae-list", kwargs={"slug": self.tender.slug})
            + "?format=xlsx&tendersiae_status=INTERESTED"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="{self.tender.slug}-liste-structures-interessees.xlsx"',
        )

        # Load file from response into a workbook
        file_content = BytesIO(response.content)
        workbook = openpyxl.load_workbook(file_content)
        sheet = workbook.active

        self.assertEqual(sheet["A1"].value, "Raison sociale")
        self.assertEqual(sheet["A2"].value, "siae_1")
        self.assertEqual(sheet["A3"].value, "siae_2")

        self.assertEqual(sheet["X1"].value, "question_1_title")
        self.assertEqual(sheet["X2"].value, "answer_for_q1_from_siae_1")
        self.assertEqual(sheet["X3"].value, "answer_for_q1_from_siae_2")

        self.assertEqual(sheet["Y1"].value, "question_2_title")
        self.assertEqual(sheet["Y2"].value, "answer_for_q2_from_siae_1")
        self.assertEqual(sheet["Y3"].value, "answer_for_q2_from_siae_2")
