from django.conf import settings
from sentry_sdk.crons import monitor

from lemarche.siaes.models import Siae
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Goal: update the 'super_badge' field of each Siae

    Note: some of these fields are updated on each Siae save()

    Usage:
    python manage.py update_siae_super_badge_field
    python manage.py update_siae_super_badge_field --id 1
    """

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, default=None, help="Indiquer l'ID d'une structure")

    @monitor(monitor_slug="update_siae_super_badge_field")
    def handle(self, *args, **options):
        self.stdout_messages_info("Updating Siae super_badge field...")

        siae_with_super_badge_count_before = Siae.objects.filter(super_badge=True).count()

        # Step 1: build the queryset
        siae_queryset = Siae.objects.all()
        if options["id"]:
            siae_queryset = siae_queryset.filter(id=options["id"])
        self.stdout_messages_info(f"Found {siae_queryset.count()} siaes")

        siaes = list(siae_queryset)

        # Step 2: loop on each Siae
        progress = 0
        for siae in siaes:
            # Step 3: compute super_badge field
            siae.set_super_badge()

            progress += 1
            if (progress % 500) == 0:
                self.stdout_info(f"{progress}...")

        # Step 4: bulk update
        Siae.objects.bulk_update(siaes, ["super_badge", "super_badge_last_updated"])

        siae_with_super_badge_count_after = Siae.objects.filter(super_badge=True).count()
        msg_success = [
            "----- Siae super_badge field -----",
            f"Done! Processed {siae_queryset.count()} siaes",
            f"Siaes with badge: before {siae_with_super_badge_count_before} / after {siae_with_super_badge_count_after}",  # noqa
        ]
        self.stdout_messages_success(msg_success)
        api_slack.send_message_to_channel("\n".join(msg_success), service_id=settings.SLACK_WEBHOOK_C4_SUPPORT_CHANNEL)
