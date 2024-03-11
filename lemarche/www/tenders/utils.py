from django.conf import settings

from lemarche.tenders import constants as tender_constants
from lemarche.tenders.models import Tender, TenderQuestion
from lemarche.users import constants as user_constants
from lemarche.users.models import User
from lemarche.www.auth.tasks import add_to_contact_list, send_new_user_password_reset_link


def create_questions_list(tender, questions_list):
    return TenderQuestion.objects.bulk_create(
        [TenderQuestion(tender=tender, **values) for values in questions_list], batch_size=100
    )


def update_or_create_questions_list(tender, questions_list):
    if questions_list:
        questions_to_update = []
        questions_to_create = []
        for q in questions_list:
            if q.get("id"):
                questions_to_update.append(q)
            else:
                # new question
                questions_to_create.append(q)
        if questions_to_create:
            create_questions_list(tender, questions_list=questions_to_create)
        if questions_to_update:
            TenderQuestion.objects.bulk_update(
                [
                    TenderQuestion(id=values.get("id"), tender=tender, text=values.get("text"))
                    for values in questions_to_update
                ],
                ["text"],
                batch_size=1000,
            )


def create_tender_from_dict(tender_dict: dict) -> Tender:
    tender_dict.pop("contact_company_name", None)
    tender_dict.pop("id_location_name", None)
    location = tender_dict.get("location")
    sectors = tender_dict.pop("sectors", [])
    questions = tender_dict.pop("questions_list")
    tender: Tender = Tender(**tender_dict)
    tender.save()
    if location:
        tender.perimeters.set([location])
    if sectors:
        tender.sectors.set(sectors)
    if questions:
        create_questions_list(tender, questions_list=questions)
    return tender


def get_or_create_user_from_anonymous_content(
    tender_dict: dict, source: str = user_constants.SOURCE_TENDER_FORM
) -> User:
    email = tender_dict.get("contact_email").lower()
    kind = (
        tender_dict.get("contact_kind")
        if tender_dict.get("contact_kind")
        else (User.KIND_BUYER if tender_dict.get("contact_company_name") else User.KIND_INDIVIDUAL)
    )
    buyer_kind_detail = tender_dict.get("contact_buyer_kind_detail", "")
    company_name = tender_dict.get("contact_company_name", "")
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "first_name": tender_dict.get("contact_first_name"),
            "last_name": tender_dict.get("contact_last_name"),
            "phone": tender_dict.get("contact_phone"),
            "kind": kind,
            "buyer_kind_detail": buyer_kind_detail,
            "company_name": company_name,
            "source": source,
        },
    )
    if created and settings.BITOUBI_ENV == "prod":
        send_new_user_password_reset_link(user)
        add_to_contact_list(user=user, type="signup", source=source)
    return user


def get_or_create_user(request_user, tender_dict: dict, source=user_constants.SOURCE_TENDER_FORM):
    user: User = None
    if not request_user.is_authenticated:
        user = get_or_create_user_from_anonymous_content(tender_dict, source=source)
    else:
        user = request_user
        need_to_be_saved = False
        if not user.phone:
            user.phone = tender_dict.get("contact_phone", "")
            need_to_be_saved = True
        if not user.company_name:
            user.company_name = tender_dict.get("contact_company_name")
            need_to_be_saved = True
        if need_to_be_saved:
            user.save()
    return user


FIELDS_TO_REMOVE = ["siae_transactioned", "extra_data", "import_raw_object"] + Tender.READONLY_FIELDS


def duplicate(tender: Tender, fields_to_remove=FIELDS_TO_REMOVE) -> Tender:
    fields_to_remove_full = ["id", "slug"] + fields_to_remove
    # other rule: fields starting with "_" : "_state", "_django_version", "__previous_siae_transactioned",
    fields_to_keep = [
        field_name
        for field_name in tender.__dict__.keys()
        if (field_name not in fields_to_remove_full and not field_name.startswith("_"))
    ]
    # sectors  # managed post-create

    new_tender_dict = dict()
    for key in fields_to_keep:
        new_tender_dict[key] = tender.__dict__[key]

    # overwrite some fields
    new_tender_dict["status"] = tender_constants.STATUS_PUBLISHED
    new_tender_dict["source"] = tender_constants.SOURCE_STAFF_C4_CREATED
    new_tender_dict["logs"] = [{"action": "tender_duplicated", "from": tender.id}]

    # create duplicate tender
    new_tender = Tender.objects.create(**new_tender_dict)
    new_tender.sectors.set(tender.sectors.all())

    return new_tender
