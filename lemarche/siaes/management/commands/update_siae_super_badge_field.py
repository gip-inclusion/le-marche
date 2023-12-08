import calendar

from django.core.management.base import CommandError
from django.utils import timezone

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
    python manage.py update_siae_super_badge_field --day-of-week 0 --day-of-month last
    """

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, default=None, help="Indiquer l'ID d'une structure")
        parser.add_argument(
            "--day-of-week",
            dest="day_of_week",
            type=int,
            help="Lundi = 0 ; Dimanche = 6",
        )
        parser.add_argument(
            "--day-of-month",
            dest="day_of_month",
            type=str,
            help="'first' for the first weekday of the month ; 'last' for the last weekday of the month",
        )

    def handle(self, *args, **options):
        self.stdout_messages_info("Updating Siae super_badge field...")

        if options["day_of_week"] is not None:
            if options["day_of_week"] != timezone.now().weekday():
                raise CommandError("Day of week not compatible with day_of_week parameter. Stopping.")

        if options["day_of_month"] is not None:
            current_year = timezone.now().year
            current_month = timezone.now().month
            current_day = timezone.now().day
            current_month_day_count = calendar.monthrange(year=current_year, month=current_month)[1]
            if (options["day_of_month"] == "first") and (current_day > 7):
                raise CommandError("Not the first weekday of the month. Stopping.")
            elif (options["day_of_month"] == "last") and (current_month_day_count - current_day >= 7):
                raise CommandError("Not the last weekday of the month. Stopping.")

        siae_with_super_badge_count_before = Siae.objects.filter(super_badge=True).count()

        # Step 1: build the queryset
        siae_queryset = Siae.objects.all()
        if options["id"]:
            siae_queryset = siae_queryset.filter(id=options["id"])
        self.stdout_messages_info(f"Found {siae_queryset.count()} siaes")

        # Step 2: loop on each Siae
        progress = 0
        for index, siae in enumerate(siae_queryset):
            # Step 3: update super_badge field
            siae.set_super_badge()

            progress += 1
            if (progress % 500) == 0:
                self.stdout_info(f"{progress}...")

        siae_with_super_badge_count_after = Siae.objects.filter(super_badge=True).count()
        msg_success = [
            "----- Siae super_badge field -----",
            f"Done! Processed {siae_queryset.count()} siaes",
            f"Siaes with badge: before {siae_with_super_badge_count_before} / after {siae_with_super_badge_count_after}",  # noqa
        ]
        self.stdout_messages_success(msg_success)
        api_slack.send_message_to_channel("\n".join(msg_success))
