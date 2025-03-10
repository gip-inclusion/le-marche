import logging
import os
from unittest.mock import patch

import factory
from django.core.management import call_command
from django.db.models import signals
from django.test import TransactionTestCase

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
            call_command("sync_with_emplois_inclusion")

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
            call_command("sync_with_emplois_inclusion")

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
            call_command("sync_with_emplois_inclusion")

        # Verify SIAE was updated
        self.assertEqual(Siae.objects.count(), 1)
        updated_siae.refresh_from_db()
        self.assertEqual(updated_siae.brand, "Updated Name")  # Brand name can only be updated once

    @patch("lemarche.utils.apis.api_emplois_inclusion.get_siae_list")
    def test_sync_with_emplois_inclusion_with_duplicate_brand_name_on_create(self, mock_get_siae_list):
        # Create existing SIAE with the same brand name
        SiaeFactory(siret="98765432101233", brand="Duplicate Brand", kind=siae_constants.KIND_EI)

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
        with self.assertLogs("lemarche.siaes.management.commands.sync_with_emplois_inclusion", level="ERROR") as log:
            call_command("sync_with_emplois_inclusion")

        # Verify warning was logged
        self.assertIn("Brand name is already used by another SIAE", log.output[0])

        # Verify both SIAEs exist
        self.assertEqual(Siae.objects.count(), 1)

    @patch("lemarche.utils.apis.api_emplois_inclusion.get_siae_list")
    def test_sync_with_emplois_inclusion_with_duplicate_brand_name_on_update(self, mock_get_siae_list):
        # Create existing SIAE with the same brand name
        SiaeFactory(siret="98765432101233", brand="Duplicate Brand", kind=siae_constants.KIND_EI)
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
        with self.assertLogs("lemarche.siaes.management.commands.sync_with_emplois_inclusion", level="ERROR") as log:
            call_command("sync_with_emplois_inclusion")

        # Verify warning was logged
        self.assertIn("Brand name is already used by another SIAE: 'Duplicate Brand'", log.output[0])

        # Verify both SIAEs exist
        self.assertEqual(Siae.objects.count(), 3)
        self.assertEqual(Siae.objects.filter(brand="Duplicate Brand").count(), 1)

        self.assertEqual(Siae.objects.filter(name="Other New SIAE").count(), 1)  # error logged but sync continued

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
            call_command("sync_with_emplois_inclusion")

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

        call_command("update_siae_count_fields")
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

        call_command("update_siae_count_fields", id=siae_to_update.id)
        siae_to_update.refresh_from_db()
        self.assertEqual(siae_to_update.user_count, 3)
        self.assertEqual(siae_to_update.sector_count, 2)
        siae_not_updated.refresh_from_db()
        self.assertEqual(siae_not_updated.user_count, 0)
        self.assertEqual(siae_not_updated.sector_count, 0)
