from django.test import TestCase
from django.urls import reverse

from lemarche.sectors.factories import SectorFactory
from lemarche.siaes.factories import SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.users.factories import UserFactory


class SiaeListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory()
        SiaeFactory()
        UserFactory(api_key="admin")

    def test_should_return_simple_siae_list_to_anonmyous_users(self):
        url = reverse("api:siae-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertTrue("raisonSociale" in response.data["results"][0])
        self.assertTrue("siret" in response.data["results"][0])
        self.assertTrue("type" not in response.data["results"][0])
        self.assertTrue("presta_type" not in response.data["results"][0])
        self.assertTrue("departement" not in response.data["results"][0])
        self.assertTrue("created_at" not in response.data["results"][0])

    def test_should_return_detailed_siae_list_to_authenticated_users(self):
        url = reverse("api:siae-list") + "?token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertTrue("raisonSociale" in response.data["results"][0])
        self.assertTrue("siret" in response.data["results"][0])
        self.assertTrue("type" in response.data["results"][0])
        self.assertTrue("presta_type" in response.data["results"][0])
        self.assertTrue("departement" in response.data["results"][0])
        self.assertTrue("created_at" in response.data["results"][0])


class SiaeListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # default_siae = {"kind": Siae.KIND_EI, "presta_type": [Siae.PRESTA_DISP], "department": "01"}
        SiaeFactory(kind=Siae.KIND_EI, presta_type=[Siae.PRESTA_DISP], department="01")
        SiaeFactory(kind=Siae.KIND_ETTI, presta_type=[Siae.PRESTA_DISP], department="01")  # siae_with_kind
        SiaeFactory(kind=Siae.KIND_ACI, presta_type=[Siae.PRESTA_BUILD], department="01")  # siae_with_presta_type
        SiaeFactory(kind=Siae.KIND_EI, presta_type=[Siae.PRESTA_PREST], department="38")  # siae_with_department
        siae_with_sector_1 = SiaeFactory(kind=Siae.KIND_EI, presta_type=[Siae.PRESTA_DISP], department="01")
        cls.sector_1 = SectorFactory()
        siae_with_sector_1.sectors.add(cls.sector_1)
        siae_with_sector_2 = SiaeFactory(kind=Siae.KIND_EI, presta_type=[Siae.PRESTA_DISP], department="01")
        cls.sector_2 = SectorFactory()
        siae_with_sector_2.sectors.add(cls.sector_2)
        UserFactory(api_key="admin")

    def test_should_return_siae_list(self):
        url = reverse("api:siae-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 6)
        self.assertEqual(len(response.data["results"]), 6)

    def test_should_filter_siae_list_by_kind(self):
        # single
        url = reverse("api:siae-list") + f"?kind={Siae.KIND_ETTI}"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = reverse("api:siae-list") + f"?kind={Siae.KIND_ETTI}&kind={Siae.KIND_ACI}"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1 + 1)
        self.assertEqual(len(response.data["results"]), 1 + 1)

    def test_should_filter_siae_list_by_presta_type(self):
        # single
        url = reverse("api:siae-list") + f"?presta_type={Siae.PRESTA_BUILD}"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = (
            reverse("api:siae-list") + f"?presta_type={Siae.PRESTA_BUILD}&presta_type={Siae.PRESTA_PREST}"
        )  # anonymous user  # noqa
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1 + 1)
        self.assertEqual(len(response.data["results"]), 1 + 1)

    def test_should_filter_siae_list_by_department(self):
        url = reverse("api:siae-list") + "?department=38"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_should_filter_siae_list_by_sector(self):
        # single
        url = reverse("api:siae-list") + f"?sectors={self.sector_1.slug}"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = (
            reverse("api:siae-list") + f"?sectors={self.sector_1.slug}&sectors={self.sector_2.slug}"
        )  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1 + 1)
        self.assertEqual(len(response.data["results"]), 1 + 1)


class SiaeDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory()
        UserFactory(api_key="admin")

    def test_should_return_simple_siae_object_to_anonmyous_users(self):
        url = reverse("api:siae-detail", args=[self.siae.id])  # anonymous user
        response = self.client.get(url)
        self.assertTrue("raisonSociale" in response.data)
        self.assertTrue("siret" in response.data)
        self.assertTrue("slug" not in response.data)
        self.assertTrue("type" not in response.data)
        self.assertTrue("presta_type" not in response.data)

    def test_should_return_detailed_siae_object_to_authenticated_users(self):
        url = reverse("api:siae-detail", args=[self.siae.id]) + "?token=admin"
        response = self.client.get(url)
        self.assertTrue("raisonSociale" in response.data)
        self.assertTrue("siret" in response.data)
        self.assertTrue("slug" in response.data)
        self.assertTrue("type" in response.data)
        self.assertTrue("presta_type" in response.data)


class SiaeRetrieveBySiretApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(name="Une structure", siret="12312312312345", department="38")
        UserFactory(api_key="admin")

    def test_should_return_404_if_siret_unknown(self):
        url = reverse("api:siae-retrieve-by-siret", args=["123"])  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_should_return_404_if_siret_known_but_with_spaces(self):
        url = reverse("api:siae-retrieve-by-siret", args=["123 123 123 12345"])  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_should_return_siae_if_siret_known(self):
        url = reverse("api:siae-retrieve-by-siret", args=["12312312312345"])  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), dict)
        self.assertEqual(response.data["siret"], "12312312312345")
        self.assertTrue("slug" not in response.data)

    def test_should_return_detailed_siae_object_to_authenticated_user(self):
        url = reverse("api:siae-retrieve-by-siret", args=["12312312312345"]) + "?token=admin"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["siret"], "12312312312345")
        self.assertEqual(response.data["slug"], "une-structure-38")


class SiaeChoicesApiTest(TestCase):
    def test_should_return_siae_kinds_list(self):
        url = reverse("api:siae-kinds-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 8)
        self.assertEqual(len(response.data["results"]), 8)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])

    def test_should_return_siae_presta_types_list(self):
        url = reverse("api:siae-presta-types-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])
