from collections import Counter

from lemarche.utils.apis import api_hubspot
from lemarche.utils.commands import BaseCommand


NOTE_AUTHOR_MAPPING = {"487714245": 4390, "487707585": 691, "497353929": 1504}


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
        print(notes[0]["properties"]["hs_note_body"])
        print(api_hubspot.cleanup_note_html(notes[0]["properties"]["hs_note_body"]))
        print(notes[1]["properties"]["hs_note_body"])
        print(api_hubspot.cleanup_note_html(notes[1]["properties"]["hs_note_body"]))
        print(notes[2]["properties"]["hs_note_body"])
        print(api_hubspot.cleanup_note_html(notes[2]["properties"]["hs_note_body"]))

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
