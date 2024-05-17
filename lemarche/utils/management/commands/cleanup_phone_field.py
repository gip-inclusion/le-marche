from django.apps import apps
from django.core.management.base import BaseCommand

from lemarche.utils.data import phone_number_is_valid


DEFAULT_COUNTRY_CODE = "+33"


class Command(BaseCommand):
    """
    This script is used to validate existing phone numbers
    And cleanup / replace them with valid numbers (with +33)

    Usage:
    python manage.py cleanup_phone_field --model users.User --field phone --dry-run
    python manage.py cleanup_phone_field --model tenders.Tender --field contact_phone --dry-run

    """

    def add_arguments(self, parser):
        parser.add_argument("--model", dest="model", default="users.User", help="Model to update")
        parser.add_argument("--field", dest="field", default="phone", help="Field where the phone number is stored")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")

    def handle(self, *args, **options):  # noqa C901
        self.stdout.write("-" * 80)
        model_name = options["model"].split(".")[1]
        field_name = options["field"]
        Model = apps.get_model(options["model"].split(".")[0], model_name)
        self.stdout.write(f"{model_name}: {Model.objects.count()}")
        qs = Model.objects.exclude(**{field_name: ""})
        self.stdout.write(f"{model_name} with a {field_name}: {qs.count()}")

        stats = {"has_dot_count": 0, "has_space_count": 0, "valid_count": 0, "invalid_count": 0, "update_count": 0}
        invalid_list = list()

        for index, item in enumerate(qs):
            item_phone = item_phone_cleaned = str(getattr(item, field_name))

            # cleanup phone number
            # example: "06.06.06.06.06" -> "0606060606"
            # example: "06 06 06 06 06" -> "0606060606"
            if "." in item_phone_cleaned:
                stats["has_dot_count"] += 1
                item_phone_cleaned = item_phone_cleaned.replace(".", "")
            if " " in item_phone:
                stats["has_space_count"] += 1
                item_phone_cleaned = item_phone_cleaned.replace(" ", "")

            # try to add +33 to phone numbers without country code
            # check that the phone number is valid before saving it
            # example: "0606060606" -> "+33606060606"
            if item_phone_cleaned.isdigit() and len(item_phone_cleaned) == 10:
                item_phone_cleaned_with_prefix = f"{DEFAULT_COUNTRY_CODE}{item_phone_cleaned[1:]}"
                if phone_number_is_valid(item_phone_cleaned_with_prefix):
                    item_phone_cleaned = item_phone_cleaned_with_prefix

            # if the final phone number is valid, save it
            if phone_number_is_valid(item_phone_cleaned):
                stats["valid_count"] += 1
                if item_phone != item_phone_cleaned:
                    stats["update_count"] += 1
                    if not options["dry_run"]:
                        setattr(item, field_name, item_phone_cleaned)
                        item.save(update_fields=[field_name])
            else:
                stats["invalid_count"] += 1
                invalid_list.append(item_phone)

        print(stats)
        # for num in invalid_list:
        #     print(num)
