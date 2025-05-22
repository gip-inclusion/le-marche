import logging
import time
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from tqdm import tqdm

from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_brevo
from lemarche.utils.commands import BaseCommand


logger = logging.getLogger(__name__)


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

    def add_arguments(self, parser):
        parser.add_argument(
            "--recently-updated",
            dest="recently_updated",
            action="store_true",
            help="Synchronize only recently modified SIAEs",
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

    def handle(
        self,
        recently_updated: bool = False,
        batch_size: int = 50,
        max_retries: int = 3,
        dry_run: bool = False,
        **options,
    ):
        self.stdout_info("-" * 80)
        self.stdout_info("SIAE synchronization script with Brevo CRM (companies)...")

        # Step 1: Build the query and filter SIAEs
        siaes_qs = Siae.objects.all()
        self.stdout_info(f"Total SIAEs in database: {Siae.objects.count()}")

        # Update only recently modified SIAEs
        if recently_updated:
            two_weeks_ago = timezone.now() - timedelta(weeks=2)
            siaes_qs = siaes_qs.filter(updated_at__gte=two_weeks_ago)
            self.stdout_info(f"Recently modified SIAEs: {siaes_qs.count()}")

        # Step 2: Add annotations for 90-day statistics
        siaes_qs = siaes_qs.with_tender_stats(since_days=90)

        # Final total of SIAEs to process
        total_siaes = siaes_qs.count()

        if dry_run:
            self.stdout_info("Simulation mode enabled - no changes will be made")
            return

        # Statistics for final report
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0, "extra_data_updated": 0, "total": total_siaes}

        # Step 3: Process SIAEs in batches
        for batch_start in tqdm(range(0, total_siaes, batch_size), desc="Synchronizing SIAEs"):
            batch_end = batch_start + batch_size
            batch_siaes = siaes_qs[batch_start:batch_end]

            for siae in batch_siaes:
                retry_count = 0
                success = False

                # Prepare new data for extra_data
                new_extra_data = {
                    "completion_rate": siae.completion_rate if siae.completion_rate is not None else 0,
                    "tender_received": siae.tender_email_send_count_annotated,
                    "tender_interest": siae.tender_detail_contact_click_count_annotated,
                }

                # Update extra_data if necessary
                extra_data_changed = False
                if siae.extra_data.get("brevo_company_data") != new_extra_data:
                    with transaction.atomic():
                        siae.extra_data.update({"brevo_company_data": new_extra_data})
                        siae.save(update_fields=["extra_data"])
                        extra_data_changed = True
                        stats["extra_data_updated"] += 1

                # Synchronize with Brevo with retry mechanism
                while retry_count < max_retries and not success:
                    try:
                        # If it's a new SIAE (without Brevo ID) or if extra_data has changed
                        if not siae.brevo_company_id or extra_data_changed:
                            api_brevo.create_or_update_company(siae)

                            if siae.brevo_company_id:
                                stats["updated"] += 1
                            else:
                                stats["created"] += 1
                        else:
                            stats["skipped"] += 1

                        success = True

                    except Exception as e:
                        retry_count += 1
                        wait_time = 2**retry_count  # Exponential backoff

                        if retry_count >= max_retries:
                            stats["errors"] += 1
                            self.stdout_error(
                                f"Failed after {max_retries} attempts for SIAE {siae.id} ({siae.name}): {str(e)}"
                            )
                        else:
                            self.stdout_warning(
                                f"Error synchronizing SIAE {siae.id}, "
                                f"attempt {retry_count}/{max_retries} in {wait_time}s: {str(e)}"
                            )
                            time.sleep(wait_time)

                # Pause to avoid API rate limiting
                count = 0
                for i, item in enumerate(batch_siaes):
                    if item.id == siae.id:
                        count = i
                        break
                if count % 10 == 0 and count > 0:
                    time.sleep(1)

        # Final report
        self.stdout_info("-" * 80)
        self.stdout_info("Synchronization completed! Results:")
        self.stdout_info(
            "- Total processed: "
            + f"{stats['created'] + stats['updated'] + stats['skipped'] + stats['errors']}/{stats['total']}"
        )
        self.stdout_info(f"- Created: {stats['created']}")
        self.stdout_info(f"- Updated: {stats['updated']}")
        self.stdout_info(f"- Skipped (already up to date): {stats['skipped']}")
        self.stdout_info(f"- Extra data updated: {stats['extra_data_updated']}")
        self.stdout_info(f"- Errors: {stats['errors']}")
