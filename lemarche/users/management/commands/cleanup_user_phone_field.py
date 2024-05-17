from django.core.management.base import BaseCommand

from lemarche.users.models import User
from lemarche.utils.data import phone_number_is_valid


DEFAULT_COUNTRY_CODE = "+33"


class Command(BaseCommand):
    """
    This script is used to validate existing user phone numbers
    And cleanup / replace them with valid numbers (with +33)

    Usage:
    python manage.py cleanup_user_phone_field
    python manage.py cleanup_user_phone_field --dry-run
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")

    def handle(self, *args, **options):  # noqa C901
        self.stdout.write("-" * 80)
        self.stdout.write(f"Users: {User.objects.count()}")
        qs = User.objects.exclude(phone="")
        self.stdout.write(f"Users with a phone: {qs.count()}")

        stats = {"has_dot_count": 0, "has_space_count": 0, "valid_count": 0, "invalid_count": 0, "update_count": 0}
        invalid_list = list()

        for index, user in enumerate(qs):
            user_phone = str(user.phone)

            # cleanup phone number
            # example: "06.06.06.06.06" -> "0606060606"
            # example: "06 06 06 06 06" -> "0606060606"
            if "." in user_phone:
                stats["has_dot_count"] += 1
                user_phone = user_phone.replace(".", "")
            if " " in user_phone:
                stats["has_space_count"] += 1
                user_phone = user_phone.replace(" ", "")

            # try to add +33 to phone numbers without country code
            # check that the phone number is valid before saving it
            # example: "0606060606" -> "+33606060606"
            if user_phone.isdigit() and len(user_phone) == 10:
                user_phone_tentative = f"{DEFAULT_COUNTRY_CODE}{user_phone[1:]}"
                if phone_number_is_valid(user_phone_tentative):
                    user_phone = user_phone_tentative

            # if the final phone number is valid, save it
            if phone_number_is_valid(user_phone):
                stats["valid_count"] += 1
                if user.phone != user_phone:
                    stats["update_count"] += 1
                    if not options["dry_run"]:
                        user.phone = user_phone
                        user.save(update_fields=["phone"])
            else:
                stats["invalid_count"] += 1
                invalid_list.append(user_phone)

        print(stats)
        # for num in invalid_list:
        #     print(num)
