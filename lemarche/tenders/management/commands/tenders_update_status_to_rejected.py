from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from lemarche.tenders.models import Tender
from lemarche.www.tenders.tasks import send_tender_author_reject_message


class Command(BaseCommand):
    help = "Si aucune modification n'est apportée dans les 10 jours suivant la demande, le Besoin est rejeté."

    def handle(self, *args, **options):
        threshold_date = timezone.now() - timedelta(days=10)
        tenders_to_update = []

        tenders_draft = Tender.objects.filter(
            status=Tender.StatusChoices.STATUS_DRAFT, email_sent_for_modification=True
        )
        tenders_draft_count = tenders_draft.count()

        self.stdout.write(f"Besoin(s) à traiter : {tenders_draft_count}")

        for tender in tenders_draft:
            email_sent_at = None
            for log_entry in tender.logs:
                if log_entry.get("action") == "send tender author modification request":
                    email_sent_at = log_entry.get("date")
                    break

            if email_sent_at:
                email_sent_at_date = timezone.datetime.fromisoformat(email_sent_at)
                if email_sent_at_date <= threshold_date:
                    tenders_to_update.append(tender)

        for tender in tenders_to_update:
            tender.set_rejected()
            send_tender_author_reject_message(tender=tender)

        if not tenders_to_update:
            self.stdout.write("Aucun besoin rejeté")
        elif len(tenders_to_update) == 1:
            self.stdout.write("1 besoin rejeté")
        else:
            self.stdout.write(f"{len(tenders_to_update)} besoins rejetés")
