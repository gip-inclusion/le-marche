from django.conf import settings
from django.urls import reverse_lazy
from django.utils import timezone
from huey.contrib.djhuey import task

from lemarche.users.models import User
from lemarche.utils.apis import api_mailjet
from lemarche.utils.apis.geocoding import get_geocoding_data
from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url, get_share_url_object


@task()
def set_siae_coords(model, siae):
    """
    Why do we use filter+update here? To avoid calling Siae.post_save signal again (recursion)
    """
    geocoding_data = get_geocoding_data(siae.address + " " + siae.city, post_code=siae.post_code)
    if geocoding_data:
        if siae.post_code != geocoding_data["post_code"]:
            if not siae.post_code or (siae.post_code[:2] == geocoding_data["post_code"][:2]):
                # update post_code as well
                model.objects.filter(id=siae.id).update(
                    coords=geocoding_data["coords"], post_code=geocoding_data["post_code"]
                )
            else:
                print(
                    f"Geocoding found a different place,{siae.name},{siae.post_code},{geocoding_data['post_code']}"  # noqa
                )
        else:
            # s.coords = geocoding_data["coords"]
            model.objects.filter(id=siae.id).update(coords=geocoding_data["coords"])
    else:
        print(f"Geocoding not found,{siae.name},{siae.post_code}")


def send_completion_reminder_email_to_siae(siae):
    email_subject = "Vous avez raté des opportunités commerciales !"
    siae_user_emails = list(siae.users.values_list("email", flat=True))
    recipient_list = whitelist_recipient_list(siae_user_emails)
    if recipient_list:
        for siae_user_email in recipient_list:
            siae_user = User.objects.get(email=siae_user_email)
            recipient_name = siae_user.full_name

            variables = {
                "SIAE_USER_FIRST_NAME": siae_user.first_name,
                "SIAE_NAME": siae.name_display,
                "SIAE_URL": get_share_url_object(siae),
                "SIAE_EDIT_URL": f"https://{get_domain_url()}{reverse_lazy('dashboard_siaes:siae_edit_contact', args=[siae.slug])}",  # noqa
            }

            api_mailjet.send_transactional_email_with_template(
                template_id=settings.MAILJET_SIAE_COMPLETION_REMINDER_TEMPLATE_ID,
                subject=email_subject,
                recipient_email=siae_user_email,
                recipient_name=recipient_name,
                variables=variables,
            )

        # log email
        log_item = {
            "action": "email_completion_reminder",
            "email_to": recipient_list,
            "email_subject": email_subject,
            # "email_body": email_body,
            "email_timestamp": timezone.now().isoformat(),
            "metadata": {
                "sector_count": siae.sector_count,
                "contact_email": True if len(siae.contact_email) else False,
            },
        }
        siae.logs.append(log_item)
        siae.save()
