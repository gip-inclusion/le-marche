from django.conf import settings

from lemarche.tenders.models import Tender
from lemarche.users.models import User
from lemarche.www.auth.tasks import send_new_user_password_reset_link


def create_tender_from_dict(tender_dict: dict) -> Tender:
    tender_dict.pop("contact_company_name", None)
    tender_dict.pop("id_location_name", None)
    location = tender_dict.get("location")
    sectors = tender_dict.pop("sectors", [])
    tender = Tender(**tender_dict)
    tender.save()
    if location:
        tender.perimeters.set([location])
    if sectors:
        tender.sectors.set(sectors)
    return tender


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


def get_or_create_user(request_user, tender_dict: dict):
    user: User = None
    if not request_user.is_authenticated:
        user = get_or_create_user_from_anonymous_content(tender_dict)
    else:
        user = request_user
        need_to_be_saved = False
        if not user.phone:
            user.phone = tender_dict.get("contact_phone")
            need_to_be_saved = True
        if not user.company_name:
            user.company_name = tender_dict.get("contact_company_name")
            need_to_be_saved = True
        if need_to_be_saved:
            user.save()
    return user
