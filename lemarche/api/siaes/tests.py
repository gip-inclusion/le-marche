from django.test import TestCase
from django.urls import reverse

from lemarche.networks.factories import NetworkFactory
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeFactory
from lemarche.users.factories import UserFactory


class SiaeListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        for _ in range(12):
            SiaeFactory()
        UserFactory(api_key="admin")

    def test_should_return_siae_sublist_to_anonmyous_users(self):
        url = reverse("api:siae-list")  # anonymous user
        response = self.client.get(url)
        # self.assertEqual(response.data["count"], 12)
        # self.assertEqual(len(response.data["results"]), 10)  # results aren't paginated
        self.assertEqual(len(response.data), 10)
        self.assertTrue("id" in response.data[0])
        self.assertTrue("name" in response.data[0])
        self.assertTrue("siret" in response.data[0])
        self.assertTrue("kind" in response.data[0])
        self.assertTrue("presta_type" in response.data[0])
        self.assertTrue("department" in response.data[0])
        self.assertTrue("created_at" in response.data[0])

    def test_should_return_detailed_siae_list_with_pagination_to_authenticated_users(self):
        url = reverse("api:siae-list") + "?token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(len(response.data["results"]), 12)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])
        self.assertTrue("siret" in response.data["results"][0])
        self.assertTrue("kind" in response.data["results"][0])
        self.assertTrue("presta_type" in response.data["results"][0])
        self.assertTrue("department" in response.data["results"][0])
        self.assertTrue("created_at" in response.data["results"][0])

    def test_should_return_401_if_token_unknown(self):
        url = reverse("api:siae-list") + "?token=wrong"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)


class SiaeListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # default_siae = {"kind": siae_constants.KIND_EI, "presta_type": [siae_constants.PRESTA_DISP], "department": "01"}  # noqa
        SiaeFactory(
            kind=siae_constants.KIND_EI, presta_type=[siae_constants.PRESTA_DISP], department="01", is_active=False
        )
        SiaeFactory(
            kind=siae_constants.KIND_ETTI, presta_type=[siae_constants.PRESTA_DISP], department="01"
        )  # siae_with_kind
        SiaeFactory(
            kind=siae_constants.KIND_ACI, presta_type=[siae_constants.PRESTA_BUILD], department="01"
        )  # siae_with_presta_type
        SiaeFactory(
            kind=siae_constants.KIND_EI, presta_type=[siae_constants.PRESTA_PREST], department="38"
        )  # siae_with_department
        cls.sector_1 = SectorFactory()
        cls.sector_2 = SectorFactory()
        siae_with_sector_1 = SiaeFactory(
            kind=siae_constants.KIND_EI, presta_type=[siae_constants.PRESTA_DISP], department="01"
        )
        siae_with_sector_1.sectors.add(cls.sector_1)
        siae_with_sector_2 = SiaeFactory(
            kind=siae_constants.KIND_EI, presta_type=[siae_constants.PRESTA_DISP], department="01"
        )
        siae_with_sector_2.sectors.add(cls.sector_2)
        cls.network_1 = NetworkFactory()
        cls.network_2 = NetworkFactory()
        siae_with_network_1 = SiaeFactory(
            kind=siae_constants.KIND_EI, presta_type=[siae_constants.PRESTA_DISP], department="01"
        )
        siae_with_network_1.networks.add(cls.network_1)
        siae_with_network_2 = SiaeFactory(
            kind=siae_constants.KIND_EI, presta_type=[siae_constants.PRESTA_DISP], department="01"
        )
        siae_with_network_2.networks.add(cls.network_2)
        UserFactory(api_key="admin")

    def test_should_return_siae_list(self):
        url = reverse("api:siae-list") + "?token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 4 + 2 + 2)
        self.assertEqual(len(response.data["results"]), 4 + 2 + 2)

    def test_should_not_filter_siae_list_for_anonmyous_user(self):
        # single
        url = reverse("api:siae-list") + f"?kind={siae_constants.KIND_ETTI}"  # anonymous user
        response = self.client.get(url)
        # self.assertEqual(response.data["count"], 1)
        # self.assertEqual(len(response.data["results"]), 4 + 2 + 2)  # results aren't paginated
        self.assertEqual(len(response.data), 4 + 2 + 2)

    def test_should_filter_siae_list_by_is_active(self):
        url = reverse("api:siae-list") + "?is_active=false&token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        url = reverse("api:siae-list") + "?is_active=true&token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3 + 2 + 2)
        self.assertEqual(len(response.data["results"]), 3 + 2 + 2)

    def test_should_filter_siae_list_by_kind(self):
        # single
        url = reverse("api:siae-list") + f"?kind={siae_constants.KIND_ETTI}&token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = reverse("api:siae-list") + f"?kind={siae_constants.KIND_ETTI}&kind={siae_constants.KIND_ACI}&token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1 + 1)
        self.assertEqual(len(response.data["results"]), 1 + 1)

    def test_should_filter_siae_list_by_presta_type(self):
        # single
        url = reverse("api:siae-list") + f"?presta_type={siae_constants.PRESTA_BUILD}&token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = (
            reverse("api:siae-list")
            + f"?presta_type={siae_constants.PRESTA_BUILD}&presta_type={siae_constants.PRESTA_PREST}&token=admin"
        )
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1 + 1)
        self.assertEqual(len(response.data["results"]), 1 + 1)

    def test_should_filter_siae_list_by_department(self):
        url = reverse("api:siae-list") + "?department=38&token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_should_filter_siae_list_by_sector(self):
        # single
        url = reverse("api:siae-list") + f"?sectors={self.sector_1.slug}&token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = reverse("api:siae-list") + f"?sectors={self.sector_1.slug}&sectors={self.sector_2.slug}&token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1 + 1)
        self.assertEqual(len(response.data["results"]), 1 + 1)

    def test_should_filter_siae_list_by_network(self):
        # single
        url = reverse("api:siae-list") + f"?networks={self.network_1.slug}&token=admin"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = reverse("api:siae-list") + f"?networks={self.network_1.slug}&networks={self.network_2.slug}&token=admin"
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
        self.assertTrue("id" in response.data)
        self.assertTrue("name" in response.data)
        self.assertTrue("siret" in response.data)
        self.assertTrue("slug" in response.data)
        self.assertTrue("kind" in response.data)
        self.assertTrue("presta_type" in response.data)
        self.assertTrue("sectors" not in response.data)
        self.assertTrue("networks" not in response.data)
        self.assertTrue("offers" not in response.data)
        self.assertTrue("client_references" not in response.data)
        self.assertTrue("labels" not in response.data)

    def test_should_return_detailed_siae_object_to_authenticated_users(self):
        url = reverse("api:siae-detail", args=[self.siae.id]) + "?token=admin"
        response = self.client.get(url)
        self.assertTrue("id" in response.data)
        self.assertTrue("name" in response.data)
        self.assertTrue("siret" in response.data)
        self.assertTrue("slug" in response.data)
        self.assertTrue("kind" in response.data)
        self.assertTrue("presta_type" in response.data)
        self.assertTrue("sectors" in response.data)
        self.assertTrue("networks" in response.data)
        self.assertTrue("offers" in response.data)
        self.assertTrue("client_references" in response.data)
        self.assertTrue("labels_old" in response.data)


class SiaeRetrieveBySlugApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(name="Une structure", siret="12312312312345", department="38")
        UserFactory(api_key="admin")

    def test_should_return_404_if_slug_unknown(self):
        url = reverse("api:siae-retrieve-by-slug", args=["test-123"])  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_should_return_siae_if_slug_known(self):
        url = reverse("api:siae-retrieve-by-slug", args=["une-structure-38"])  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), dict)
        self.assertEqual(response.data["siret"], "12312312312345")
        self.assertEqual(response.data["slug"], "une-structure-38")
        self.assertTrue("sectors" not in response.data)

    def test_should_return_detailed_siae_object_to_authenticated_user(self):
        url = reverse("api:siae-retrieve-by-slug", args=["une-structure-38"]) + "?token=admin"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["siret"], "12312312312345")
        self.assertEqual(response.data["slug"], "une-structure-38")
        self.assertTrue("sectors" in response.data)


class SiaeRetrieveBySiretApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(name="Une structure", siret="12312312312345", department="38")
        SiaeFactory(name="Une autre structure", siret="22222222222222", department="69")
        SiaeFactory(name="Une autre structure avec le meme siret", siret="22222222222222", department="69")
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
        self.assertEqual(response.data["slug"], "une-structure-38")
        self.assertTrue("sectors" not in response.data)

    def test_should_return_detailed_siae_object_to_authenticated_user(self):
        url = reverse("api:siae-retrieve-by-siret", args=["12312312312345"]) + "?token=admin"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["siret"], "12312312312345")
        self.assertEqual(response.data["slug"], "une-structure-38")
        self.assertTrue("sectors" in response.data)

    def test_should_return_siae_list_if_siret_known_and_duplicate(self):
        url = reverse("api:siae-retrieve-by-siret", args=["22222222222222"])  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(response.data[0]["siret"], "22222222222222")
        self.assertEqual(response.data[1]["siret"], "22222222222222")
        self.assertTrue("sectors" not in response.data[0])

    def test_should_return_siae_detailed_list_if_siret_known_and_duplicate(self):
        url = reverse("api:siae-retrieve-by-siret", args=["22222222222222"]) + "?token=admin"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(response.data[0]["siret"], "22222222222222")
        self.assertEqual(response.data[1]["siret"], "22222222222222")
        self.assertTrue("sectors" in response.data[0])


class SiaeChoicesApiTest(TestCase):
    def test_should_return_siae_kinds_list(self):
        url = reverse("api:siae-kinds-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 10)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])

    def test_should_return_siae_presta_types_list(self):
        url = reverse("api:siae-presta-types-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])
