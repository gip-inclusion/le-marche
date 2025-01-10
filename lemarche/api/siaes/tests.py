from django.test import TestCase
from django.urls import reverse

from lemarche.api.utils import generate_random_string
from lemarche.networks.factories import NetworkFactory
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeActivityFactory, SiaeFactory
from lemarche.siaes.models import Siae
from lemarche.users.factories import UserFactory


class SiaeListApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        for _ in range(12):
            SiaeFactory()
        cls.user_token = generate_random_string()
        UserFactory(api_key=cls.user_token)

    def test_should_return_siae_sublist_to_anonymous_users(self):
        url = reverse("api:siae-list")  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_should_return_detailed_siae_list_with_pagination_to_authenticated_users(self):
        url = reverse("api:siae-list")
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(len(response.data["results"]), 12)
        self.assertTrue("id" in response.data["results"][0])
        self.assertTrue("name" in response.data["results"][0])
        self.assertTrue("siret" in response.data["results"][0])
        self.assertTrue("kind" in response.data["results"][0])
        self.assertTrue("kind_parent" in response.data["results"][0])
        self.assertTrue("department" in response.data["results"][0])
        self.assertTrue("created_at" in response.data["results"][0])

    def test_should_return_401_if_token_unknown(self):
        url = reverse("api:siae-list")
        response = self.client.get(url, headers={"authorization": "wrong"})
        self.assertEqual(response.status_code, 401)


class SiaeListFilterApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(kind=siae_constants.KIND_EI, department="01", is_active=False)
        SiaeFactory(kind=siae_constants.KIND_ETTI, department="01")
        SiaeFactory(kind=siae_constants.KIND_ACI, department="01")
        SiaeFactory(kind=siae_constants.KIND_EI, department="38")
        SiaeFactory(kind="OPCS", department="38")
        cls.sector_1 = SectorFactory()
        cls.sector_2 = SectorFactory()
        siae_with_sector_1 = SiaeFactory(kind=siae_constants.KIND_EI, department="01")
        SiaeActivityFactory(siae=siae_with_sector_1, sectors=[cls.sector_1], presta_type=[siae_constants.PRESTA_BUILD])
        siae_with_sector_2 = SiaeFactory(kind=siae_constants.KIND_EI, department="01")
        SiaeActivityFactory(siae=siae_with_sector_2, sectors=[cls.sector_2], presta_type=[siae_constants.PRESTA_PREST])
        cls.network_1 = NetworkFactory(name="Reseau 1")
        cls.network_2 = NetworkFactory(name="Reseau 2")
        siae_with_network_1 = SiaeFactory(kind=siae_constants.KIND_EI, department="01")
        siae_with_network_1.networks.add(cls.network_1)
        siae_with_network_2 = SiaeFactory(kind=siae_constants.KIND_EI, department="01")
        siae_with_network_2.networks.add(cls.network_2)
        cls.user_token = generate_random_string()
        UserFactory(api_key=cls.user_token)

    def test_siae_count(self):
        self.assertEqual(Siae.objects.count(), 9)

    def test_should_return_siae_list(self):
        url = reverse("api:siae-list")
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 4 + 2 + 2)
        self.assertEqual(len(response.data["results"]), 4 + 2 + 2)

    def test_should_not_filter_siae_list_for_anonymous_user(self):
        # single
        url = reverse("api:siae-list") + f"?kind={siae_constants.KIND_ETTI}"  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_should_filter_siae_list_by_is_active(self):
        url = reverse("api:siae-list") + "?is_active=false"
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        url = reverse("api:siae-list") + "?is_active=true"
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 3 + 2 + 2)
        self.assertEqual(len(response.data["results"]), 3 + 2 + 2)

    def test_should_filter_siae_list_by_kind(self):
        # single
        url = reverse("api:siae-list") + f"?kind={siae_constants.KIND_ETTI}"
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = reverse("api:siae-list") + f"?kind={siae_constants.KIND_ETTI}&kind={siae_constants.KIND_ACI}"
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 1 + 1)
        self.assertEqual(len(response.data["results"]), 1 + 1)

    def test_should_filter_siae_list_by_presta_type(self):
        # single
        url = reverse("api:siae-list") + f"?presta_types={siae_constants.PRESTA_BUILD}"
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = (
            reverse("api:siae-list")
            + f"?presta_types={siae_constants.PRESTA_BUILD}&presta_types={siae_constants.PRESTA_PREST}"
        )
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 1 + 1)
        self.assertEqual(len(response.data["results"]), 1 + 1)

    def test_should_filter_siae_list_by_department(self):
        url = reverse("api:siae-list") + "?department=38"
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_should_filter_siae_list_by_sector(self):
        # single
        url = reverse("api:siae-list") + f"?sectors={self.sector_1.slug}"
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = reverse("api:siae-list") + f"?sectors={self.sector_1.slug}&sectors={self.sector_2.slug}"
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 1 + 1)
        self.assertEqual(len(response.data["results"]), 1 + 1)

    def test_should_filter_siae_list_by_network(self):
        # single
        url = reverse("api:siae-list") + f"?networks={self.network_1.slug}"
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        # multiple
        url = reverse("api:siae-list") + f"?networks={self.network_1.slug}&networks={self.network_2.slug}"
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.data["count"], 1 + 1)
        self.assertEqual(len(response.data["results"]), 1 + 1)


class SiaeDetailApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory()
        cls.user_token = generate_random_string()
        UserFactory(api_key=cls.user_token)

    def test_should_return_4O4_if_siae_excluded(self):
        siae_opcs = SiaeFactory(kind="OPCS")
        url = reverse("api:siae-detail", args=[siae_opcs.id])  # anonymous
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        url = reverse("api:siae-detail", args=[siae_opcs.id])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 404)

    def test_should_return_simple_siae_object_to_anonymous_users(self):
        url = reverse("api:siae-detail", args=[self.siae.id])  # anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_should_return_detailed_siae_object_to_authenticated_users(self):
        url = reverse("api:siae-detail", args=[self.siae.id])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertTrue("id" in response.data)
        self.assertTrue("name" in response.data)
        self.assertTrue("siret" in response.data)
        self.assertTrue("slug" in response.data)
        self.assertTrue("kind" in response.data)
        self.assertTrue("kind_parent" in response.data)
        self.assertTrue("sectors" in response.data)
        self.assertTrue("networks" in response.data)
        self.assertTrue("offers" in response.data)
        self.assertTrue("client_references" in response.data)
        self.assertTrue("labels_old" in response.data)


class SiaeRetrieveBySlugApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_token = generate_random_string()
        SiaeFactory(name="Une structure", siret="12312312312345", department="38")
        UserFactory(api_key=cls.user_token)

    def test_should_return_404_if_slug_unknown(self):
        url = reverse("api:siae-retrieve-by-slug", args=["test-123"])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 404)

    def test_should_return_4O4_if_siae_excluded(self):
        siae_opcs = SiaeFactory(kind="OPCS")
        url = reverse("api:siae-retrieve-by-slug", args=[siae_opcs.slug])  # anonymous
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        url = reverse("api:siae-retrieve-by-slug", args=[siae_opcs.slug])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 404)

    def test_should_return_detailed_siae_object_to_authenticated_user(self):
        url = reverse("api:siae-retrieve-by-slug", args=["une-structure-38"])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["siret"], "12312312312345")
        self.assertEqual(response.data["slug"], "une-structure-38")
        self.assertTrue("sectors" in response.data)


class SiaeRetrieveBySirenApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(name="Une structure", siret="12312312312345", department="38")
        SiaeFactory(name="Une autre structure", siret="22222222233333", department="69")
        SiaeFactory(name="Une autre structure avec le meme siret", siret="22222222233333", department="69")
        cls.user_token = generate_random_string()
        UserFactory(api_key=cls.user_token)

    def test_should_return_400_if_siren_malformed(self):
        # anonymous user
        for siren in ["123", "12312312312345"]:
            url = reverse("api:siae-retrieve-by-siren", args=[siren])
            response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
            self.assertEqual(response.status_code, 400)

    def test_should_return_empty_list_if_siren_unknown(self):
        # anonymous user
        url = reverse("api:siae-retrieve-by-siren", args=["444444444"])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(len(response.data), 0)

    def test_should_return_4O4_if_siae_excluded(self):
        siae_opcs = SiaeFactory(kind="OPCS", siret="99999999999999")
        url = reverse("api:siae-retrieve-by-siren", args=[siae_opcs.siren])  # anonymous
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        url = reverse("api:siae-retrieve-by-siren", args=[siae_opcs.siren])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(len(response.data), 0)

    def test_should_return_siae_list_if_siren_known(self):
        url = reverse("api:siae-retrieve-by-siren", args=["123123123"])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["siret"], "12312312312345")
        self.assertEqual(response.data[0]["slug"], "une-structure-38")
        self.assertTrue("sectors" not in response.data)
        url = reverse("api:siae-retrieve-by-siren", args=["222222222"])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["siret"], "22222222233333")
        self.assertEqual(response.data[1]["siret"], "22222222233333")
        # authenticated user
        url = reverse("api:siae-retrieve-by-siren", args=["123123123"]) + "?token=" + self.user_token
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["siret"], "12312312312345")
        self.assertEqual(response.data[0]["slug"], "une-structure-38")
        self.assertTrue("sectors" in response.data[0])
        url = reverse("api:siae-retrieve-by-siren", args=["222222222"]) + "?token=" + self.user_token
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["siret"], "22222222233333")
        self.assertEqual(response.data[1]["siret"], "22222222233333")
        self.assertTrue("sectors" in response.data[0])


class SiaeRetrieveBySiretApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(name="Une structure", siret="12312312312345", department="38")
        SiaeFactory(name="Une autre structure", siret="22222222233333", department="69")
        SiaeFactory(name="Une autre structure avec le meme siret", siret="22222222233333", department="69")
        cls.user_token = generate_random_string()
        UserFactory(api_key=cls.user_token)

    def test_should_return_404_if_siret_malformed(self):
        for siret in ["123", "123123123123456", "123 123 123 12345"]:
            url = reverse("api:siae-retrieve-by-siret", args=[siret])
            response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
            self.assertEqual(response.status_code, 400)

    def test_should_return_empty_list_if_siret_unknown(self):
        url = reverse("api:siae-retrieve-by-siret", args=["44444444444444"])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(len(response.data), 0)

    def test_should_return_4O4_if_siae_excluded(self):
        siae_opcs = SiaeFactory(kind="OPCS", siret="99999999999999")
        url = reverse("api:siae-retrieve-by-siret", args=[siae_opcs.siret])  # anonymous
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        url = reverse("api:siae-retrieve-by-siret", args=[siae_opcs.siret])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(len(response.data), 0)

    def test_should_return_siae_list_if_siret_known(self):
        url = reverse("api:siae-retrieve-by-siret", args=["12312312312345"])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["siret"], "12312312312345")
        self.assertEqual(response.data[0]["slug"], "une-structure-38")
        url = reverse("api:siae-retrieve-by-siret", args=["22222222233333"])
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["siret"], "22222222233333")
        self.assertEqual(response.data[1]["siret"], "22222222233333")
        # authenticated user
        url = reverse("api:siae-retrieve-by-siret", args=["12312312312345"]) + "?token=" + self.user_token
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["siret"], "12312312312345")
        self.assertEqual(response.data[0]["slug"], "une-structure-38")
        self.assertTrue("sectors" in response.data[0])
        url = reverse("api:siae-retrieve-by-siret", args=["22222222233333"]) + "?token=" + self.user_token
        response = self.client.get(url, headers={"authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(type(response.data), list)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["siret"], "22222222233333")
        self.assertEqual(response.data[1]["siret"], "22222222233333")
        self.assertTrue("sectors" in response.data[0])


class SiaeChoicesApiTest(TestCase):
    def test_should_return_siae_kinds_list(self):
        # anonymous user
        url = reverse("api:siae-kinds-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_should_return_siae_presta_types_list(self):
        # anonymous user
        url = reverse("api:siae-presta-types-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
