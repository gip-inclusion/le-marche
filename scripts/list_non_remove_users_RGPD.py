import datetime
import time

from brevo_python.rest import ApiException
from django.utils import timezone

from lemarche.users.models import User
from lemarche.utils.apis.api_brevo import BrevoTransactionalEmailApiClient


# 1. Configuration
TEMPLATE_ID = 472
LIMIT_PER_PAGE = 1000


api_instance = BrevoTransactionalEmailApiClient().api_instance


offset = 0
all_emails = {}
one_month_ago = timezone.localdate() - datetime.timedelta(days=30)

try:
    while True:
        result = api_instance.get_transac_emails_list(
            template_id=472,
            start_date="2026-03-01",
            end_date=str(one_month_ago),
            limit=LIMIT_PER_PAGE,
            offset=offset,
        )

        transactional_emails = result.transactional_emails

        # Si la page est vide, on a fini de tout récupérer
        if not transactional_emails:
            break

        for email in result.transactional_emails:
            all_emails[email.email] = email._date[:10]

        # Si on a reçu moins d'événements que la limite, c'est la dernière page
        if len(transactional_emails) < LIMIT_PER_PAGE:
            break

        # Incrémentation de l'offset pour la page suivante
        offset += LIMIT_PER_PAGE
        time.sleep(0.1)

except ApiException as e:
    print(f"Erreur lors de l'appel API : {e}")


remaining_users = list(
    User.objects.filter(email__in=all_emails, date_joined__gte=one_month_ago).values_list("email", flat=True)
)

for email in remaining_users:
    print(f"{email}:{all_emails[email]}")
