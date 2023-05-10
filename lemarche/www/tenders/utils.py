from django.conf import settings

from lemarche.users.models import User
from lemarche.www.auth.tasks import send_new_user_password_reset_link


def get_or_create_user_from_anonymous_content(tender_dict: dict) -> User:
    email = tender_dict.get("contact_email").lower()
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "first_name": tender_dict.get("contact_first_name"),
            "last_name": tender_dict.get("contact_last_name"),
            "phone": tender_dict.get("contact_phone"),
            "company_name": tender_dict.pop("contact_company_name")
            if tender_dict.get("contact_company_name")
            else "Particulier",
            "kind": User.KIND_BUYER,  # not necessarily true, could be a PARTNER
            "source": User.SOURCE_TENDER_FORM,
        },
    )
    if created and settings.BITOUBI_ENV == "prod":
        send_new_user_password_reset_link(user)
    return user
