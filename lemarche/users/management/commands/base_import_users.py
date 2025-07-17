import csv

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction

from lemarche.users.models import User
from lemarche.www.auth.tasks import send_new_user_password_reset_link


class BaseImportUsersCommand(BaseCommand):
    """Base class for importing users from CSV files.

    Subclasses must implement:
    - get_user_kind(): return the user kind (e.g., User.KIND_BUYER)
    - get_user_fields(): return dict of additional fields to set on user creation
    - get_update_fields(): return list of fields to update for existing users
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "filename",
            type=str,
            help="Fichier csv contenant les utilisateurs à importer.",
        )
        parser.add_argument(
            "template_code",
            type=str,
            help="Code de la template de mail Brevo enregistrée"
            " dans la base pour envoyer l'invitation aux utilisateurs importés.",
        )
        # Subclasses can add more arguments by calling super().add_arguments(parser)

    def handle(self, *args, **options):
        # Subclasses can override this to add setup logic (e.g., get company)
        with open(options["filename"], "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            imported_list = list(reader)

        for imported_user in imported_list:
            try:
                with transaction.atomic():
                    self._import_user(
                        imported_user, template_code=options["template_code"], **self._get_extra_context(options)
                    )
                    self._post_import_user(imported_user, **self._get_extra_context(options))
            except Exception as e:
                self.stdout.write(f"Erreur lors de l'import de l'utilisateur {imported_user['EMAIL']}: {e}")

    def _import_user(self, imported_user: dict, template_code: str, **kwargs) -> None:
        """
        Create a new user and send a password reset link to it.
        If the user already exists, update its fields.
        """
        user_fields = self._get_base_user_fields(imported_user)
        user_fields.update(self.get_user_fields(**kwargs))

        try:
            with transaction.atomic():
                user = User.objects.create_user(**user_fields)
        except IntegrityError:  # email already exists
            update_fields = self.get_update_fields(**kwargs)
            if update_fields:
                user = User.objects.get(email=imported_user["EMAIL"])
                for field, value in update_fields.items():
                    setattr(user, field, value)
                user.save(update_fields=list(update_fields.keys()))
                self.stdout.write(
                    f"L'utilisateur {imported_user['EMAIL']} est déjà inscrit, informations mises à jour."
                )
            else:
                self.stdout.write(f"L'utilisateur {imported_user['EMAIL']} est déjà inscrit, aucune mise à jour.")
        else:  # new user, send password reset link
            send_new_user_password_reset_link(user, template_code=template_code)
            self.stdout.write(f"L'utilisateur {imported_user['EMAIL']} a été inscrit avec succès.")

        # Post-import actions (e.g., add to Brevo list)
        self._post_import_user_actions(user, **kwargs)

    def _get_base_user_fields(self, imported_user: dict) -> dict:
        """Get the common fields for all user types."""
        return {
            "email": imported_user["EMAIL"],
            "first_name": imported_user["FIRST_NAME"],
            "last_name": imported_user["LAST_NAME"],
            "phone": imported_user["PHONE"],
            "kind": self.get_user_kind(),
            "position": imported_user["POSITION"],
            "accept_rgpd": True,
            "accept_survey": True,
            "password": None,
        }

    def _get_extra_context(self, options: dict) -> dict:
        """Get extra context from options for subclasses."""
        return {}

    def _post_import_user(self, imported_user: dict, **kwargs) -> None:
        """Hook for post-import actions that don't require the user object."""
        pass

    def _post_import_user_actions(self, user: User, **kwargs) -> None:
        """Hook for post-import actions that require the user object."""
        pass

    def get_user_kind(self) -> str:
        """Return the user kind (e.g., User.KIND_BUYER)."""
        raise NotImplementedError

    def get_user_fields(self, **kwargs) -> dict:
        """Return additional fields to set on user creation."""
        raise NotImplementedError

    def get_update_fields(self, **kwargs) -> dict:
        """Return fields to update for existing users."""
        raise NotImplementedError
