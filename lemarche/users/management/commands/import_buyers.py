from lemarche.companies.models import Company
from lemarche.users.management.commands.base_import_users import BaseImportUsersCommand
from lemarche.users.models import User
from lemarche.utils.emails import add_to_contact_list


class Command(BaseImportUsersCommand):
    """Import new buyers from a csv file.
    The file should respect these headers:
        FIRST_NAME | LAST_NAME | EMAIL | PHONE | POSITION
    """

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "company_slug",
            type=str,
            help="Slug de la société à qui appartient les acheteurs importés.",
        )
        parser.add_argument(
            "brevo_contact_id",
            type=int,
            help="ID de la liste de contact Brevo à utiliser pour les acheteurs importés.",
        )

    def handle(self, *args, **options):
        # Get company before processing
        self.company = Company.objects.get(slug=options["company_slug"])
        super().handle(*args, **options)

    def _get_extra_context(self, options: dict) -> dict:
        return {
            "company": self.company,
            "brevo_contact_id": options["brevo_contact_id"],
        }

    def _post_import_user(self, imported_user: dict, **kwargs) -> None:
        """Add email domain to company."""
        self._add_email_dns_to_company(email=imported_user["EMAIL"], company=self.company)

    def _post_import_user_actions(self, user: User, **kwargs) -> None:
        """Add user to Brevo contact list."""
        add_to_contact_list(user, contact_type=kwargs["brevo_contact_id"])

    def get_user_kind(self) -> str:
        return User.KIND_BUYER

    def get_user_fields(self, imported_user: dict, **kwargs) -> dict:
        user_fields = super().get_user_fields(imported_user, **kwargs)
        user_fields.update(
            {
                "company": self.company,
                "company_name": self.company.name,
            }
        )
        return user_fields

    def get_update_fields(self) -> dict:
        return {
            "company": self.company,
            "company_name": self.company.name,
        }

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
