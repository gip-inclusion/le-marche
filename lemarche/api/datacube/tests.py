import freezegun
from django.test import TestCase, override_settings
from django.urls import reverse

from lemarche.companies.factories import CompanyFactory
from lemarche.tenders.factories import TenderFactory
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class DatacubeApiTest(TestCase):
    maxDiff = None

    @override_settings(DATACUBE_API_TOKEN="bar")
    def test_list_tenders_authentication(self):
        url = reverse("api:datacube-tenders")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # an appropriate token from the settings is required
        response = self.client.get(url, headers={"Authorization": "Token "})
        self.assertEqual(response.status_code, 401)

        response = self.client.get(url, headers={"Authorization": "Token foo"})
        self.assertEqual(response.status_code, 401)

        response = self.client.get(url, headers={"Authorization": "Token bar"})
        self.assertEqual(response.status_code, 200)

        # or alternatively, if you're logged in as superuser
        admin = UserFactory(kind="ADMIN")
        self.client.force_login(admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        admin.is_superuser = True
        admin.save(update_fields=["is_superuser"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @freezegun.freeze_time("2024-06-21 12:23:34")
    @override_settings(DATACUBE_API_TOKEN="bar")
    def test_list_tenders_content(self):
        url = reverse("api:datacube-tenders")
        response = self.client.get(url, headers={"Authorization": "Token bar"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 0, "next": None, "previous": None, "results": []})

        user = UserFactory(kind=User.KIND_BUYER, email="lagarde@example.com")
        CompanyFactory(name="Lagarde et Fils", users=[user])
        TenderFactory(title="Sébastien Le Lopez", amount="0-42K", author=user, presta_type=["FANFAN", "LA", "TULIPE"])

        # no associated company
        TenderFactory(title="Marc Henry", amount_exact=697, author__email="henry@example.com")

        response = self.client.get(url, headers={"Authorization": "Token bar"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "amount": "0-42K",
                        "amount_exact": None,
                        "author_email": "lagarde@example.com",
                        "company_name": "Lagarde et Fils",
                        "company_slug": "lagarde-et-fils",
                        "created_at": "2024-06-21T14:23:34+02:00",
                        "kind": "QUOTE",
                        "presta_type": ["FANFAN", "LA", "TULIPE"],
                        "slug": "sebastien-le-lopez",
                        "source": "FORM",
                        "status": "SENT",
                        "title": "Sébastien Le Lopez",
                        "updated_at": "2024-06-21T14:23:34+02:00",
                    },
                    {
                        "amount": None,
                        "amount_exact": 697,
                        "author_email": "henry@example.com",
                        "created_at": "2024-06-21T14:23:34+02:00",
                        "kind": "QUOTE",
                        "presta_type": [],
                        "slug": "marc-henry",
                        "source": "FORM",
                        "status": "SENT",
                        "title": "Marc Henry",
                        "updated_at": "2024-06-21T14:23:34+02:00",
                    },
                ],
            },
        )
