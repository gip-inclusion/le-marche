import logging
import os
from datetime import datetime
from io import StringIO
from unittest.mock import patch

import factory
from django.core.management import call_command
from django.db.models import signals
from django.test import TestCase, TransactionTestCase

from lemarche.networks.factories import NetworkFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeActivityFactory, SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.users.factories import UserFactory


class SyncWithEmploisInclusionCommandTest(TransactionTestCase):
    def setUp(self):
        logging.disable(logging.DEBUG)  # setting in tests disables all logging by default

    @patch("lemarche.utils.apis.api_emplois_inclusion.get_siae_list")
    def test_sync_with_emplois_inclusion_create_new_siae(self, mock_get_siae_list):
        # Mock API response for a new SIAE
        mock_get_siae_list.return_value = [
            {
                "id": 123,
                "siret": "12345678901234",
                "naf": "8899B",
                "kind": "EI",
                "name": "New SIAE",
                "brand": "",
                "phone": "",
                "email": "",
                "website": "",
                "description": "",
                "address_line_1": "1 rue Test",
                "address_line_2": "",
                "post_code": "37000",
                "city": "Tours",
                "department": "37",
                "source": "ASP",
                "latitude": 0,
                "longitude": 0,
                "convention_is_active": True,
                "convention_asp_id": 0,
                "admin_name": "",
                "admin_email": "",
            }
        ]

        # Verify SIAE doesn't exist
        self.assertEqual(Siae.objects.count(), 0)

        # Run command
        os.environ["API_EMPLOIS_INCLUSION_TOKEN"] = "test"
        with self.assertNoLogs("lemarche.siaes.management.commands.sync_with_emplois_inclusion"):
            call_command("sync_with_emplois_inclusion", stdout=StringIO())

        # Verify SIAE was created
        self.assertEqual(Siae.objects.count(), 1)
        siae = Siae.objects.first()
        self.assertEqual(siae.siret, "12345678901234")
        self.assertEqual(siae.name, "New SIAE")
        self.assertEqual(siae.brand, "")

    @patch("lemarche.utils.apis.api_emplois_inclusion.get_siae_list")
    def test_sync_with_emplois_inclusion_update_existing_siae(self, mock_get_siae_list):
        # Create existing SIAE
        existing_siae = SiaeFactory(c1_id=123, siret="12345678901234", kind=siae_constants.KIND_EI)

        return_value = [
            {
                "id": 123,
                "siret": "12345678901234",
                "naf": "8899B",
                "kind": "EI",
                "name": "New SIAE",
                "brand": "Updated Name",
                "phone": "",
                "email": "",
                "website": "",
                "description": "",
                "address_line_1": "2 rue Test",
                "address_line_2": "",
                "post_code": "69001",
                "city": "Lyon",
                "department": "69",
                "source": "ASP",
                "latitude": 0,
                "longitude": 0,
                "convention_is_active": True,
                "convention_asp_id": 0,
                "admin_name": "",
                "admin_email": "",
            }
        ]

        # Mock API response with updated data
        mock_get_siae_list.return_value = return_value

        # Run command
        os.environ["API_EMPLOIS_INCLUSION_TOKEN"] = "test"
        with self.assertNoLogs("lemarche.siaes.management.commands.sync_with_emplois_inclusion"):
            call_command("sync_with_emplois_inclusion", stdout=StringIO())

        # Verify SIAE was updated
        self.assertEqual(Siae.objects.count(), 1)
        updated_siae = Siae.objects.get(id=existing_siae.id)
        self.assertEqual(updated_siae.brand, "Updated Name")  # update first time
        self.assertEqual(updated_siae.address, "2 rue Test")
        self.assertEqual(updated_siae.post_code, "69001")
        self.assertEqual(updated_siae.city, "Lyon")
        self.assertEqual(updated_siae.department, "69")

        # Mock API response with updated data for the same SIAE with different brand name
        return_value[0]["brand"] = "Other Name"
        mock_get_siae_list.return_value = return_value

        # Run command
        with self.assertNoLogs("lemarche.siaes.management.commands.sync_with_emplois_inclusion"):
            call_command("sync_with_emplois_inclusion", stdout=StringIO())

        # Verify SIAE was updated
        self.assertEqual(Siae.objects.count(), 1)
        updated_siae.refresh_from_db()
        self.assertEqual(updated_siae.brand, "Updated Name")  # Brand name can only be updated once

    @patch("lemarche.utils.apis.api_emplois_inclusion.get_siae_list")
    def test_sync_with_emplois_inclusion_with_duplicate_brand_name_on_create(self, mock_get_siae_list):
        # Create existing SIAE with the same brand name
        siae = SiaeFactory(siret="98765432101233", brand="Duplicate Brand", kind=siae_constants.KIND_EI)

        # Mock API response with duplicate brand name
        mock_get_siae_list.return_value = [
            {
                "id": 123,
                "siret": "12345678901234",
                "naf": "8899B",
                "kind": "EI",
                "name": "New SIAE",
                "brand": "Duplicate Brand",
                "phone": "",
                "email": "",
                "website": "",
                "description": "",
                "address_line_1": "1 rue Test",
                "address_line_2": "",
                "post_code": "37000",
                "city": "Tours",
                "department": "37",
                "source": "ASP",
                "latitude": 0,
                "longitude": 0,
                "convention_is_active": True,
                "convention_asp_id": 0,
                "admin_name": "",
                "admin_email": "",
            }
        ]

        # Run command (should not raise exception)
        os.environ["API_EMPLOIS_INCLUSION_TOKEN"] = "test"

        with self.subTest(existing_siae_is_delisted=False):
            with self.assertLogs(
                "lemarche.siaes.management.commands.sync_with_emplois_inclusion", level="ERROR"
            ) as log:
                call_command("sync_with_emplois_inclusion", stdout=StringIO())

            # Verify warning was logged
            self.assertIn("Brand name is already used by another live SIAE during creation", log.output[0])

            # Verify only one SIAE exist, not duplicate
            self.assertEqual(Siae.objects.count(), 1)

        with self.subTest(existing_siae_is_delisted=True):
            # Delisted SIAE should not be taken into account
            siae.is_delisted = True
            siae.save()
            with self.assertNoLogs("lemarche.siaes.management.commands.sync_with_emplois_inclusion"):
                call_command("sync_with_emplois_inclusion", stdout=StringIO())

            self.assertEqual(Siae.objects.count(), 2)
            self.assertEqual(Siae.objects.exclude(pk=siae.pk).first().name, "New SIAE")

    @patch("lemarche.utils.apis.api_emplois_inclusion.get_siae_list")
    def test_sync_with_emplois_inclusion_with_duplicate_brand_name_on_update(self, mock_get_siae_list):
        # Create existing SIAE with the same brand name
        siae = SiaeFactory(siret="98765432101233", brand="Duplicate Brand", kind=siae_constants.KIND_EI)
        SiaeFactory(siret="98765432101234", c1_id=123, kind=siae_constants.KIND_EI)

        self.assertEqual(Siae.objects.count(), 2)

        # Mock API response with duplicate brand name
        mock_get_siae_list.return_value = [
            {
                "id": 123,
                "siret": "12345678901234",
                "naf": "8899B",
                "kind": "EI",
                "name": "New SIAE",
                "brand": "Duplicate Brand",
                "phone": "",
                "email": "",
                "website": "",
                "description": "",
                "address_line_1": "1 rue Test",
                "address_line_2": "",
                "post_code": "37000",
                "city": "Tours",
                "department": "37",
                "source": "ASP",
                "latitude": 0,
                "longitude": 0,
                "convention_is_active": True,
                "convention_asp_id": 0,
                "admin_name": "",
                "admin_email": "",
            },
            {
                "id": 124,
                "siret": "12345678901235",
                "naf": "8899B",
                "kind": "EI",
                "name": "Other New SIAE",
                "brand": "",
                "phone": "",
                "email": "",
                "website": "",
                "description": "",
                "address_line_1": "1 rue Test",
                "address_line_2": "",
                "post_code": "37000",
                "city": "Tours",
                "department": "37",
                "source": "ASP",
                "latitude": 0,
                "longitude": 0,
                "convention_is_active": True,
                "convention_asp_id": 0,
                "admin_name": "",
                "admin_email": "",
            },
        ]

        # Run command (should not raise exception)
        os.environ["API_EMPLOIS_INCLUSION_TOKEN"] = "test"

        with self.subTest(existing_siae_is_delisted=False):
            with self.assertLogs(
                "lemarche.siaes.management.commands.sync_with_emplois_inclusion", level="ERROR"
            ) as log:
                call_command("sync_with_emplois_inclusion", stdout=StringIO())

            # Verify warning was logged
            self.assertIn("Brand name is already used by another live SIAE during update", log.output[0])

            # Verify both SIAEs exist
            self.assertEqual(Siae.objects.count(), 3)
            self.assertEqual(Siae.objects.filter(brand="Duplicate Brand").count(), 1)

            self.assertEqual(Siae.objects.filter(name="Other New SIAE").count(), 1)  # error logged but sync continued

        with self.subTest(existing_siae_is_delisted=True):
            # Delisted SIAE should not be taken into account
            siae.is_delisted = True
            siae.save()
            with self.assertNoLogs("lemarche.siaes.management.commands.sync_with_emplois_inclusion"):
                call_command("sync_with_emplois_inclusion", stdout=StringIO())

            self.assertEqual(Siae.objects.filter(brand="Duplicate Brand").count(), 2)
            self.assertEqual(Siae.objects.is_live().filter(brand="Duplicate Brand").count(), 1)

    @patch("lemarche.utils.apis.api_emplois_inclusion.get_siae_list")
    def test_sync_with_emplois_inclusion_with_kind_not_supported(self, mock_get_siae_list):
        mock_get_siae_list.return_value = [
            {
                "id": 123,
                "siret": "12345678901234",
                "kind": "FAKE",
                "name": "Fake SIAE",
                "naf": "8899B",
                "brand": "",
                "phone": "",
                "email": "",
                "website": "",
                "description": "",
                "address_line_1": "1 rue Test",
                "address_line_2": "",
                "post_code": "37000",
                "city": "Tours",
                "department": "37",
                "source": "ASP",
                "latitude": 0,
                "longitude": 0,
                "convention_is_active": True,
                "convention_asp_id": 0,
                "admin_name": "",
                "admin_email": "",
            },
            {
                "id": 124,
                "siret": "12345678901235",
                "naf": "8899B",
                "kind": "EI",
                "name": "Other SIAE",
                "brand": "",
                "phone": "",
                "email": "",
                "website": "",
                "description": "",
                "address_line_1": "1 rue Test",
                "address_line_2": "",
                "post_code": "37000",
                "city": "Tours",
                "department": "37",
                "source": "ASP",
                "latitude": 0,
                "longitude": 0,
                "convention_is_active": True,
                "convention_asp_id": 0,
                "admin_name": "",
                "admin_email": "",
            },
        ]
        os.environ["API_EMPLOIS_INCLUSION_TOKEN"] = "test"
        with self.assertLogs("lemarche.siaes.management.commands.sync_with_emplois_inclusion", level="ERROR") as log:
            call_command("sync_with_emplois_inclusion", stdout=StringIO())

        self.assertIn("Kind not supported: FAKE", log.output[0])

        # Verify only one SIAE was created to check if the sync was not interrupted
        self.assertEqual(Siae.objects.count(), 1)
        self.assertEqual(Siae.objects.first().name, "Other SIAE")


class SiaeUpdateCountFieldsCommandTest(TransactionTestCase):
    @factory.django.mute_signals(signals.post_save, signals.m2m_changed)
    def test_update_count_fields(self):
        """
        Create two siaes with users and activities, and check that the count fields are updated correctly
        """
        siae_1 = SiaeFactory()
        for _ in range(3):
            user = UserFactory()
            siae_1.users.add(user)
        SiaeActivityFactory.create_batch(2, siae=siae_1)

        self.assertEqual(siae_1.user_count, 0)
        self.assertEqual(siae_1.sector_count, 0)
        self.assertEqual(siae_1.network_count, 0)
        self.assertEqual(siae_1.group_count, 0)
        self.assertEqual(siae_1.offer_count, 0)
        self.assertEqual(siae_1.client_reference_count, 0)
        self.assertEqual(siae_1.label_count, 0)
        self.assertEqual(siae_1.image_count, 0)
        self.assertEqual(siae_1.etablissement_count, 0)
        self.assertEqual(siae_1.completion_rate, None)
        self.assertEqual(siae_1.tender_count, 0)
        self.assertEqual(siae_1.tender_email_send_count, 0)
        self.assertEqual(siae_1.tender_email_link_click_count, 0)
        self.assertEqual(siae_1.tender_detail_display_count, 0)
        self.assertEqual(siae_1.tender_detail_contact_click_count, 0)

        siae_2 = SiaeFactory()
        for _ in range(2):
            user = UserFactory()
            siae_2.users.add(user)
        SiaeActivityFactory.create_batch(4, siae=siae_2)

        self.assertEqual(siae_2.user_count, 0)
        self.assertEqual(siae_2.sector_count, 0)

        call_command("update_siae_count_fields", stdout=StringIO())
        siae_1.refresh_from_db()
        self.assertEqual(siae_1.user_count, 3)
        self.assertEqual(siae_1.sector_count, 2)
        siae_2.refresh_from_db()
        self.assertEqual(siae_2.user_count, 2)
        self.assertEqual(siae_2.sector_count, 4)

    @factory.django.mute_signals(signals.post_save, signals.m2m_changed)
    def test_update_count_fields_with_id(self):
        """
        Create two siaes with users and activities, and check that the count fields are updated correctly
        Only for the siae with id
        """
        siae_to_update = SiaeFactory()
        for _ in range(3):
            user = UserFactory()
            siae_to_update.users.add(user)
        SiaeActivityFactory.create_batch(2, siae=siae_to_update)

        siae_not_updated = SiaeFactory()
        for _ in range(3):
            user = UserFactory()
            siae_not_updated.users.add(user)
        SiaeActivityFactory.create_batch(2, siae=siae_not_updated)

        call_command("update_siae_count_fields", id=siae_to_update.id, stdout=StringIO())
        siae_to_update.refresh_from_db()
        self.assertEqual(siae_to_update.user_count, 3)
        self.assertEqual(siae_to_update.sector_count, 2)
        siae_not_updated.refresh_from_db()
        self.assertEqual(siae_not_updated.user_count, 0)
        self.assertEqual(siae_not_updated.sector_count, 0)


class SiaeUpdateApiEntrepriseFieldsCommandTest(TestCase):

    def setUp(self):
        super().setUp()
        self.siae = SiaeFactory()
        self.mock_return_value = {
            "results": [
                {
                    "nom_complet": "SIAE (IAE)",
                    "nom_raison_sociale": "SIAE",
                    "activite_principale": "81.21Z",
                    "date_creation": "2000-01-01",
                    "date_fermeture": "null",
                    "etat_administratif": "A",
                    "nature_juridique": "5710",
                    "section_activite_principale": "N",
                    "tranche_effectif_salarie": "32",
                    "annee_tranche_effectif_salarie": "2022",
                    "matching_etablissements": [
                        {
                            "siret": self.siae.siret,
                            "activite_principale": "81.22Z",
                            "annee_tranche_effectif_salarie": "2024",
                            "date_creation": "2023-06-01",
                            "tranche_effectif_salarie": "32",
                            "est_siege": False,
                            "etat_administratif": "A",
                        }
                    ],
                    "finances": {"2023": {"ca": 9726858, "resultat_net": -782299}},
                }
            ],
            "total_results": 1,
            "page": 1,
            "per_page": 10,
            "total_pages": 1,
        }

    @patch("lemarche.utils.apis.api_recherche_entreprises.requests.get")
    def test_update_api_entreprise_fields_dry_run(self, mock_requests_get):
        """
        Check that the field is not updated in dry run
        """
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = self.mock_return_value

        # Dry run
        out = StringIO()
        call_command("update_api_entreprise_fields", stdout=out)
        self.siae.refresh_from_db()
        self.assertEqual(self.siae.api_entreprise_employees, "")
        self.assertEqual(self.siae.api_entreprise_employees_year_reference, "")
        self.assertIsNone(self.siae.api_entreprise_date_constitution)
        self.assertIsNone(self.siae.api_entreprise_ca)
        self.assertIsNone(self.siae.api_entreprise_etablissement_last_sync_date)
        self.assertIsNone(self.siae.api_entreprise_entreprise_last_sync_date)
        self.assertIsNone(self.siae.api_entreprise_exercice_last_sync_date)

        self.assertIn(f"Would update SIAE {self.siae.id} with", out.getvalue())
        self.assertIn("Done! Processed 1 siae", out.getvalue())

    @patch("lemarche.utils.apis.api_recherche_entreprises.requests.get")
    def test_update_api_entreprise_fields_wet_run(self, mock_requests_get):
        """
        Check that the field is updated correctly in wet run
        """

        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = self.mock_return_value

        # Wet run
        call_command("update_api_entreprise_fields", wet_run=True, stdout=StringIO())
        self.siae.refresh_from_db()
        self.assertEqual(self.siae.api_entreprise_employees, "250 à 499 salariés")
        self.assertEqual(self.siae.api_entreprise_employees_year_reference, "2024")
        self.assertIsNotNone(self.siae.api_entreprise_etablissement_last_sync_date)
        self.assertEqual(
            self.siae.api_entreprise_date_constitution, datetime.strptime("2023-06-01", "%Y-%m-%d").date()
        )
        self.assertEqual(self.siae.api_entreprise_forme_juridique, "SAS")
        self.assertEqual(self.siae.api_entreprise_forme_juridique_code, "5710")
        self.assertIsNotNone(self.siae.api_entreprise_entreprise_last_sync_date)
        self.assertEqual(self.siae.api_entreprise_ca, 9726858)
        self.assertIsNotNone(self.siae.api_entreprise_exercice_last_sync_date)

    @patch("lemarche.utils.apis.api_recherche_entreprises.requests.get")
    def test_update_api_entreprise_fields_with_siret(self, mock_requests_get):
        """
        Check that the field is updated correctly with a siret
        """
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = self.mock_return_value

        SiaeFactory(siret="1222222222222")
        self.siae.refresh_from_db()

        out = StringIO()
        call_command("update_api_entreprise_fields", siret=self.siae.siret, wet_run=True, stdout=out)

        mock_requests_get.assert_called_once()
        self.assertIn("Done! Processed 1 siae", out.getvalue())
        self.siae.refresh_from_db()
        self.assertEqual(self.siae.api_entreprise_employees, "250 à 499 salariés")

    @patch("lemarche.utils.apis.api_recherche_entreprises.requests.get")
    def test_update_api_entreprise_fields_with_no_finance(self, mock_requests_get):
        """
        Check that the field is updated correctly with no finance
        """
        mock_requests_get.return_value.status_code = 200
        self.mock_return_value["results"][0]["finances"] = None
        mock_requests_get.return_value.json.return_value = self.mock_return_value

        call_command("update_api_entreprise_fields", siret=self.siae.siret, wet_run=True, stdout=StringIO())
        self.siae.refresh_from_db()
        self.assertEqual(self.siae.api_entreprise_employees, "250 à 499 salariés")
        self.assertIsNone(self.siae.api_entreprise_ca)
        self.assertIsNone(self.siae.api_entreprise_exercice_last_sync_date)

    @patch("lemarche.utils.apis.api_recherche_entreprises.requests.get")
    def test_update_api_entreprise_fields_finance_orders_asc(self, mock_requests_get):
        """
        Check that the field is updated correctly with finance orders in ascending order
        """
        mock_requests_get.return_value.status_code = 200
        self.mock_return_value["results"][0]["finances"] = {
            "2023": {"ca": 9726858, "resultat_net": -782299},
            "2024": {"ca": 12345678, "resultat_net": 505663},
        }
        mock_requests_get.return_value.json.return_value = self.mock_return_value

        call_command("update_api_entreprise_fields", siret=self.siae.siret, wet_run=True, stdout=StringIO())
        self.siae.refresh_from_db()
        self.assertEqual(self.siae.api_entreprise_ca, 12345678)

    @patch("lemarche.utils.apis.api_recherche_entreprises.requests.get")
    def test_update_api_entreprise_fields_finance_orders_desc(self, mock_requests_get):
        """
        Check that the field is updated correctly with finance orders in descending order
        """
        mock_requests_get.return_value.status_code = 200
        self.mock_return_value["results"][0]["finances"] = {
            "2024": {"ca": 12345678, "resultat_net": 505663},
            "2023": {"ca": 9726858, "resultat_net": -782299},
        }
        mock_requests_get.return_value.json.return_value = self.mock_return_value

        call_command("update_api_entreprise_fields", siret=self.siae.siret, wet_run=True, stdout=StringIO())
        self.siae.refresh_from_db()
        self.assertEqual(self.siae.api_entreprise_ca, 12345678)

    @patch("lemarche.utils.apis.api_recherche_entreprises.requests.get")
    def test_update_api_entreprise_fields_with_siret_not_found(self, mock_requests_get):
        """
        Check that the field is updated correctly with a siret not found
        """
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "results": [],
            "total_results": 0,
            "page": 1,
            "per_page": 10,
            "total_pages": 1,
        }
        out = StringIO()
        call_command("update_api_entreprise_fields", siret=self.siae.siret, wet_run=True, stdout=out)
        self.assertIn("SIRET not found", out.getvalue())


class HosmoZCommandTest(TestCase):

    def setUp(self):
        self.hosmoz_network = NetworkFactory(slug="hosmoz")

    def test_update_empty_siae(self):
        siae = SiaeFactory(
            siret="41155513900012",
            contact_email="",
            contact_phone="",
            employees_insertion_count=None,
            employees_insertion_count_last_updated=None,
            logo_url="",
        )
        self.assertEqual(siae.networks.all().count(), 0)

        call_command(
            "update_hosmoz",
            csv_file="lemarche/fixtures/tests/hosmoz_import.csv",
            logo_folder="lemarche/fixtures/tests/logos",
            stdout=StringIO(),
        )

        siae.refresh_from_db()

        self.assertEqual(siae.contact_email, "contact_lala@email.com")
        self.assertEqual(siae.contact_phone, "01 02 03 04 05")
        self.assertEqual(siae.employees_insertion_count, 22)
        self.assertIsNotNone(siae.employees_insertion_count_last_updated)
        self.assertEqual(siae.networks.all().count(), 1)
        self.assertEqual(siae.logo_url, "http://localhost:9000/bucket/lemarche/fixtures/tests/logos/1.png")

    def test_update_full_siae(self):
        siae = SiaeFactory(
            siret="41155513900012",
            contact_email="dontupdatecontact@email.com",
            contact_phone="++33 1 02 06 06 06",
            employees_insertion_count=10,
            employees_insertion_count_last_updated=None,
            networks=[self.hosmoz_network],
            logo_url="https://logo.com/logo.png",
        )
        self.assertEqual(siae.networks.all().count(), 1)

        call_command(
            "update_hosmoz",
            csv_file="lemarche/fixtures/tests/hosmoz_import.csv",
            logo_folder="lemarche/fixtures/tests/logos",
            stdout=StringIO(),
        )

        siae.refresh_from_db()

        self.assertEqual(siae.contact_email, "dontupdatecontact@email.com")
        self.assertEqual(siae.contact_phone, "++33 1 02 06 06 06")
        self.assertEqual(siae.employees_insertion_count, 10)
        self.assertIsNone(siae.employees_insertion_count_last_updated)
        self.assertEqual(siae.networks.all().count(), 1)
        self.assertEqual(siae.logo_url, "https://logo.com/logo.png")
