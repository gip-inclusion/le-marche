"""When the anonymizing user feature will be deployed first, there is a possibility that some users are already
inactive since a long time, and could be removed before reaching the warning period.
We set their last_login date just before, so they can receive the warning email and act before their account is
anonymized
"""

from django.db import migrations
from django.conf import settings
from django.utils import timezone

from dateutil.relativedelta import relativedelta


def update_last_login(apps, schema_editor):
    User = apps.get_model("users", "User")
    expiry_date = timezone.now() - relativedelta(months=settings.INACTIVE_USER_TIMEOUT_IN_MONTHS)
    warning_date = expiry_date + relativedelta(days=settings.INACTIVE_USER_WARNING_DELAY_IN_DAYS)

    # select inactive users about to be deleted
    qs = User.objects.filter(last_login__lte=expiry_date)
    # Set their last login few days before the fatal date, so they can be warned by auto email
    qs.update(last_login=warning_date)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0042_email_template_anonymise_user"),
    ]

    operations = [
        migrations.RunPython(update_last_login, reverse_code=migrations.RunPython.noop),
    ]
