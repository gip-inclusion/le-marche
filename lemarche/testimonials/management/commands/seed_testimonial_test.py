"""
Crée des témoignages de test dans différents statuts pour tester
le dashboard et la fiche commerciale sans dépendre des emails Brevo.

Usage:
    python manage.py seed_testimonial_test --siret 12345678901234
    python manage.py seed_testimonial_test --slug ma-structure
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from lemarche.siaes.models import Siae
from lemarche.testimonials import constants as testimonial_constants
from lemarche.testimonials.models import SiaeTestimonial
from lemarche.utils.commands import BaseCommand
from lemarche.utils.urls import get_domain_url


class Command(BaseCommand):
    help = "Crée des témoignages de test pour le dashboard et la fiche commerciale"

    def add_arguments(self, parser):
        parser.add_argument("--siret", type=str, default=None, help="SIRET de la structure cible")
        parser.add_argument("--slug", type=str, default=None, help="Slug de la structure cible")

    def handle(self, *args, **options):
        if options["siret"]:
            siae = Siae.objects.filter(siret=options["siret"]).first()
        elif options["slug"]:
            siae = Siae.objects.filter(slug=options["slug"]).first()
        else:
            siae = Siae.objects.is_live().first()

        if not siae:
            self.stdout_info("Aucune structure trouvée. Vérifiez le SIRET ou le slug.")
            return

        self.stdout_messages_info([f"Structure cible : {siae.name} ({siae.siret})"])

        now = timezone.now()

        testimonial_submitted, _ = SiaeTestimonial.objects.update_or_create(
            siae=siae,
            client_email="client.test.soumis@example.com",
            defaults={
                "content": (
                    "Collaboration excellente. Équipe réactive et professionnelle, résultats au rendez-vous."
                    " Je recommande sans hésitation à tout acheteur souhaitant allier performance et impact social."
                ),
                "author_first_name": "Marie",
                "author_last_name": "Dupont",
                "author_organization": "Acheteur SA",
                "status": testimonial_constants.STATUS_SUBMITTED,
                "sent_at": now - timedelta(days=5),
                "token_expires_at": now + timedelta(days=25),
                "submitted_at": now - timedelta(days=1),
            },
        )

        testimonial_published, _ = SiaeTestimonial.objects.update_or_create(
            siae=siae,
            client_email="client.test.publie@example.com",
            defaults={
                "content": (
                    "Très bon partenariat sur notre marché d'entretien des espaces verts."
                    " La qualité est constante et le suivi commercial sérieux. Nous renouvelons le contrat."
                ),
                "author_first_name": "Jean",
                "author_last_name": "Martin",
                "author_organization": "Mairie de Lyon",
                "status": testimonial_constants.STATUS_PUBLISHED,
                "sent_at": now - timedelta(days=30),
                "token_expires_at": now + timedelta(days=0),
                "submitted_at": now - timedelta(days=20),
                "published_at": now - timedelta(days=10),
            },
        )

        testimonial_sent, _ = SiaeTestimonial.objects.update_or_create(
            siae=siae,
            client_email="client.test.invite@example.com",
            defaults={
                "content": "",
                "status": testimonial_constants.STATUS_SENT,
                "sent_at": now,
                "token_expires_at": now + timedelta(days=testimonial_constants.TOKEN_EXPIRY_DAYS),
            },
        )

        domain = get_domain_url()
        submit_url = f"https://{domain}{reverse('testimonials:submit', kwargs={'token': testimonial_sent.token})}"

        self.stdout_messages_success(
            [
                "Témoignages de test créés :",
                f"  [SOUMIS]  client.test.soumis@example.com  → pk={testimonial_submitted.pk}",
                f"  [PUBLIÉ]  client.test.publie@example.com  → pk={testimonial_published.pk}",
                f"  [INVITÉ]  client.test.invite@example.com  → pk={testimonial_sent.pk}",
                "",
                "Lien direct vers le formulaire client (sans email) :",
                f"  {submit_url}",
                "",
                "Dashboard témoignages :",
                f"  https://{domain}/profil/prestataires/{siae.slug}/temoignages/",
            ]
        )
