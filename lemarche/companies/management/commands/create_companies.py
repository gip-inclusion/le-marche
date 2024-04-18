import operator
from functools import reduce

from django.db.models import Q

from lemarche.companies.models import Company
from lemarche.users.models import User

# from lemarche.utils.apis import api_slack
from lemarche.utils.commands import BaseCommand
from lemarche.utils.emails import GENERIC_EMAIL_DOMAIN_SUFFIX_LIST


class Command(BaseCommand):
    """
    Usage:
    - poetry run python manage.py create_companies

    Common rules:
    "ville", "commune" --> Commune (138)
    "agglo" --> Communauté d'agglomération (121)
    "metropole" --> Métropole (123)
    "@cc" --> Communauté de communes (131)
    "départe" --> Département (31)
    "région" --> Région (111)
    "hospital" --> CHU (36)
    "pnr", "parc" --> Parc naturel régional (195)
    "@ac-" --> Académie (177)
    "@univ-" --> Université (139)
    ...
    """

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)

        user_buyer_without_company = User.objects.filter(kind="BUYER", company_id__isnull=True)
        self.stdout_info(f"Users without company: {user_buyer_without_company.count()}")
        user_buyer_without_company_with_tender = user_buyer_without_company.filter(tenders__isnull=False)
        self.stdout_info(f"Users without company with tender: {user_buyer_without_company_with_tender.count()}")

        user_qs = (
            user_buyer_without_company.filter(
                reduce(operator.and_, (~Q(email__endswith=x) for x in GENERIC_EMAIL_DOMAIN_SUFFIX_LIST))
            )
            .exclude(company_name__icontains="particulier")
            .exclude(company_name="")
        )
        self.stdout_info(f"Users final queryset (extra filtering): {user_qs.count()}")
        companies_created = 0

        for user in user_qs:
            user_email_suffix = user.email.split("@")[1]
            # check that no company already exist
            company_qs = Company.objects.filter(email_domain_list__contains=[user_email_suffix])
            if not company_qs.count():
                result = input(f"Create company: {user_email_suffix} / {user.company_name} ? (y/n/id) ")
                if result == "n":
                    pass
                elif result == "y":
                    company = Company.objects.create(name=user.company_name, email_domain_list=[user_email_suffix])
                    company.users.add(user)
                    self.stdout_info(f"Company created for {user_email_suffix}")
                    companies_created += 1
                elif result.isdigit():
                    company = Company.objects.get(id=int(result))
                    company.email_domain_list += [user_email_suffix]
                    company.save()
                    company.users.add(user)
                    self.stdout_info(f"User added to existing company {company.name} (and email_domain_list updated)")

            elif company_qs.count() == 1:
                company = company_qs.first()
                company.users.add(user)
                self.stdout_info(f"User added to existing company {company.name}")

        msg_success = [
            "----- Create companies -----",
            f"Done! Processed {user_qs.count()} users without company",
            f"Created {companies_created} companies",
        ]
        self.stdout_messages_success(msg_success)
        # api_slack.send_message_to_channel("\n".join(msg_success))
