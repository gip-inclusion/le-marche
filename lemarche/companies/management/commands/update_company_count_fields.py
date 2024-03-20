from lemarche.companies.models import Company
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Goal: update the '_count' fields of each Company

    Usage:
    - poetry run python manage.py update_company_count_fields
    """

    def handle(self, *args, **options):
        self.stdout_messages_info("Updating Company count fields...")

        # Step 1a: build the queryset
        company_queryset = Company.objects.has_email_domain().with_user_stats()
        self.stdout_messages_info(f"Found {company_queryset.count()} companies with an email_domain")

        # Step 1b: init fields to update
        update_fields = Company.FIELDS_STATS_COUNT
        self.stdout_messages_info(f"Fields to update: {update_fields}")

        # Step 2: loop on each Company with an email domain
        progress = 0
        for index, company in enumerate(company_queryset):
            company.user_count = company.user_count_annotated
            company.user_tender_count = company.user_tender_count_annotated

            # Step 3: update count fields
            company.save(update_fields=update_fields)

            progress += 1
            if (progress % 50) == 0:
                self.stdout_info(f"{progress}...")

        msg_success = [
            "----- Company count fields -----",
            f"Done! Processed {company_queryset.count()} companies with an email_domain",
            f"Fields updated: {update_fields}",
        ]
        self.stdout_messages_success(msg_success)
        api_slack.send_message_to_channel("\n".join(msg_success))
