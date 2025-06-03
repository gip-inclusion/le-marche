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

        # Statistics for final report
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0, "extra_data_updated": 0, "total": total_siaes}

        # Step 3: Process SIAEs in batches
        for siae in tqdm(siaes_qs.iterator(), total=siaes_qs.count(), desc="Synchronizing SIAEs"):
            # Prepare new data for extra_data
            new_extra_data = {
                "completion_rate": siae.completion_rate,
                "tender_received": siae.tender_email_send_count_annotated,
                "tender_interest": siae.tender_detail_contact_click_count_annotated,
            }

            # Update extra_data if necessary
            extra_data_changed = False
            if siae.extra_data.get("brevo_company_data") != new_extra_data:
                siae.extra_data.update({"brevo_company_data": new_extra_data})
                if not dry_run:
                    siae.save(update_fields=["extra_data"])
                extra_data_changed = True
                stats["extra_data_updated"] += 1

                try:
                    # If it's a new SIAE (without Brevo ID) or if extra_data has changed
                    if not siae.brevo_company_id or extra_data_changed:
                        if not dry_run:
                            api_brevo.create_or_update_company(siae, max_retries=max_retries, retry_delay=5)

                        if siae.brevo_company_id:
                            stats["updated"] += 1
                        else:
                            stats["created"] += 1
                    else:
                        stats["skipped"] += 1

                except Exception as e:
                    stats["errors"] += 1
                    self.stdout_error(f"Error processing {siae.id}: {str(e)}")

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
