from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from tqdm import tqdm

from lemarche.companies.models import Company
from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_brevo
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Script for synchronizing companies (SIAE and buyer companies) with Brevo CRM

    Features:
    - Complete or partial synchronization (recently modified companies)
    - Supports both SIAE and buyer Company synchronization
    - Tracks statistics over 90 days for Brevo (SIAE only)
    - Robust error handling and recovery mechanism
    - Progress display

    Usage:
    python manage.py crm_brevo_sync_companies --recently-updated
    python manage.py crm_brevo_sync_companies --batch-size=50 --dry-run
    python manage.py crm_brevo_sync_companies
    """

    def __init__(self):
        super().__init__()
        self.stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "extra_data_updated": 0,
            "total": 0,
        }

    def add_arguments(self, parser):
        parser.add_argument(
            "--recently-updated",
            dest="recently_updated",
            action="store_true",
            help="Synchronize only recently modified companies",
        )
        parser.add_argument(
            "--max-retries",
            dest="max_retries",
            type=int,
            default=3,
            help="Maximum number of retry attempts in case of API error",
        )
        parser.add_argument(
            "--recently-updated-from-weeks",
            dest="recently_updated_from_weeks",
            type=int,
            default=2,
            help="Synchronize only recently modified SIAEs from the last X weeks (default: 2 weeks)",
        )
        parser.add_argument(
            "--batch-size",
            dest="batch_size",
            type=int,
            default=50,
            help="Number of companies to process per batch",
        )
        parser.add_argument(
            "--max-retries",
            dest="max_retries",
            type=int,
            default=3,
            help="Maximum number of retry attempts in case of API error",
        )
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Simulation mode (no changes)")

        parser.add_argument(
            "--company-type",
            dest="company_type",
            type=str,
            choices=["siae", "buyer", "all"],
            default="all",
            help="Type of companies to synchronize: siae, buyer, or all",
        )
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Simulation mode (no changes)")

    def handle(
        self,
        recently_updated: bool = False,
        max_retries: int = 3,
        company_type: str = "all",
        dry_run: bool = False,
        recently_updated_from_weeks: int = 2,
        **options,
    ):
        self.stdout_info("-" * 80)
        self.stdout_info("SIAE synchronization script with Brevo CRM (companies)...")

        if dry_run:
            self.stdout_info("Simulation mode enabled - no changes will be made")

        # Set variables for retries
        self.max_retries = max_retries
        self.retry_delay = 5  # milliseconds
        self.recently_updated_from_weeks = recently_updated_from_weeks

        if dry_run:
            self.stdout_info("Simulation mode enabled - no changes will be made")

        # Process SIAE companies
        if company_type in ["siae", "all"]:
            self.stdout_info("Processing SIAE companies...")
            self._sync_siaes(recently_updated, max_retries, dry_run)

        # Process buyer companies
        if company_type in ["buyer", "all"]:
            self.stdout_info("Processing buyer companies...")
            self._sync_buyer_companies(recently_updated, max_retries, dry_run)

        # Display final report
        self._display_final_report()

    def _sync_siaes(self, recently_updated: bool, max_retries: int, dry_run: bool):
        """Synchronize SIAE companies with Brevo CRM"""
        # Build the queryset
        siaes_qs = self._build_siae_queryset(recently_updated)

        # Initialize statistics
        self.stats["total"] += siaes_qs.count()

        # Process SIAEs
        self._process_siaes(siaes_qs, dry_run)

    def _build_siae_queryset(self, recently_updated: bool):
        """Build the queryset of SIAEs to process."""
        siaes_qs = Siae.objects.all()
        self.stats["total"] = siaes_qs.count()
        self.stdout_info(f"Total SIAEs in database: {self.stats['total']}")

        if recently_updated:
            two_weeks_ago = timezone.now() - timedelta(weeks=self.recently_updated_from_weeks)
            siaes_qs = siaes_qs.filter(updated_at__gte=two_weeks_ago)
            self.stats["total"] = siaes_qs.count()
            self.stdout_info(f"Recently modified SIAEs: {self.stats['total']}")

        return siaes_qs.with_tender_stats(since_days=90)  # type: ignore

    def _process_siaes(self, siaes_qs, dry_run: bool) -> None:
        """Process each SIAE individually."""
        # use .iterator to optimize the chunk processing of large querysets
        for siae in siaes_qs.iterator():
            try:
                self._process_single_siae(siae, dry_run)
            except Exception as e:
                self.stats["errors"] += 1
                self.stdout_error(f"Error processing SIAE {siae.id}: {str(e)}")

    def _process_single_siae(self, siae, dry_run: bool):
        """Process a single SIAE."""
        new_extra_data = self._prepare_siae_extra_data(siae)
        extra_data_changed = self._update_siae_extra_data_if_needed(siae, new_extra_data, dry_run)
        self._sync_siae_with_brevo_if_needed(siae, extra_data_changed, dry_run, self.max_retries)

    def _prepare_siae_extra_data(self, siae) -> dict:
        """Prepare new extra_data for SIAE."""
        return {
            "completion_rate": siae.completion_rate if siae.completion_rate is not None else 0,
            "tender_received": siae.tender_email_send_count_annotated,
            "tender_interest": siae.tender_detail_contact_click_count_annotated,
        }

    def _update_siae_extra_data_if_needed(self, siae, new_extra_data: dict, dry_run: bool) -> bool:
        """Update SIAE extra_data if needed and return whether changes were made."""
        if siae.extra_data.get("brevo_company_data") != new_extra_data:
            siae.extra_data.update({"brevo_company_data": new_extra_data})
            if not dry_run:
                siae.save(update_fields=["extra_data"])
            self.stats["extra_data_updated"] += 1
            return True
        return False

    def _sync_siae_with_brevo_if_needed(self, siae, extra_data_changed: bool, dry_run: bool, max_retries: int):
        """Synchronize SIAE with Brevo if needed."""
        if not siae.brevo_company_id or extra_data_changed:
            if not dry_run:
                api_brevo.create_or_update_company(siae, max_retries=max_retries, retry_delay=5)

            if siae.brevo_company_id:
                self.stats["updated"] += 1
            else:
                self.stats["created"] += 1
        else:
            self.stats["skipped"] += 1

    def _sync_buyer_companies(self, recently_updated: bool, max_retries: int, dry_run: bool):
        """Synchronize buyer companies with Brevo CRM"""
        # Build the queryset
        companies_qs = self._build_buyer_company_queryset(recently_updated)

        # Initialize statistics
        self.stats["total"] += companies_qs.count()

        # Process companies
        self._process_buyer_companies(companies_qs, dry_run, max_retries)

    def _build_buyer_company_queryset(self, recently_updated: bool):
        """Build the queryset of buyer companies to process."""
        companies_qs = Company.objects.all()
        self.stdout_info(f"Total buyer companies in database: {Company.objects.count()}")

        if recently_updated:
            two_weeks_ago = timezone.now() - timedelta(weeks=2)
            companies_qs = companies_qs.filter(updated_at__gte=two_weeks_ago)
            self.stdout_info(f"Recently modified buyer companies: {companies_qs.count()}")

        return companies_qs.with_user_stats()  # type: ignore

    def _process_buyer_companies(self, companies_qs, dry_run: bool, max_retries: int):
        """Process each buyer company individually."""
        for company in companies_qs.iterator():
            try:
                self._process_single_buyer_company(company, dry_run, max_retries)
            except Exception as e:
                self.stats["errors"] += 1
                self.stdout_error(f"Error processing buyer company {company.id}: {str(e)}")

    def _process_single_buyer_company(self, company, dry_run: bool, max_retries: int):
        """Process a single buyer company."""
        new_extra_data = self._prepare_buyer_company_extra_data(company)
        extra_data_changed = self._update_buyer_company_extra_data_if_needed(company, new_extra_data, dry_run)
        self._sync_buyer_company_with_brevo_if_needed(company, extra_data_changed, dry_run, max_retries)

    def _prepare_buyer_company_extra_data(self, company) -> dict:
        """Prepare new extra_data for buyer company."""
        return {
            "user_count": company.user_count_annotated,
            "tender_count": company.user_tender_count_annotated,
        }

    def _update_buyer_company_extra_data_if_needed(self, company, new_extra_data: dict, dry_run: bool) -> bool:
        """Update buyer company extra_data if needed and return whether changes were made."""
        if company.extra_data.get("brevo_company_data") != new_extra_data:
            company.extra_data.update({"brevo_company_data": new_extra_data})
            if not dry_run:
                company.save(update_fields=["extra_data"])
            self.stats["extra_data_updated"] += 1
            return True
        return False

    def _sync_buyer_company_with_brevo_if_needed(
        self, company, extra_data_changed: bool, dry_run: bool, max_retries: int
    ):
        """Synchronize buyer company with Brevo if needed."""
        if not company.brevo_company_id or extra_data_changed:
            if not dry_run:
                api_brevo.create_or_update_buyer_company(company, max_retries=max_retries, retry_delay=5)

            if company.brevo_company_id:
                self.stats["updated"] += 1
            else:
                self.stats["created"] += 1
        else:
            self.stats["skipped"] += 1

    def _display_final_report(self):
        """Display final synchronization report."""
        total_processed = self.stats["created"] + self.stats["updated"] + self.stats["skipped"] + self.stats["errors"]
        self.stdout_info("-" * 80)
        self.stdout_info("Synchronization completed! Results:")
        self.stdout_info(f"- Total processed: {total_processed}/{self.stats['total']}")
        self.stdout_info(f"- Created: {self.stats['created']}")
        self.stdout_info(f"- Updated: {self.stats['updated']}")
        self.stdout_info(f"- Skipped (already up to date): {self.stats['skipped']}")
        self.stdout_info(f"- Extra data updated: {self.stats['extra_data_updated']}")
        self.stdout_info(f"- Errors: {self.stats['errors']}")
