from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase

from lemarche.utils.apis.brevo_attributes import ALL_COMPANY_ATTRIBUTES, ALL_CONTACT_ATTRIBUTES


class BrevoCheckAttributesCommandTest(TestCase):
    """Tests for the brevo_check_attributes management command."""

    @patch("lemarche.crm.management.commands.brevo_check_attributes.api_brevo.BrevoBaseApiClient")
    @patch("lemarche.crm.management.commands.brevo_check_attributes.brevo_python.ContactsApi")
    def test_check_contact_attributes_all_present(self, mock_contacts_api_class, mock_base_client):
        """Test when all contact attributes are present in Brevo"""
        # Mock existing attributes in Brevo
        mock_api_instance = MagicMock()
        mock_contacts_api_class.return_value = mock_api_instance

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"attributes": [{"name": attr} for attr in ALL_CONTACT_ATTRIBUTES]}
        mock_api_instance.get_attributes.return_value = mock_response

        out = StringIO()
        call_command("brevo_check_attributes", entity="contacts", dry_run=True, stdout=out)

        output = out.getvalue()
        self.assertIn("No missing attributes ✅", output)
        self.assertIn("CONTACT ATTRIBUTES VERIFICATION", output)

    @patch("lemarche.crm.management.commands.brevo_check_attributes.api_brevo.BrevoBaseApiClient")
    @patch("lemarche.crm.management.commands.brevo_check_attributes.brevo_python.ContactsApi")
    def test_check_contact_attributes_missing(self, mock_contacts_api_class, mock_base_client):
        """Test when some contact attributes are missing in Brevo"""
        # Mock existing attributes in Brevo (missing some expected ones)
        mock_api_instance = MagicMock()
        mock_contacts_api_class.return_value = mock_api_instance

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "attributes": [
                {"name": "NOM"},
                {"name": "PRENOM"},
                # Missing other expected attributes
            ]
        }
        mock_api_instance.get_attributes.return_value = mock_response

        out = StringIO()
        call_command("brevo_check_attributes", entity="contacts", dry_run=True, stdout=out)

        output = out.getvalue()
        self.assertIn("Missing attributes", output)
        self.assertIn("DATE_INSCRIPTION", output)
        self.assertIn("TYPE_ORGANISATION", output)

    @patch("lemarche.crm.management.commands.brevo_check_attributes.api_brevo.BrevoBaseApiClient")
    @patch("lemarche.crm.management.commands.brevo_check_attributes.brevo_python.CompaniesApi")
    def test_check_company_attributes_all_present(self, mock_companies_api_class, mock_base_client):
        """Test when all company attributes are present in Brevo"""
        # Mock existing attributes in Brevo
        mock_api_instance = MagicMock()
        mock_companies_api_class.return_value = mock_api_instance

        # companies_attributes_get() returns directly a list, not a dict with to_dict()
        mock_response = [{"internalName": attr} for attr in ALL_COMPANY_ATTRIBUTES]
        mock_api_instance.companies_attributes_get.return_value = mock_response

        out = StringIO()
        call_command("brevo_check_attributes", entity="companies", dry_run=True, stdout=out)

        output = out.getvalue()
        self.assertIn("No missing attributes ✅", output)
        self.assertIn("COMPANY ATTRIBUTES VERIFICATION", output)

    @patch("lemarche.crm.management.commands.brevo_check_attributes.api_brevo.BrevoBaseApiClient")
    @patch("lemarche.crm.management.commands.brevo_check_attributes.brevo_python.CompaniesApi")
    def test_check_company_attributes_missing(self, mock_companies_api_class, mock_base_client):
        """Test when some company attributes are missing in Brevo"""
        # Mock existing attributes in Brevo (missing some expected ones)
        mock_api_instance = MagicMock()
        mock_companies_api_class.return_value = mock_api_instance

        # companies_attributes_get() returns directly a list, not a dict with to_dict()
        mock_response = [
            {"internalName": "domain"},
            {"internalName": "phone_number"},
            # Missing other expected attributes
        ]
        mock_api_instance.companies_attributes_get.return_value = mock_response

        out = StringIO()
        call_command("brevo_check_attributes", entity="companies", dry_run=True, stdout=out)

        output = out.getvalue()
        self.assertIn("Missing attributes", output)
        self.assertIn("app_id", output)
        self.assertIn("siae", output)

    @patch("lemarche.crm.management.commands.brevo_check_attributes.api_brevo.BrevoBaseApiClient")
    @patch("lemarche.crm.management.commands.brevo_check_attributes.brevo_python.ContactsApi")
    def test_create_missing_contact_attributes_dry_run(self, mock_contacts_api_class, mock_base_client):
        """Test creating missing contact attributes in dry run mode"""
        # Mock existing attributes in Brevo (missing some expected ones)
        mock_api_instance = MagicMock()
        mock_contacts_api_class.return_value = mock_api_instance

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "attributes": [
                {"name": "NOM"},
                {"name": "PRENOM"},
            ]
        }
        mock_api_instance.get_attributes.return_value = mock_response

        out = StringIO()
        call_command("brevo_check_attributes", entity="contacts", create_missing=True, dry_run=True, stdout=out)

        output = out.getvalue()
        self.assertIn("Simulation mode - the following attributes would be created:", output)
        self.assertIn("DATE_INSCRIPTION", output)
        # Should not actually call create_attribute in dry run mode
        mock_api_instance.create_attribute.assert_not_called()

    @patch("lemarche.crm.management.commands.brevo_check_attributes.api_brevo.BrevoBaseApiClient")
    @patch("lemarche.crm.management.commands.brevo_check_attributes.brevo_python.ContactsApi")
    def test_create_missing_contact_attributes_real(self, mock_contacts_api_class, mock_base_client):
        """Test actually creating missing contact attributes"""
        # Mock existing attributes in Brevo (missing some expected ones)
        mock_api_instance = MagicMock()
        mock_contacts_api_class.return_value = mock_api_instance

        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "attributes": [
                {"name": "NOM"},
                {"name": "PRENOM"},
            ]
        }
        mock_api_instance.get_attributes.return_value = mock_response

        out = StringIO()
        call_command("brevo_check_attributes", entity="contacts", create_missing=True, dry_run=False, stdout=out)

        output = out.getvalue()
        self.assertIn("Creating missing contact attributes", output)
        self.assertIn("✅ Attribute created", output)

    def test_check_all_entities(self):
        """Test checking both contacts and companies"""
        with (
            patch("lemarche.crm.management.commands.brevo_check_attributes.api_brevo.BrevoBaseApiClient"),
            patch("lemarche.crm.management.commands.brevo_check_attributes.brevo_python.ContactsApi") as mock_contacts,
            patch(
                "lemarche.crm.management.commands.brevo_check_attributes.brevo_python.CompaniesApi"
            ) as mock_companies,
        ):
            # Mock responses for both APIs
            for mock_api_class in [mock_contacts, mock_companies]:
                mock_api_instance = MagicMock()
                mock_api_class.return_value = mock_api_instance

                # Different response structures for contacts vs companies
                if mock_api_class == mock_contacts:
                    # Contacts API returns object with to_dict()
                    mock_response = MagicMock()
                    mock_response.to_dict.return_value = {"attributes": []}
                    mock_api_instance.get_attributes.return_value = mock_response
                else:
                    # Companies API returns list directly
                    mock_response = []
                    mock_api_instance.companies_attributes_get.return_value = mock_response

            out = StringIO()
            call_command("brevo_check_attributes", entity="all", dry_run=True, stdout=out)

            output = out.getvalue()
            self.assertIn("CONTACT ATTRIBUTES VERIFICATION", output)
            self.assertIn("COMPANY ATTRIBUTES VERIFICATION", output)

    def test_command_arguments(self):
        """Test command argument parsing"""
        out = StringIO()

        # Test valid entity choices work
        call_command("brevo_check_attributes", entity="contacts", dry_run=True, stdout=out)
        call_command("brevo_check_attributes", entity="companies", dry_run=True, stdout=out)
        call_command("brevo_check_attributes", entity="all", dry_run=True, stdout=out)
