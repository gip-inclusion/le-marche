from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse

from lemarche.networks.factories import NetworkFactory
from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeFactory, SiaeOfferFactory
from lemarche.siaes.models import Siae
from lemarche.users.factories import DEFAULT_PASSWORD, UserFactory
from lemarche.www.siaes.forms import SiaeSearchForm


class SiaeSearchFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(is_active=True)
        SiaeFactory(is_active=False)

    def test_search_should_return_live_siaes(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)


class SiaeKindSearchFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(kind=Siae.KIND_EI)
        SiaeFactory(kind=Siae.KIND_AI)

    def test_search_kind_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_kind_empty_string(self):
        url = reverse("siae:search_results") + "?kind="
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_kind_should_filter(self):
        url = reverse("siae:search_results") + f"?kind={Siae.KIND_EI}"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)

    def test_search_kind_multiple_should_filter(self):
        url = reverse("siae:search_results") + f"?kind={Siae.KIND_EI}&kind={Siae.KIND_AI}"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1 + 1)


class SiaePrestaTypeSearchFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(presta_type=[siae_constants.PRESTA_DISP])
        SiaeFactory(presta_type=[siae_constants.PRESTA_DISP, siae_constants.PRESTA_BUILD])

    def test_search_presta_type_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_presta_type_empty_string(self):
        url = reverse("siae:search_results") + "?presta_type="
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_presta_type_should_filter(self):
        url = reverse("siae:search_results") + f"?presta_type={siae_constants.PRESTA_BUILD}"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        url = reverse("siae:search_results") + f"?presta_type={siae_constants.PRESTA_DISP}"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1 + 1)


class SiaeTerritorySearchFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(is_qpv=True)
        SiaeFactory(is_zrr=True)

    def test_search_territory_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_territory_empty_string(self):
        url = reverse("siae:search_results") + "?territory="
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_territory_should_filter(self):
        url = reverse("siae:search_results") + "?territory=QPV"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)

    def test_search_territory_multiple_should_filter(self):
        url = reverse("siae:search_results") + "?territory=QPV&territory=ZRR"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1 + 1)

    def test_search_territory_multiple_should_filter_and_avoid_duplicates(self):
        SiaeFactory(is_qpv=True, is_zrr=True)
        url = reverse("siae:search_results") + "?territory=QPV&territory=ZRR"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1 + 1 + 1)


class SiaeSectorSearchFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory()  # siae_without_sector
        siae_with_one_sector = SiaeFactory()
        siae_with_two_sectors = SiaeFactory()
        siae_with_other_sector = SiaeFactory()
        cls.sector_1 = SectorFactory()
        cls.sector_2 = SectorFactory()
        cls.sector_3 = SectorFactory()
        siae_with_one_sector.sectors.add(cls.sector_1)
        siae_with_two_sectors.sectors.add(cls.sector_1, cls.sector_2)
        siae_with_other_sector.sectors.add(cls.sector_3)

    def test_search_sector_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 4)

    def test_search_sector_empty_string(self):
        url = reverse("siae:search_results") + "?sectors="
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 4)

    def test_search_sector_should_filter(self):
        url = reverse("siae:search_results") + f"?sectors={self.sector_1.slug}"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1 + 1)
        url = reverse("siae:search_results") + f"?sectors={self.sector_2.slug}"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)

    def test_search_sector_multiple_should_filter(self):
        url = reverse("siae:search_results") + f"?sectors={self.sector_1.slug}&sectors={self.sector_3.slug}"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2 + 1)  # OR

    def test_search_sector_multiple_should_not_return_duplicates(self):
        url = reverse("siae:search_results") + f"?sectors={self.sector_1.slug}&sectors={self.sector_2.slug}"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1 + 1)  # OR


class SiaeNetworkSearchFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.network = NetworkFactory()
        SiaeFactory()
        siae_with_network = SiaeFactory()
        siae_with_network.networks.add(cls.network)

    def test_search_network_empty(self):
        form = SiaeSearchForm({"networks": ""})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 2)

    def test_search_network(self):
        form = SiaeSearchForm({"networks": f"{self.network.slug}"})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 1)

    def test_search_unknown_network_ignores_filter(self):
        form = SiaeSearchForm({"networks": "coucou"})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 2)


class SiaePerimeterSearchFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # create the Perimeters
        cls.auvergne_rhone_alpes_perimeter = PerimeterFactory(
            name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84"
        )
        cls.isere_perimeter = PerimeterFactory(
            name="Isère", kind=Perimeter.KIND_DEPARTMENT, insee_code="38", region_code="84"
        )
        cls.grenoble_perimeter = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
            coords=Point(5.7301, 45.1825),
        )
        cls.chamrousse_perimeter = PerimeterFactory(
            name="Chamrousse",
            kind=Perimeter.KIND_CITY,
            insee_code="38567",
            department_code="38",
            region_code="84",
            post_codes=["38410"],
            coords=Point(5.8862, 45.1106),
        )
        cls.bretagne_perimeter = PerimeterFactory(name="Bretagne", kind=Perimeter.KIND_REGION, insee_code="R53")
        cls.finister_perimeter = PerimeterFactory(
            name="Finistère", kind=Perimeter.KIND_DEPARTMENT, insee_code="29", region_code="53"
        )
        cls.quimper_perimeter = PerimeterFactory(
            insee_code="29232",
            name="Quimper",
            kind=Perimeter.KIND_CITY,
            department_code="29",
            region_code="53",
            post_codes=["2923", "2924"],
            coords=Point(47.9911, -4.1126),
        )
        # create the Siaes
        SiaeFactory(
            city=cls.grenoble_perimeter.name,
            department=cls.grenoble_perimeter.department_code,
            region=cls.auvergne_rhone_alpes_perimeter.name,
            post_code=cls.grenoble_perimeter.post_codes[0],
            geo_range=Siae.GEO_RANGE_COUNTRY,
        )
        SiaeFactory(
            city=cls.grenoble_perimeter.name,
            department=cls.grenoble_perimeter.department_code,
            region=cls.auvergne_rhone_alpes_perimeter.name,
            post_code=cls.grenoble_perimeter.post_codes[0],
            geo_range=Siae.GEO_RANGE_REGION,
        )
        SiaeFactory(
            city=cls.grenoble_perimeter.name,
            department=cls.grenoble_perimeter.department_code,
            region=cls.auvergne_rhone_alpes_perimeter.name,
            post_code=cls.grenoble_perimeter.post_codes[1],
            geo_range=Siae.GEO_RANGE_DEPARTMENT,
        )
        SiaeFactory(
            city=cls.grenoble_perimeter.name,
            department=cls.grenoble_perimeter.department_code,
            region=cls.auvergne_rhone_alpes_perimeter.name,
            post_code=cls.grenoble_perimeter.post_codes[2],
            geo_range=Siae.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=10,
            coords=Point(5.7301, 45.1825),
        )
        # La Tronche is a city located just next to Grenoble
        SiaeFactory(
            city="La Tronche",
            department="38",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=Siae.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=10,
            coords=Point(5.746, 45.2124),
        )
        # Chamrousse is a city located further away from Grenoble
        SiaeFactory(
            city=cls.chamrousse_perimeter.name,
            department="38",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=Siae.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=5,
            coords=Point(5.8862, 45.1106),
        )
        SiaeFactory(
            city="Lyon",
            department="69",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=Siae.GEO_RANGE_COUNTRY,
        )
        SiaeFactory(
            city="Lyon",
            department="69",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=Siae.GEO_RANGE_REGION,
        )
        SiaeFactory(
            city="Lyon",
            department="69",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=Siae.GEO_RANGE_DEPARTMENT,
        )
        SiaeFactory(
            city="Lyon",
            department="69",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=Siae.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=50,
            coords=Point(4.8236, 45.7685),
        )
        SiaeFactory(
            city=cls.quimper_perimeter.name,
            department=cls.quimper_perimeter.department_code,
            region=cls.bretagne_perimeter.name,
            geo_range=Siae.GEO_RANGE_COUNTRY,
        )
        SiaeFactory(
            city=cls.quimper_perimeter.name,
            department=cls.quimper_perimeter.department_code,
            region=cls.bretagne_perimeter.name,
            geo_range=Siae.GEO_RANGE_REGION,
        )
        SiaeFactory(
            city=cls.quimper_perimeter.name,
            department=cls.quimper_perimeter.department_code,
            region=cls.bretagne_perimeter.name,
            geo_range=Siae.GEO_RANGE_DEPARTMENT,
        )
        SiaeFactory(
            city=cls.quimper_perimeter.name,
            department=cls.quimper_perimeter.department_code,
            region=cls.bretagne_perimeter.name,
            geo_range=Siae.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=50,
            coords=Point(47.9914, -4.0916),
        )

    def test_object_count(self):
        self.assertEqual(Perimeter.objects.count(), 7)
        self.assertEqual(Siae.objects.count(), 14)

    def test_search_perimeter_empty(self):
        form = SiaeSearchForm({"perimeters": [""]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 14)

    def test_search_perimeter_region(self):
        form = SiaeSearchForm({"perimeters": [self.auvergne_rhone_alpes_perimeter.id]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 10)

    def test_search_perimeter_not_exist(self):
        form = SiaeSearchForm({"perimeters": ["-1"]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 14)
        self.assertFalse(form.is_valid())
        self.assertIn("perimeters", form.errors.keys())
        self.assertIn("Périmètre inconnu", form.errors["perimeters"][0])

    def test_search_perimeter_department(self):
        form = SiaeSearchForm({"perimeters": [self.isere_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 6)

    def test_search_perimeter_city(self):
        """
        We should return:
        - all the Siae exactly in this city+department (4 SIAE)
        + all the Siae with geo_range=GEO_RANGE_CUSTOM + coords in the geo_range_custom_distance range of Grenoble (2 SIAE: Grenoble & La Tronche. Chamrousse is outside)  # noqa
        + all the Siae with geo_range=GEO_RANGE_DEPARTMENT + department=38 (1 SIAE)
        """
        form = SiaeSearchForm({"perimeters": [self.grenoble_perimeter.id]})
        self.assertTrue(form.is_valid())
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 2 + 2 + 1)

    def test_search_perimeter_city_2(self):
        """
        We should return:
        - all the Siae exactly in this city+department (1 SIAE)
        + all the Siae with geo_range=GEO_RANGE_CUSTOM + coords in the geo_range_custom_distance range of Grenoble (1 SIAE: Chamrousse. Grenoble & La Tronche are outside)  # noqa
        + all the Siae with geo_range=GEO_RANGE_DEPARTMENT + department=38 (1 SIAE)
        """
        form = SiaeSearchForm({"perimeters": [self.chamrousse_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 0 + 1 + 1)

    def test_search_perimeter_multiperimeter_1(self):
        """
        We should return:
        - all the Siae exactly in this city+department of Grenoble or Chamrousse (2 SIAE)
        + all the Siae with geo_range=GEO_RANGE_CUSTOM + coords in the geo_range_custom_distance range of Grenoble or Chamrousse (2 SIAE) # noqa
        + all the Siae with geo_range=GEO_RANGE_DEPARTMENT + department of Grenoble or chamrousse (2 SIAE)
        """
        form = SiaeSearchForm({"perimeters": [self.grenoble_perimeter, self.chamrousse_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 2 + 2 + 2)

    def test_search_perimeter_multiperimeter_2(self):
        """
        We should return:
        - all the Siae exactly in this city+department of Grenoble or quimper (2 SIAE)
        + all the Siae with geo_range=GEO_RANGE_CUSTOM + coords in the geo_range_custom_distance range of Grenoble or Quimper (2 SIAE) # noqa
        + all the Siae with geo_range=GEO_RANGE_DEPARTMENT + department of Grenoble or Quimper (3 SIAE)
        """
        form = SiaeSearchForm({"perimeters": [self.grenoble_perimeter, self.quimper_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 2 + 2 + 3)

    def test_search_perimeter_multiperimeter_error(self):
        """
        test one perimeter is good and the other one is not
        We should return the default qs with error
        """
        form = SiaeSearchForm({"perimeters": [self.grenoble_perimeter, "-1"]})
        qs = form.filter_queryset()
        self.assertFalse(form.is_valid())
        self.assertIn("perimeters", form.errors.keys())
        self.assertIn("Périmètre inconnu", form.errors["perimeters"][0])
        self.assertEqual(qs.count(), 14)


class SiaeSearchOrderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(name="Ma boite")
        SiaeFactory(name="Une autre structure")
        SiaeFactory(name="ABC Insertion")

    def test_should_bring_the_siae_with_users_to_the_top(self):
        siae_with_user = SiaeFactory(name="ZZ ESI")
        user = UserFactory()
        siae_with_user.users.add(user)
        url = reverse("siae:search_results", kwargs={})
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 3 + 1)
        self.assertEqual(siaes[0].has_user, True)
        self.assertEqual(siaes[0].name, "ZZ ESI")

    def test_should_bring_the_siae_with_descriptions_to_the_top(self):
        SiaeFactory(name="ZZ ESI 2", description="coucou")
        url = reverse("siae:search_results", kwargs={})
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 3 + 1)
        self.assertEqual(siaes[0].has_description, True)
        self.assertEqual(siaes[0].name, "ZZ ESI 2")

    def test_should_bring_the_siae_with_offers_to_the_top(self):
        siae_with_offer = SiaeFactory(name="ZZ ESI 3")
        SiaeOfferFactory(siae=siae_with_offer)
        siae_with_offer.save()  # to update the siae count fields
        url = reverse("siae:search_results", kwargs={})
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 3 + 1)
        self.assertEqual(siaes[0].has_offer, True)
        self.assertEqual(siaes[0].name, "ZZ ESI 3")

    def test_should_bring_the_siae_closer_to_the_city_to_the_top(self):
        grenoble_perimeter = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            coords=Point(5.7301, 45.1825),
        )
        SiaeFactory(
            name="ZZ GEO Pontcharra",
            department="38",
            geo_range=Siae.GEO_RANGE_DEPARTMENT,
            coords=Point(6.0271, 45.4144),
        )
        SiaeFactory(
            name="ZZ GEO La Tronche",
            department="38",
            geo_range=Siae.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=10,
            coords=Point(5.746, 45.2124),
        )
        SiaeFactory(
            name="ZZ GEO Grenoble",
            department="38",
            geo_range=Siae.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=10,
            coords=Point(5.7301, 45.1825),
        )
        url = reverse("siae:search_results") + f"?perimeters={grenoble_perimeter.id}"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 3)
        self.assertEqual(siaes[0].name, "ZZ GEO Grenoble")
        self.assertEqual(siaes[1].name, "ZZ GEO La Tronche")
        self.assertEqual(siaes[2].name, "ZZ GEO Pontcharra")


class SiaeDetailTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_should_display_contact_fields_to_authenticated_users(self):
        siae = SiaeFactory(name="Ma boite", contact_email="contact@example.com")
        self.client.login(email=self.user.email, password=DEFAULT_PASSWORD)
        url = reverse("siae:detail", args=[siae.slug])
        response = self.client.get(url)
        self.assertContains(response, siae.contact_email)

    def test_should_not_display_contact_fields_to_anonymous_users(self):
        siae = SiaeFactory(name="Ma boite", contact_email="contact@example.com")
        url = reverse("siae:detail", args=[siae.slug])
        response = self.client.get(url)
        self.assertNotContains(response, siae.contact_email)
