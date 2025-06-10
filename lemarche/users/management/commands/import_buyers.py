import csv

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from lemarche.companies.models import Company
from lemarche.users.models import User
from lemarche.utils.emails import add_to_contact_list
from lemarche.www.auth.tasks import send_new_user_password_reset_link


class Command(BaseCommand):
    """Import new buyers from a csv file.
    The file should respect these headers:
        FIRST_NAME | LAST_NAME | EMAIL | PHONE | POSITION
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "filename",
            type=str,
            help="Fichier csv contenant les acheteurs à importer.",
        )
        parser.add_argument(
            "company_slug",
            type=str,
            help="Slug de la société à qui appartient les acheteurs importés.",
        )
        parser.add_argument(
            "template_code",
            type=str,
            help="Code de la template de mail Brevo enregistrée"
            " dans la base pour envoyer l'invitation aux acheteurs importés.",
        )
        parser.add_argument(
            "brevo_contact_id",
            type=int,
            help="ID de la liste de contact Brevo à utiliser pour les acheteurs importés.",
        )

    def handle(self, *args, **options):
        company = Company.objects.get(slug=options["company_slug"])

        with open(options["filename"], "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            imported_list = list(reader)

        for imported_user in imported_list:
            try:
                with transaction.atomic():
                    self._import_user(
                        imported_user,
                        company,
                        template_code=options["template_code"],
                        brevo_contact_id=options["brevo_contact_id"],
                    )
                    self._add_email_dns_to_company(email=imported_user["EMAIL"], company=company)
            except Exception as e:
                self.stdout.write(f"Erreur lors de l'import de l'acheteur {imported_user['EMAIL']}: {e}")

    def _import_user(self, imported_user: dict, company: Company, template_code: str, brevo_contact_id: int) -> None:
        """
        Create a new user and send a password reset link to it.
        If the user already exists, update its company.
        Always add to Brevo contact list.
        """
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=imported_user["EMAIL"],
                    first_name=imported_user["FIRST_NAME"],
                    last_name=imported_user["LAST_NAME"],
                    phone=imported_user["PHONE"],
                    kind=User.KIND_BUYER,
                    company=company,
                    company_name=company.name,
                    position=imported_user["POSITION"],
                    accept_rgpd=True,
                    accept_survey=True,
                    password=None,
                )
        except IntegrityError:  # email already exists
            # Already registered users have their company updated
            user = User.objects.get(email=imported_user["EMAIL"])
            user.company = company
            user.company_name = company.name
            user.save(update_fields=["company", "company_name"])
            self.stdout.write(f"L'acheteur {imported_user['EMAIL']} est déjà inscrit, entreprise mise à jour.")
        else:  # new user, send password reset link
            send_new_user_password_reset_link(user, template_code=template_code)
            self.stdout.write(f"L'acheteur {imported_user['EMAIL']} a été inscrit avec succès.")
        finally:  # add to Brevo contact list, even if user already exists or not
            add_to_contact_list(user, contact_type=brevo_contact_id)

    def _add_email_dns_to_company(self, email: str, company: Company) -> None:
        """If the email domain is not already in the company's email_domain_list, add it."""
        email_dns = email.split("@")[1]
        if email_dns not in company.email_domain_list:
            company.email_domain_list.append(email_dns)
            company.save(update_fields=["email_domain_list"])
            self.stdout.write(
                f"Le nom de domaine email {email_dns}"
                f" a été ajoutée à la liste des domaines de l'entreprise {company.name}."
            )
