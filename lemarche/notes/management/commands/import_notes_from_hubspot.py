from collections import Counter

from lemarche.notes.models import Note
from lemarche.tenders.models import Tender
from lemarche.users.models import User
from lemarche.utils.apis import api_hubspot
from lemarche.utils.commands import BaseCommand


NOTE_AUTHOR_MAPPING = {"487714245": 4390, "487707585": 691, "497353929": 1504, None: None}


class Command(BaseCommand):
    def handle(self, *args, **options):
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
        # print(notes[0]["properties"]["hs_note_body"])
        # print(api_hubspot.cleanup_note_html(notes[0]["properties"]["hs_note_body"]))
        # print(notes[1]["properties"]["hs_note_body"])
        # print(api_hubspot.cleanup_note_html(notes[1]["properties"]["hs_note_body"]))
        # print(notes[2]["properties"]["hs_note_body"])
        # print(api_hubspot.cleanup_note_html(notes[2]["properties"]["hs_note_body"]))

        notes_contacts = [
            n["associations"]["contacts"]
            for n in notes
            if (n.get("associations") and n["associations"].get("contacts"))
        ]
        print("notes > contacts", len(notes_contacts))
        notes_deals = [
            n["associations"]["deals"] for n in notes if (n.get("associations") and n["associations"].get("deals"))
        ]
        print("notes > deals", len(notes_deals))
        notes_companies = [
            n["associations"]["companies"]
            for n in notes
            if (n.get("associations") and n["associations"].get("companies"))
        ]
        print("notes > companies", len(notes_companies))
        notes_deals_with_contact = [
            n
            for n in notes
            if (n.get("associations") and n["associations"].get("contacts") and n["associations"].get("deals"))
        ]
        print("notes > deals with contact", len(notes_deals_with_contact))
        notes_authors = [n["properties"]["hubspot_owner_id"] for n in notes]
        print("notes > author count", Counter(notes_authors))

        for note in notes[:10]:
            self.create_note(note)

    def create_note(self, hubspot_note_dict):
        note_dict = dict()

        # basics
        note_dict["text"] = api_hubspot.cleanup_note_html(hubspot_note_dict["properties"]["hs_note_body"])
        note_dict["author_id"] = NOTE_AUTHOR_MAPPING[hubspot_note_dict["properties"]["hubspot_owner_id"]]
        note_dict["created_at"] = hubspot_note_dict["created_at"]
        note_dict["updated_at"] = hubspot_note_dict["updated_at"]

        # relation
        if hubspot_note_dict.get("associations"):
            if hubspot_note_dict["associations"].get("deals"):
                print("deal")
                deal_id = hubspot_note_dict["associations"]["deals"]["results"][0]["id"]
                hubspot_deal_dict = api_hubspot.get_deal(deal_id)
                Tender.objects.filter(created_at__date=hubspot_deal_dict.created_at.date())
                # Note.objects.create(note_dict)
            elif hubspot_note_dict["associations"].get("contacts"):
                print("contact")
                contact_id = hubspot_note_dict["associations"]["contacts"]["results"][0]["id"]
                hubspot_contact_dict = api_hubspot.get_contact(contact_id)
                user = User.objects.get(email=hubspot_contact_dict["properties"]["email"])
                note_dict["content_object"] = user
            else:
                print("Note with association, but not deal or contact", hubspot_note_dict["id"])
        else:
            print("Note without association", hubspot_note_dict["id"])

        if note_dict["content_object"]:
            Note.objects.create(**note_dict)
