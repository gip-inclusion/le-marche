from lemarche.companies.models import Company
from lemarche.users.models import User
from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Command to attach users to their company, depending on their e-mail address
    Only for companies that have their 'email_domain_list' field set

    Usage:
    - poetry run python manage.py set_company_users --dry-run
    - poetry run python manage.py set_company_users --only-add
    - poetry run python manage.py set_company_users
    """

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run (no changes to the DB)")
        parser.add_argument(
            "--only-add", dest="only_add", action="store_true", help="Only add new users, don't delete existing"
        )

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Populating users field...")

        users = User.objects.all()
        companies = Company.objects.all()
        companies_with_email_domain_list = companies.has_email_domain()

        # Old stats (before changes)
        old_users_with_company_count = users.has_company().count()
        old_companies_with_user_count = companies.has_user().count()
        self.stdout_info("-" * 80)
        self.stdout_info(f"User count: {users.count()}")
        self.stdout_info(f"Users with company count: {old_users_with_company_count}")
        self.stdout_info(f"Company count: {companies.count()}")
        self.stdout_info(f"Companies with email_domain_list field count: {companies_with_email_domain_list.count()}")
        self.stdout_info(f"Companies with user count: {old_companies_with_user_count}")

        self.stdout_info("-" * 80)
        self.stdout_info("Mapping users to their company, depending on User.email and Company.email_domain_list...")
        progress = 0

        for company in companies_with_email_domain_list:
            company_email_domain_list_users = list()
            for company_email_domain in company.email_domain_list:
                company_email_domain_users = User.objects.filter(email__iendswith=f"@{company_email_domain}")
                company_email_domain_list_users += company_email_domain_users
            if not options["dry_run"]:
                if options["only_add"]:
                    company.users.add(*company_email_domain_list_users)
                else:
                    company.users.set(company_email_domain_list_users)
            progress += 1
            if (progress % 50) == 0:
                self.stdout_info(f"{progress}...")

        # New stats (after changes)
        new_users_with_company_count = users.has_company().count()
        new_companies_with_user_count = companies.has_user().count()

        msg_success = [
            "----- Company users -----",
            f"Done! Processed {companies_with_email_domain_list.count()} companies with email_domain_list",
            f"Users with company: before {old_users_with_company_count} / after {new_users_with_company_count} / {new_users_with_company_count-old_users_with_company_count}",  # noqa
            f"Companies with user: before {old_companies_with_user_count} / after {new_companies_with_user_count} / {new_companies_with_user_count-old_companies_with_user_count}",  # noqa
        ]

        self.stdout_messages_success(msg_success)
        api_slack.send_message_to_channel("\n".join(msg_success))
