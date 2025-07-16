import os
import tempfile
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from lemarche.companies.factories import CompanyFactory
from lemarche.purchases.models import Purchase
from lemarche.siaes.factories import SiaeFactory


class ImportPurchasesCommandTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = CompanyFactory(name="Test Company")
        cls.siae = SiaeFactory(siret="12345678901234")
        cls.current_year = timezone.now().year

        # Get the path to the sample file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cls.sample_file = os.path.join(current_dir, "sample_purchases.csv")

    def setUp(self):
        self.csv_content = """Raison sociale du Fournisseur,SIRET,Dépense achat (€),Catégorie d'achat (optionnelle),Entité acheteuse (optionnelle)
Entreprise Test 1,12345678901234,15000.50,Services informatiques,Service IT
Entreprise Test 2,98765432109876,2500.00,Fournitures de bureau,Service RH
Entreprise Test 3,11111111111111,75000.00,Matériel informatique,Service Achats
Entreprise Test 4,22222222222222,1200.75,Formation,Service Formation
Entreprise Test 5,33333333333333,50000.00,Maintenance,Service Technique"""  # noqa: E501

    def create_temp_csv_file(self, content=None):
        """Create a temporary CSV file for testing"""
        if content is None:
            content = self.csv_content

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def test_import_purchases_with_sample_file(self):
        """Test import using the existing sample_purchases.csv file"""

        call_command("import_purchases", self.sample_file, company_slug=self.company.slug, year=self.current_year)

        # Check that purchases were created
        purchases = Purchase.objects.all()
        self.assertEqual(purchases.count(), 5)

        # Check first purchase details from sample file
        first_purchase = purchases.first()
        self.assertEqual(first_purchase.supplier_name, "Entreprise Test 1")
        self.assertEqual(first_purchase.supplier_siret, "11111111111111")
        self.assertEqual(first_purchase.purchase_amount, Decimal("15000.50"))
        self.assertEqual(first_purchase.purchase_category, "Services informatiques")
        self.assertEqual(first_purchase.buying_entity, "Service IT")
        self.assertEqual(first_purchase.purchase_year, self.current_year)
        self.assertEqual(first_purchase.company, self.company)

        # Check that one purchase matched with SIAE
        siae_purchases = purchases.filter(siae__isnull=False)
        self.assertEqual(siae_purchases.count(), 1)
        siae_purchase = siae_purchases.first()
        self.assertEqual(siae_purchase.siae, self.siae)
        self.assertEqual(siae_purchase.supplier_name, "Entreprise Test 3")

    def test_import_purchases_with_default_year(self):
        """Test import without specifying year (should use current year)"""

        call_command("import_purchases", self.sample_file, company_slug=self.company.slug)

        purchases = Purchase.objects.all()
        self.assertEqual(purchases.count(), 5)

        # All purchases should have current year
        for purchase in purchases:
            self.assertEqual(purchase.purchase_year, self.current_year)

    def test_import_purchases_dry_run(self):
        """Test dry run mode - no data should be saved"""

        call_command(
            "import_purchases", self.sample_file, company_slug=self.company.slug, year=self.current_year, dry_run=True
        )

        # No purchases should be created in dry run mode
        purchases = Purchase.objects.all()
        self.assertEqual(purchases.count(), 0)

    def test_import_purchases_with_skip_errors(self):
        """Test import with skip_errors option"""
        # Create CSV with invalid data
        invalid_csv = """Raison sociale du Fournisseur,SIRET,Dépense achat (€),Catégorie d'achat (optionnelle),Entité acheteuse (optionnelle)
Entreprise Test 1,12345678901234,15000.50,Services informatiques,Service IT
Entreprise Test 2,invalid_siret,2500.00,Fournitures de bureau,Service RH
Entreprise Test 3,11111111111111,75000.00,Matériel informatique,Service Achats"""  # noqa: E501

        csv_file = self.create_temp_csv_file(invalid_csv)

        try:
            call_command(
                "import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year, skip_errors=True
            )

            # Only valid purchases should be created
            purchases = Purchase.objects.all()
            self.assertEqual(purchases.count(), 2)  # 2 valid, 1 invalid

        finally:
            os.unlink(csv_file)

    def test_import_purchases_without_skip_errors(self):
        """Test import without skip_errors - should fail on first error"""
        # Create CSV with invalid data
        invalid_csv = """Raison sociale du Fournisseur,SIRET,Dépense achat (€),Catégorie d'achat (optionnelle),Entité acheteuse (optionnelle)
Entreprise Test 1,12345678901234,15000.50,Services informatiques,Service IT
Entreprise Test 2,invalid_siret,2500.00,Fournitures de bureau,Service RH"""  # noqa: E501

        csv_file = self.create_temp_csv_file(invalid_csv)

        try:
            with self.assertRaises(CommandError) as context:
                call_command("import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year)

            self.assertIn("Invalid SIRET format", str(context.exception))

            # No purchases should be created
            purchases = Purchase.objects.all()
            self.assertEqual(purchases.count(), 0)

        finally:
            os.unlink(csv_file)

    def test_import_purchases_invalid_year(self):
        """Test import with invalid year"""
        csv_file = self.create_temp_csv_file()

        try:
            with self.assertRaises(CommandError) as context:
                call_command("import_purchases", csv_file, company_slug=self.company.slug, year=1800)  # Invalid year

            self.assertIn("Invalid year", str(context.exception))

        finally:
            os.unlink(csv_file)

    def test_import_purchases_company_not_found(self):
        """Test import with non-existent company slug"""
        csv_file = self.create_temp_csv_file()

        try:
            with self.assertRaises(CommandError) as context:
                call_command("import_purchases", csv_file, company_slug="non-existent-company", year=self.current_year)

            self.assertIn("Company with slug non-existent-company not found", str(context.exception))

        finally:
            os.unlink(csv_file)

    def test_import_purchases_missing_required_columns(self):
        """Test import with missing required columns"""
        invalid_csv = """Raison sociale du Fournisseur,SIRET
Entreprise Test 1,12345678901234"""

        csv_file = self.create_temp_csv_file(invalid_csv)

        try:
            with self.assertRaises(CommandError) as context:
                call_command("import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year)

            self.assertIn("Missing required columns", str(context.exception))

        finally:
            os.unlink(csv_file)

    def test_import_purchases_empty_file(self):
        """Test import with empty CSV file"""
        csv_file = self.create_temp_csv_file("")

        try:
            with self.assertRaises(CommandError) as context:
                call_command("import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year)

            self.assertIn("Could not read CSV headers", str(context.exception))

        finally:
            os.unlink(csv_file)

    def test_import_purchases_invalid_amount(self):
        """Test import with invalid purchase amount"""
        invalid_csv = """Raison sociale du Fournisseur,SIRET,Dépense achat (€),Catégorie d'achat (optionnelle),Entité acheteuse (optionnelle)
Entreprise Test 1,12345678901234,invalid_amount,Services informatiques,Service IT"""  # noqa: E501

        csv_file = self.create_temp_csv_file(invalid_csv)

        try:
            with self.assertRaises(CommandError) as context:
                call_command("import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year)

            self.assertIn("Invalid purchase amount", str(context.exception))

        finally:
            os.unlink(csv_file)

    def test_import_purchases_negative_amount(self):
        """Test import with negative purchase amount"""
        invalid_csv = """Raison sociale du Fournisseur,SIRET,Dépense achat (€),Catégorie d'achat (optionnelle),Entité acheteuse (optionnelle)
Entreprise Test 1,12345678901234,-15000.50,Services informatiques,Service IT"""  # noqa: E501

        csv_file = self.create_temp_csv_file(invalid_csv)

        try:
            with self.assertRaises(CommandError) as context:
                call_command("import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year)

            self.assertIn("Invalid purchase amount: -15000.50", str(context.exception))

        finally:
            os.unlink(csv_file)

    def test_import_purchases_missing_supplier_name(self):
        """Test import with missing supplier name"""
        invalid_csv = """Raison sociale du Fournisseur,SIRET,Dépense achat (€),Catégorie d'achat (optionnelle),Entité acheteuse (optionnelle)
,12345678901234,15000.50,Services informatiques,Service IT"""  # noqa: E501

        csv_file = self.create_temp_csv_file(invalid_csv)

        try:
            with self.assertRaises(CommandError) as context:
                call_command("import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year)

            self.assertIn("Supplier name is required", str(context.exception))

        finally:
            os.unlink(csv_file)

    def test_import_purchases_missing_siret(self):
        """Test import with missing SIRET"""
        invalid_csv = """Raison sociale du Fournisseur,SIRET,Dépense achat (€),Catégorie d'achat (optionnelle),Entité acheteuse (optionnelle)
Entreprise Test 1,,15000.50,Services informatiques,Service IT"""  # noqa: E501

        csv_file = self.create_temp_csv_file(invalid_csv)

        try:
            with self.assertRaises(CommandError) as context:
                call_command("import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year)

            self.assertIn("SIRET is required", str(context.exception))

        finally:
            os.unlink(csv_file)

    def test_import_purchases_with_different_delimiter(self):
        """Test import with semicolon delimiter"""
        semicolon_csv = """Raison sociale du Fournisseur;SIRET;Dépense achat (€);Catégorie d'achat (optionnelle);Entité acheteuse (optionnelle)
Entreprise Test 1;12345678901234;15000.50;Services informatiques;Service IT"""  # noqa: E501

        csv_file = self.create_temp_csv_file(semicolon_csv)

        try:
            call_command(
                "import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year, delimiter=";"
            )

            purchases = Purchase.objects.all()
            self.assertEqual(purchases.count(), 1)

            purchase = purchases.first()
            self.assertEqual(purchase.supplier_name, "Entreprise Test 1")
            self.assertEqual(purchase.supplier_siret, "12345678901234")

        finally:
            os.unlink(csv_file)

    def test_import_purchases_amount_with_comma(self):
        """Test import with amount using comma as decimal separator"""
        comma_csv = """Raison sociale du Fournisseur,SIRET,Dépense achat (€),Catégorie d'achat (optionnelle),Entité acheteuse (optionnelle)
Entreprise Test 1,12345678901234,"15000,50",Services informatiques,Service IT"""  # noqa: E501

        csv_file = self.create_temp_csv_file(comma_csv)

        try:
            call_command("import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year)

            purchases = Purchase.objects.all()
            self.assertEqual(purchases.count(), 1)

            purchase = purchases.first()
            self.assertEqual(purchase.purchase_amount, Decimal("15000.50"))

        finally:
            os.unlink(csv_file)

    def test_import_purchases_siret_with_spaces(self):
        """Test import with SIRET containing spaces"""
        space_siret_csv = """Raison sociale du Fournisseur,SIRET,Dépense achat (€),Catégorie d'achat (optionnelle),Entité acheteuse (optionnelle)
Entreprise Test 1,123 456 789 01234,15000.50,Services informatiques,Service IT"""  # noqa: E501

        csv_file = self.create_temp_csv_file(space_siret_csv)

        try:
            call_command("import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year)

            purchases = Purchase.objects.all()
            self.assertEqual(purchases.count(), 1)

            purchase = purchases.first()
            self.assertEqual(purchase.supplier_siret, "12345678901234")

        finally:
            os.unlink(csv_file)

    def test_import_purchases_optional_fields_empty(self):
        """Test import with empty optional fields"""
        empty_optional_csv = """Raison sociale du Fournisseur,SIRET,Dépense achat (€),Catégorie d'achat (optionnelle),Entité acheteuse (optionnelle)
Entreprise Test 1,12345678901234,15000.50,,"""  # noqa: E501

        csv_file = self.create_temp_csv_file(empty_optional_csv)

        try:
            call_command("import_purchases", csv_file, company_slug=self.company.slug, year=self.current_year)

            purchases = Purchase.objects.all()
            self.assertEqual(purchases.count(), 1)

            purchase = purchases.first()
            self.assertIsNone(purchase.purchase_category)
            self.assertIsNone(purchase.buying_entity)

        finally:
            os.unlink(csv_file)

    def test_import_purchases_with_multiple_siaes_with_same_siret(self):
        SiaeFactory(siret="12345678901234")
        out = StringIO()
        call_command(
            "import_purchases", self.sample_file, company_slug=self.company.slug, year=self.current_year, stdout=out
        )

        purchases = Purchase.objects.filter(siae=self.siae)
        self.assertEqual(purchases.count(), 1)

        purchase = purchases.first()
        self.assertEqual(purchase.supplier_name, "Entreprise Test 3")

        self.assertIn(
            f"Multiple SIAEs found for SIRET: 12345678901234. Using first one: {self.siae.name}", out.getvalue()
        )
