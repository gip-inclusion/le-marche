from datetime import timedelta

from django.utils import timezone
from tqdm import tqdm

from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_brevo
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Script for synchronizing companies (SIAE) with Brevo CRM

    Features:
    - Complete or partial synchronization (recently modified companies)
    - Tracks statistics over 90 days for Brevo
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
            help="Synchronize only recently modified SIAEs",
        )
        parser.add_argument(
            "--max-retries",
            dest="max_retries",
            type=int,
            default=3,
            help="Maximum number of retry attempts in case of API error",
        )
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Simulation mode (no changes)")

    def handle(
        self,
        recently_updated: bool = False,
        max_retries: int = 3,
        dry_run: bool = False,
        **options,
    ):
        self.stdout_info("-" * 80)
        self.stdout_info("SIAE synchronization script with Brevo CRM (companies)...")
        # Build the queryset
        siaes_qs = self._build_queryset(recently_updated)

        # Initialize statistics
        self.stats["total"] = siaes_qs.count()

        if dry_run:
            self.stdout_info("Simulation mode enabled - no changes will be made")

        # Process SIAEs
        self._process_siaes(siaes_qs, dry_run, max_retries)

        # Display final report
        self._display_final_report()

    def _build_queryset(self, recently_updated: bool):
        """Build the queryset of SIAEs to process."""
        siaes_qs = Siae.objects.all()
        self.stdout_info(f"Total SIAEs in database: {Siae.objects.count()}")

        if recently_updated:
            two_weeks_ago = timezone.now() - timedelta(weeks=2)
            siaes_qs = siaes_qs.filter(updated_at__gte=two_weeks_ago)
            self.stdout_info(f"Recently modified SIAEs: {siaes_qs.count()}")

        return siaes_qs.with_tender_stats(since_days=90)  # type: ignore

    def _process_siaes(self, siaes_qs, dry_run: bool, max_retries: int):
        """Process each SIAE individually."""
        for siae in tqdm(siaes_qs.iterator(), total=siaes_qs.count(), desc="Synchronizing SIAEs"):
            try:
                self._process_single_siae(siae, dry_run, max_retries)
            except Exception as e:
                self.stats["errors"] += 1
                self.stdout_error(f"Error processing {siae.id}: {str(e)}")

    def _process_single_siae(self, siae, dry_run: bool, max_retries: int):
        """Process a single SIAE."""
        new_extra_data = self._prepare_extra_data(siae)
        extra_data_changed = self._update_extra_data_if_needed(siae, new_extra_data, dry_run)
        self._sync_with_brevo_if_needed(siae, extra_data_changed, dry_run, max_retries)

    def _prepare_extra_data(self, siae) -> dict:
        """Prepare new extra_data."""
        return {
            "completion_rate": siae.completion_rate,
            "tender_received": siae.tender_email_send_count_annotated,
            "tender_interest": siae.tender_detail_contact_click_count_annotated,
        }

    def _update_extra_data_if_needed(self, siae, new_extra_data: dict, dry_run: bool) -> bool:
        """Update extra_data if needed and return whether changes were made."""
        if siae.extra_data.get("brevo_company_data") != new_extra_data:
            siae.extra_data.update({"brevo_company_data": new_extra_data})
            if not dry_run:
                siae.save(update_fields=["extra_data"])
            self.stats["extra_data_updated"] += 1
            return True
        return False

    def _sync_with_brevo_if_needed(self, siae, extra_data_changed: bool, dry_run: bool, max_retries: int):
        """Synchronize with Brevo if needed."""
        if not siae.brevo_company_id or extra_data_changed:
            is_created_or_updated = False
            if not dry_run:
                is_created_or_updated = api_brevo.create_or_update_company(
                    siae, max_retries=max_retries, retry_delay=5
                )

            if not is_created_or_updated and not dry_run:
                self.stats["errors"] += 1
                self.stdout_error(f"Failed to create or update Brevo company for SIAE {siae.id}")
            elif siae.brevo_company_id:
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
        self.stdout_info(
            f"""- Total processed:
            {total_processed}/{self.stats['total']}"""
        )
        self.stdout_info(f"- Created: {self.stats['created']}")
        self.stdout_info(f"- Updated: {self.stats['updated']}")
        self.stdout_info(f"- Skipped (already up to date): {self.stats['skipped']}")
        self.stdout_info(f"- Extra data updated: {self.stats['extra_data_updated']}")
        self.stdout_info(f"- Errors: {self.stats['errors']}")
