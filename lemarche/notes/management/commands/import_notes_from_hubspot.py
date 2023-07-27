from collections import Counter

from lemarche.notes.models import Note
from lemarche.tenders.models import Tender
from lemarche.users.models import User
from lemarche.utils.apis import api_hubspot
from lemarche.utils.commands import BaseCommand


NOTE_AUTHOR_MAPPING = {"487714245": 4390, "487707585": 691, "497353929": 1504, None: None}


class Command(BaseCommand):
    """
    One-shot command to import notes from Hubspot

    Notes were created on 3 types of objects:
    - contacts (Users)
    - deals (Tenders)
    - companies (Siaes or other ?)

    Usage:
    python manage.py import_notes_from_hubspot
    """

    def handle(self, *args, **options):  # noqa C901
        # contacts
        contacts = api_hubspot.get_all_contacts()
        print("contacts count", len(contacts))
        # print(contacts[0])

        # deals
        deals = api_hubspot.get_all_deals()
        print("deals count", len(deals))
        # print(deals[0])

        # companies
        companies = api_hubspot.get_all_companies()
        print("companies count", len(companies))
        # print(companies[0])

        # notes
        notes = api_hubspot.get_all_notes()
        print("notes count", len(notes))

        notes_contacts = [n for n in notes if (n.get("associations") and n["associations"].get("contacts"))]
        print("notes > contacts", len(notes_contacts))
        notes_deals = [n for n in notes if (n.get("associations") and n["associations"].get("deals"))]
        print("notes > deals", len(notes_deals))
        notes_companies = [n for n in notes if (n.get("associations") and n["associations"].get("companies"))]
        print("notes > companies", len(notes_companies))
        notes_deals_with_contact = [
            n
            for n in notes
            if (n.get("associations") and n["associations"].get("contacts") and n["associations"].get("deals"))
        ]
        print("notes > deals with contact", len(notes_deals_with_contact))
        notes_authors = [n["properties"]["hubspot_owner_id"] for n in notes]
        print("notes > author count", Counter(notes_authors))

        print("=====================")
        results = {
            "progress": 0,
            "empty_body": 0,
            "empty_deal_or_contact": 0,
            "empty_association": 0,
            "deal_tender_author_empty": 0,
            "deal_tender_not_found": 0,
            "deal_tender_multiple": 0,
            "deal_tender_ok": 0,
            "contact_user_not_found": 0,
            "contact_user_multiple": 0,
            "contact_user_ok": 0,
        }
        for hubspot_note_dict in notes:
            note_dict = dict()
            note_body_raw = hubspot_note_dict["properties"]["hs_note_body"]

            if note_body_raw and note_body_raw.startswith("<div"):
                # basics
                note_dict["text"] = api_hubspot.cleanup_note_html(note_body_raw)
                note_dict["author_id"] = NOTE_AUTHOR_MAPPING[hubspot_note_dict["properties"]["hubspot_owner_id"]]
                note_dict["created_at"] = hubspot_note_dict["created_at"]
                note_dict["updated_at"] = hubspot_note_dict["updated_at"]

                # relation
                if hubspot_note_dict.get("associations"):
                    if hubspot_note_dict["associations"].get("deals"):
                        deal_id = hubspot_note_dict["associations"]["deals"]["results"][0]["id"]
                        hubspot_deal_dict = api_hubspot.get_deal(deal_id)
                        if hubspot_deal_dict.get("associations") and hubspot_deal_dict["associations"].get("contacts"):
                            hubspot_deal_contact_id = hubspot_deal_dict["associations"]["contacts"]["results"][0]["id"]
                            hubspot_deal_contact_dict = api_hubspot.get_contact(hubspot_deal_contact_id)
                            tenders = Tender.objects.filter(
                                author__email=hubspot_deal_contact_dict["properties"]["email"]
                            )
                            if tenders.count() == 0:
                                results["deal_tender_not_found"] += 1
                            elif tenders.count() == 2:
                                results["deal_tender_multiple"] += 1
                            else:
                                note_dict["content_object"] = tenders.first()
                                results["deal_tender_ok"] += 1
                        else:
                            results["deal_tender_author_empty"] += 1
                    elif hubspot_note_dict["associations"].get("contacts"):
                        contact_id = hubspot_note_dict["associations"]["contacts"]["results"][0]["id"]
                        hubspot_contact_dict = api_hubspot.get_contact(contact_id)
                        users = User.objects.filter(email=hubspot_contact_dict["properties"]["email"])
                        if users.count() == 0:
                            results["contact_user_not_found"] += 1
                        elif users.count() == 2:
                            results["contact_user_multiple"] += 1
                        else:
                            note_dict["content_object"] = users.first()
                            results["contact_user_ok"] += 1
                    else:
                        results["empty_deal_or_contact"] += 1
                else:
                    results["empty_association"] += 1

                if note_dict.get("content_object"):
                    Note.objects.create(**note_dict)

            else:
                results["empty_body"] += 1

            results["progress"] += 1
            if (results["progress"] % 100) == 0:
                print(results["progress"])

        print(results)
