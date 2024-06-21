from django.utils import timezone


def last_year() -> int:
    return timezone.now().year - 1
