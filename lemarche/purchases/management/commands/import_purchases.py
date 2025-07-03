import csv
import logging
from decimal import Decimal, InvalidOperation

from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone

from lemarche.companies.models import Company
from lemarche.purchases.models import Purchase
from lemarche.siaes.models import Siae
from lemarche.utils.commands import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Import purchase data from CSV file. The CSV file must have the following columns: "
        "Raison sociale du Fournisseur, SIRET, Dépense achat (€), Catégorie d'achat (optionnelle), "
        "Entité acheteuse (optionnelle)"
    )

    """
    Import purchase data from CSV file.
    The CSV file must have the following columns:
    - Raison sociale du Fournisseur
    - SIRET
    - Dépense achat (€)
    - Catégorie d'achat (optionnelle)
    - Entité acheteuse (optionnelle)

    Usage:
    python manage.py import_purchases path/to/purchases.csv --year 2025 --company-slug "company-slug" --delimiter ";"
      --encoding "latin-1" --dry-run --skip-errors

    Short example:
    python manage.py import_purchases data/purchases.csv --company-slug "company-slug"
    """

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file to import")
        parser.add_argument("--year", type=int, help="Year of the purchases (default: current year)")
        parser.add_argument("--delimiter", type=str, default=",", help="CSV delimiter (default: comma)")
        parser.add_argument("--encoding", type=str, default="utf-8", help="CSV file encoding (default: utf-8)")
        parser.add_argument("--dry-run", action="store_true", help="Run without saving to database (for testing)")
        parser.add_argument("--skip-errors", action="store_true", help="Skip rows with errors and continue")
        parser.add_argument(
            "--company-slug", type=str, required=True, help="Slug of the Company to link purchases to (required)"
        )

    def handle(self, *args, **options):
        """Main entry point for the command."""
        self._setup_import(options)
        self._validate_year(options.get("year") or timezone.now().year)
        company = self._get_company(options["company_slug"])

        stats = self._initialize_stats()

        try:
            self._process_csv_file(options, company, stats)
        except FileNotFoundError:
            raise CommandError(f"CSV file not found: {options['csv_file']}")
        except UnicodeDecodeError:
            raise CommandError(
                f"Could not decode file with encoding {options['encoding']}. "
                f"Try --encoding=utf-8-sig or --encoding=latin-1"
            )
        except Exception as e:
            raise CommandError(f"Unexpected error: {str(e)}")

    def _setup_import(self, options):
        """Setup import parameters and display initial information."""
        self.csv_file = options["csv_file"]
        self.purchase_year = options.get("year") or timezone.now().year
        self.delimiter = options["delimiter"]
        self.encoding = options["encoding"]
        self.dry_run = options["dry_run"]
        self.skip_errors = options["skip_errors"]

        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No data will be saved to database"))

    def _validate_year(self, year):
        """Validate the purchase year."""
        current_year = timezone.now().year
        if year < 1900 or year > current_year + 1:
            raise CommandError(f"Invalid year: {year}. Must be between 1900 and {current_year + 1}")

    def _get_company(self, company_slug):
        """Get company by slug."""
        try:
            company = Company.objects.get(slug=company_slug)
            self.stdout.write(f"Linking purchases to company: {company.name}")
            return company
        except Company.DoesNotExist:
            raise CommandError(f"Company with slug {company_slug} not found")

    def _initialize_stats(self):
        """Initialize statistics dictionary."""
        return {"total_rows": 0, "imported": 0, "skipped": 0, "errors": 0, "siae_matches": 0, "company_matches": 0}

    def _process_csv_file(self, options, company, stats):
        """Process the CSV file and import purchases."""
        expected_columns = [
            "Raison sociale du Fournisseur",
            "SIRET",
            "Dépense achat (€)",
            "Catégorie d'achat (optionnelle)",
            "Entité acheteuse (optionnelle)",
        ]

        with open(self.csv_file, "r", encoding=self.encoding) as file:
            reader = csv.DictReader(file, delimiter=self.delimiter)
            if not reader.fieldnames:
                raise CommandError("Could not read CSV headers")

            self._validate_csv_columns(reader.fieldnames, expected_columns)
            self.stdout.write(f"Found columns: {list(reader.fieldnames)}")
            self.stdout.write(f"Importing purchases for year: {self.purchase_year}")

            with transaction.atomic():
                self._process_rows(reader, company, stats)

        self._display_final_stats(stats)

    def _validate_csv_columns(self, fieldnames, expected_columns):
        """Validate that all expected columns are present in the CSV."""
        missing_columns = [col for col in expected_columns if col not in fieldnames]
        if missing_columns:
            raise CommandError(f"Missing required columns: {missing_columns}")

    def _process_rows(self, reader, company, stats):
        """Process all rows in the CSV file."""
        for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header for row number in error message
            stats["total_rows"] += 1

            try:
                self._process_single_row(row, company, stats)
            except Exception as e:
                self._handle_row_error(e, row_num, stats)

    def _process_single_row(self, row, company, stats):
        """Process a single row from the CSV."""
        # Clean and validate data
        supplier_name = row["Raison sociale du Fournisseur"].strip()
        supplier_siret = row["SIRET"].strip().replace(" ", "")
        purchase_amount_str = row["Dépense achat (€)"].strip()
        purchase_category = row["Catégorie d'achat (optionnelle)"].strip() or None
        buying_entity = row["Entité acheteuse (optionnelle)"].strip() or None

        # Validate required fields
        self._validate_row_data(supplier_name, supplier_siret, purchase_amount_str)

        # Parse purchase amount
        purchase_amount = self._parse_purchase_amount(purchase_amount_str)

        # Find matching SIAE
        siae = self._find_matching_siae(supplier_siret, stats)

        # Create purchase object
        purchase_data = {
            "supplier_name": supplier_name,
            "supplier_siret": supplier_siret,
            "purchase_amount": purchase_amount,
            "purchase_category": purchase_category,
            "buying_entity": buying_entity,
            "purchase_year": self.purchase_year,
            "siae": siae,
            "company": company,
        }

        if not self.dry_run:
            Purchase.objects.create(**purchase_data)

        stats["imported"] += 1

        # Progress indicator
        if stats["imported"] % 100 == 0:
            self.stdout_info(f'Processed {stats["imported"]} rows...')

    def _validate_row_data(self, supplier_name, supplier_siret, purchase_amount_str):
        """Validate required fields in a row."""
        if not supplier_name:
            raise ValueError("Supplier name is required")

        if not supplier_siret:
            raise ValueError("SIRET is required")

        # Validate SIRET format (14 digits)
        if not supplier_siret.isdigit() or len(supplier_siret) != 14:
            raise ValueError(f"Invalid SIRET format: {supplier_siret}")

    def _parse_purchase_amount(self, purchase_amount_str):
        """Parse and validate purchase amount."""
        try:
            purchase_amount_str = purchase_amount_str.replace(" ", "").replace(",", ".")
            purchase_amount = Decimal(purchase_amount_str)
            if purchase_amount <= 0:
                raise ValueError("Purchase amount must be positive")
            return purchase_amount
        except (InvalidOperation, ValueError):
            raise ValueError(f"Invalid purchase amount: {purchase_amount_str}")

    def _find_matching_siae(self, supplier_siret, stats):
        """Find matching SIAE for the given SIRET."""
        siae = None
        try:
            siae = Siae.objects.is_live().get(siret=supplier_siret)
            stats["siae_matches"] += 1
        except Siae.DoesNotExist:
            pass  # No SIAE found, this is normal
        except Siae.MultipleObjectsReturned:
            # If multiple SIAEs are found, we get first one
            siae = Siae.objects.is_live().filter(siret=supplier_siret).first()
            self.stdout_warning(f"Multiple SIAEs found for SIRET: {supplier_siret}. Using first one: {siae.name}")
        return siae

    def _handle_row_error(self, error, row_num, stats):
        """Handle errors that occur while processing a row."""
        stats["errors"] += 1
        error_msg = f"Row {row_num}: {str(error)}"

        if self.skip_errors:
            self.stdout_warning(f"Error on row {row_num}: {str(error)}")
            stats["skipped"] += 1
        else:
            # In transaction mode, we need to rollback on error
            if not self.dry_run:
                raise CommandError(f"Transaction rolled back due to error: {error_msg}")
            else:
                raise CommandError(error_msg)

    def _display_final_stats(self, stats):
        """Display final import statistics."""
        self.stdout_messages_info(
            [
                "\n" + "=" * 50,
                "IMPORT SUMMARY",
                "=" * 50,
                f'Total rows processed: {stats["total_rows"]}',
                f'Successfully imported: {stats["imported"]}',
                f'Skipped due to errors: {stats["skipped"]}',
                f'Errors encountered: {stats["errors"]}',
                f'SIAE matches found: {stats["siae_matches"]}',
            ]
        )

        if stats["imported"] > 0:
            siae_percentage = (stats["siae_matches"] / stats["imported"]) * 100
            self.stdout_info(f"SIAE match percentage: {siae_percentage:.1f}%")

        if self.dry_run:
            self.stdout_warning("\nDRY RUN - No data was actually saved to database")
        else:
            self.stdout_success("\nImport completed successfully!")
