from django.urls import reverse_lazy
from huey.contrib.djhuey import task

from lemarche.conversations.models import TemplateTransactional
from lemarche.users.models import User
from lemarche.utils.apis.geocoding import get_geocoding_data
from lemarche.utils.emails import whitelist_recipient_list
from lemarche.utils.urls import get_domain_url, get_object_share_url


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
    email_template = TemplateTransactional.objects.get(code="SIAE_COMPLETION_REMINDER")
    siae_user_emails = list(siae.users.values_list("email", flat=True))
    recipient_list = whitelist_recipient_list(siae_user_emails)
    if len(recipient_list):
        for recipient_email in recipient_list:
            siae_user = User.objects.get(email=recipient_email)
            recipient_name = siae_user.full_name

            variables = {
                "SIAE_USER_ID": siae_user.id,
                "SIAE_USER_FIRST_NAME": siae_user.first_name,
                "SIAE_ID": siae.id,
                "SIAE_NAME": siae.name_display,
                "SIAE_CONTACT_EMAIL": siae.contact_email,
                "SIAE_SECTOR_COUNT": siae.sector_count,
                "SIAE_URL": get_object_share_url(siae),
                "SIAE_EDIT_URL": f"https://{get_domain_url()}{reverse_lazy('dashboard_siaes:siae_edit_contact', args=[siae.slug])}",  # noqa
            }

            email_template.send_transactional_email(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                variables=variables,
                recipient_content_object=siae_user,
                parent_content_object=siae,
            )


@task()
def send_reminder_email_to_siae(siae, message, tender_url):
    email_template = TemplateTransactional.objects.get(code="SIAE_REMINDER")

    variables = {
        "MESSAGE": message,
        "TENDER_URL": tender_url,
    }

    email_template.send_transactional_email(
        subject="Êtes-vous intéressé par mon projet d'achat ?",
        from_email="commercial@lemarche.inclusion.beta.gouv.fr",
        from_name="L'équipe du Marché de l'inclusion",
        recipient_email=siae.contact_email,
        recipient_name=siae.contact_full_name,
        variables=variables,
    )
