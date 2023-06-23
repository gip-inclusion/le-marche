from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse

from lemarche.networks.factories import NetworkFactory
from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeClientReferenceFactory, SiaeFactory, SiaeOfferFactory
from lemarche.siaes.models import Siae
from lemarche.users.factories import UserFactory
from lemarche.www.siaes.forms import SiaeFilterForm


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
        SiaeFactory(kind=siae_constants.KIND_EI)
        SiaeFactory(kind=siae_constants.KIND_AI)

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
        url = reverse("siae:search_results") + f"?kind={siae_constants.KIND_EI}"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)

    def test_search_kind_multiple_should_filter(self):
        url = reverse("siae:search_results") + f"?kind={siae_constants.KIND_EI}&kind={siae_constants.KIND_AI}"
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

    def test_search_unknown_sector_ignores_filter(self):
        url = reverse("siae:search_results") + "?sectors=coucou"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 4)


class SiaeNetworkSearchFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.network = NetworkFactory()
        SiaeFactory()
        siae_with_network = SiaeFactory()
        siae_with_network.networks.add(cls.network)

    def test_search_network_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_network_empty_string(self):
        url = reverse("siae:search_results") + "?networks="
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_network_should_filter(self):
        url = reverse("siae:search_results") + f"?networks={self.network.slug}"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)

    def test_search_unknown_network_ignores_filter(self):
        url = reverse("siae:search_results") + "?networks=coucou"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)


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
            geo_range=siae_constants.GEO_RANGE_COUNTRY,
        )
        SiaeFactory(
            city=cls.grenoble_perimeter.name,
            department=cls.grenoble_perimeter.department_code,
            region=cls.auvergne_rhone_alpes_perimeter.name,
            post_code=cls.grenoble_perimeter.post_codes[0],
            geo_range=siae_constants.GEO_RANGE_REGION,
        )
        SiaeFactory(
            city=cls.grenoble_perimeter.name,
            department=cls.grenoble_perimeter.department_code,
            region=cls.auvergne_rhone_alpes_perimeter.name,
            post_code=cls.grenoble_perimeter.post_codes[1],
            geo_range=siae_constants.GEO_RANGE_DEPARTMENT,
        )
        SiaeFactory(
            city=cls.grenoble_perimeter.name,
            department=cls.grenoble_perimeter.department_code,
            region=cls.auvergne_rhone_alpes_perimeter.name,
            post_code=cls.grenoble_perimeter.post_codes[2],
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=10,
            coords=Point(5.7301, 45.1825),
        )
        # La Tronche is a city located just next to Grenoble
        SiaeFactory(
            city="La Tronche",
            department="38",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=10,
            coords=Point(5.746, 45.2124),
        )
        # Chamrousse is a city located further away from Grenoble
        SiaeFactory(
            city=cls.chamrousse_perimeter.name,
            department="38",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=5,
            coords=Point(5.8862, 45.1106),
        )
        SiaeFactory(
            city="Lyon",
            department="69",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=siae_constants.GEO_RANGE_COUNTRY,
        )
        SiaeFactory(
            city="Lyon",
            department="69",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=siae_constants.GEO_RANGE_REGION,
        )
        SiaeFactory(
            city="Lyon",
            department="69",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=siae_constants.GEO_RANGE_DEPARTMENT,
        )
        SiaeFactory(
            city="Lyon",
            department="69",
            region=cls.auvergne_rhone_alpes_perimeter.name,
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=50,
            coords=Point(4.8236, 45.7685),
        )
        SiaeFactory(
            city=cls.quimper_perimeter.name,
            department=cls.quimper_perimeter.department_code,
            region=cls.bretagne_perimeter.name,
            geo_range=siae_constants.GEO_RANGE_COUNTRY,
        )
        SiaeFactory(
            city=cls.quimper_perimeter.name,
            department=cls.quimper_perimeter.department_code,
            region=cls.bretagne_perimeter.name,
            geo_range=siae_constants.GEO_RANGE_REGION,
        )
        SiaeFactory(
            city=cls.quimper_perimeter.name,
            department=cls.quimper_perimeter.department_code,
            region=cls.bretagne_perimeter.name,
            geo_range=siae_constants.GEO_RANGE_DEPARTMENT,
        )
        SiaeFactory(
            city=cls.quimper_perimeter.name,
            department=cls.quimper_perimeter.department_code,
            region=cls.bretagne_perimeter.name,
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=50,
            coords=Point(47.9914, -4.0916),
        )

    def test_object_count(self):
        self.assertEqual(Perimeter.objects.count(), 7)
        self.assertEqual(Siae.objects.count(), 14)

    def test_search_perimeter_empty(self):
        form = SiaeFilterForm({"perimeters": [""]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 14)

    def test_search_perimeter_not_exist(self):
        form = SiaeFilterForm({"perimeters": ["-1"]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 14)
        self.assertFalse(form.is_valid())
        self.assertIn("perimeters", form.errors.keys())
        self.assertIn("Sélectionnez un choix valide", form.errors["perimeters"][0])

    def test_search_perimeter_region(self):
        form = SiaeFilterForm({"perimeters": [self.auvergne_rhone_alpes_perimeter.slug]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 10)

    def test_search_perimeter_department(self):
        form = SiaeFilterForm({"perimeters": [self.isere_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 6)

    def test_search_perimeter_city(self):
        """
        We should return:
        - all the Siae exactly in the city - Grenoble (4 Siae)
        + all the Siae in the city's department (except GEO_RANGE_CUSTOM) - Isere (0 new Siae)
        + all the Siae with geo_range=GEO_RANGE_CUSTOM + coords in the geo_range_custom_distance range of Grenoble (1 new Siae: La Tronche. Chamrousse is outside)  # noqa
        """
        form = SiaeFilterForm({"perimeters": [self.grenoble_perimeter.slug]})
        self.assertTrue(form.is_valid())
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 4 + 0 + 1)

    def test_search_perimeter_city_2(self):
        """
        We should return:
        - all the Siae exactly in the city - Chamrousse (1 Siae)
        + all the Siae in the city's department (except GEO_RANGE_CUSTOM) - Isere (3 new Siae)
        + all the Siae with geo_range=GEO_RANGE_CUSTOM + coords in the geo_range_custom_distance range of Grenoble (1 Siae, 0 new: Chamrousse. Grenoble & La Tronche are outside)  # noqa
        """
        form = SiaeFilterForm({"perimeters": [self.chamrousse_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 1 + 3 + 0)

    def test_search_perimeter_multiperimeter_1(self):
        """
        We should return:
        - all the Siae exactly in these cities - Grenoble & Chamrousse (4 + 1 Siae)
        + all the Siae in the cities departments (except GEO_RANGE_CUSTOM) - Isere (0 new Siae)
        + all the Siae with geo_range=GEO_RANGE_CUSTOM + coords in the geo_range_custom_distance range of Grenoble or Chamrousse (2 Siae, 1 new) # noqa
        """
        form = SiaeFilterForm({"perimeters": [self.grenoble_perimeter, self.chamrousse_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 5 + 0 + 1)

    def test_search_perimeter_multiperimeter_2(self):
        """
        We should return:
        - all the Siae exactly in these cities - Grenoble & Quimper (4 + 4)
        + all the Siae in the cities departments (except GEO_RANGE_CUSTOM) - Isere & 29 (0 new Siae)
        + all the Siae with geo_range=GEO_RANGE_CUSTOM + coords in the geo_range_custom_distance range of Grenoble or Quimper (1 new Siae) # noqa
        """
        form = SiaeFilterForm({"perimeters": [self.grenoble_perimeter, self.quimper_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 8 + 0 + 1)

    def test_search_perimeter_multiperimeter_error(self):
        """
        test one perimeter is good and the other one is not
        We should return the default qs with error
        """
        form = SiaeFilterForm({"perimeters": [self.grenoble_perimeter, "-1"]})
        qs = form.filter_queryset()
        self.assertFalse(form.is_valid())
        self.assertIn("perimeters", form.errors.keys())
        self.assertIn("Sélectionnez un choix valide", form.errors["perimeters"][0])
        self.assertEqual(qs.count(), 14)

    def test_search_location_empty(self):
        form = SiaeFilterForm({"locations": [""]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 14)

    def test_search_location_not_exist(self):
        form = SiaeFilterForm({"locations": ["-1"]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 14)
        self.assertFalse(form.is_valid())
        self.assertIn("locations", form.errors.keys())
        self.assertIn("Sélectionnez un choix valide", form.errors["locations"][0])

    def test_search_location_region(self):
        form = SiaeFilterForm({"locations": [self.auvergne_rhone_alpes_perimeter.slug]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 10)

    def test_search_location_department(self):
        form = SiaeFilterForm({"locations": [self.isere_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 6)

    def test_search_location_city(self):
        """
        We should return all the Siae exactly in the city - Grenoble (4 Siae)
        """
        form = SiaeFilterForm({"locations": [self.grenoble_perimeter.slug]})
        self.assertTrue(form.is_valid())
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 4)


class SiaeHasClientReferencesFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_with_client_reference = SiaeFactory()
        SiaeClientReferenceFactory(siae=cls.siae_with_client_reference)
        cls.siae_with_client_reference.save()  # to set client_reference_count=1
        cls.siae_without_client_reference = SiaeFactory()  # client_reference_count=0

    def test_search_has_client_references_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_has_client_references_empty_string(self):
        url = reverse("siae:search_results") + "?has_client_references="
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_has_client_references_should_filter(self):
        # True
        url = reverse("siae:search_results") + "?has_client_references=True"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_with_client_reference.id)
        # False
        url = reverse("siae:search_results") + "?has_client_references=False"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_without_client_reference.id)


class SiaeHasGroupsFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_with_group = SiaeFactory(group_count=1)
        cls.siae_without_group = SiaeFactory(group_count=0)

    def test_search_has_groups_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_has_groups_empty_string(self):
        url = reverse("siae:search_results") + "?has_groups="
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)

    def test_search_has_groups_should_filter(self):
        # True
        url = reverse("siae:search_results") + "?has_groups=True"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_with_group.id)
        # False
        url = reverse("siae:search_results") + "?has_groups=False"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_without_group.id)


class SiaeFullTextSearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_1 = SiaeFactory(name="Ma boite", siret="11111111111111")
        cls.siae_2 = SiaeFactory(name="Une autre activité", siret="22222222222222")
        cls.siae_3 = SiaeFactory(name="ABC Insertion", siret="33333333344444")
        cls.siae_4 = SiaeFactory(name="Empty", brand="ETHICOFIL", siret="55555555555555")

    def test_search_query_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 4)

    def test_search_query_empty_string(self):
        url = reverse("siae:search_results") + "?q="
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 4)

    def test_search_by_siae_name(self):
        # name & brand work similarly
        url = reverse("siae:search_results") + "?q=boite"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].name, self.siae_1.name)
        # full name with space
        url = reverse("siae:search_results") + "?q=ma boite"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].name, self.siae_1.name)

    def test_search_by_siae_name_partial(self):
        url = reverse("siae:search_results") + "?q=insert"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].name, self.siae_3.name)

    def test_search_by_siae_name_should_be_case_insensitive(self):
        url = reverse("siae:search_results") + "?q=abc"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].name, self.siae_3.name)
        # with case
        url = reverse("siae:search_results") + "?q=ABC"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].name, self.siae_3.name)

    def test_search_by_siae_name_should_ignore_accents(self):
        url = reverse("siae:search_results") + "?q=activite"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].name, self.siae_2.name)
        # with accent
        url = reverse("siae:search_results") + "?q=activité"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].name, self.siae_2.name)

    def test_search_by_siae_brand(self):
        url = reverse("siae:search_results") + "?q=ethicofil"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].name, self.siae_4.name)

    def test_search_by_siae_brand_should_accept_typos(self):
        url = reverse("siae:search_results") + "?q=ethicofl"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].name, self.siae_4.name)

    def test_search_by_siae_name_order_by_similarity(self):
        SiaeFactory(name="Ma botte", siret="11111111111111")
        url = reverse("siae:search_results") + "?q=boite"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)
        self.assertEqual(siaes[0].name, self.siae_1.name)

    def test_search_by_siae_siret(self):
        url = reverse("siae:search_results") + "?q=22222222222222"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        # siren search
        url = reverse("siae:search_results") + "?q=333333333"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        # siret with space
        url = reverse("siae:search_results") + "?q=333 333 333 44444"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)


class SiaeClientReferenceTextSearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_1 = SiaeFactory(name="Ma boite")
        cls.siae_2 = SiaeFactory(name="Une autre activité")
        cls.siae_3 = SiaeFactory(name="ABC Insertion")
        cls.siae_4 = SiaeFactory(name="Empty", brand="ETHICOFIL")
        cls.client_reference_1_1 = SiaeClientReferenceFactory(name="Big Corp", siae=cls.siae_1)
        cls.client_reference_1_2 = SiaeClientReferenceFactory(name="SNCF", siae=cls.siae_1)
        cls.client_reference_2_1 = SiaeClientReferenceFactory(name="SNCF IDF", siae=cls.siae_2)

    def test_search_client_reference_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 4)

    def test_search_client_reference_empty_string(self):
        url = reverse("siae:search_results") + "?company_client_reference="
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 4)

    def test_search_by_company_name_partial(self):
        url = reverse("siae:search_results") + "?company_client_reference=Corp"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)

    def test_search_by_company_name_should_be_case_insensitive(self):
        url = reverse("siae:search_results") + "?company_client_reference=sncf"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)
        # with case
        url = reverse("siae:search_results") + "?company_client_reference=SNCF"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)


class SiaeSearchOrderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiaeFactory(name="Ma boite")
        SiaeFactory(name="Une autre structure")
        SiaeFactory(name="ABC Insertion")
        cls.grenoble_perimeter = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            # post_codes=["38000", "38100", "38700"],
            coords=Point(5.7301, 45.1825),
        )

    def test_should_order_by_last_updated(self):
        url = reverse("siae:search_results", kwargs={})
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 3)
        self.assertEqual(siaes[0].name, "ABC Insertion")

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
        SiaeFactory(
            name="ZZ GEO Pontcharra",
            department="38",
            geo_range=siae_constants.GEO_RANGE_DEPARTMENT,
            coords=Point(6.0271, 45.4144),
        )
        SiaeFactory(
            name="ZZ GEO La Tronche",
            department="38",
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=10,
            coords=Point(5.746, 45.2124),
        )
        SiaeFactory(
            name="ZZ GEO Grenoble",
            department="38",
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            geo_range_custom_distance=10,
            coords=Point(5.7301, 45.1825),
        )
        url = reverse("siae:search_results") + f"?perimeters={self.grenoble_perimeter.slug}"
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
        self.client.force_login(self.user)
        url = reverse("siae:detail", args=[siae.slug])
        response = self.client.get(url)
        self.assertContains(response, siae.contact_email)

    def test_should_not_display_contact_fields_to_anonymous_users(self):
        siae = SiaeFactory(name="Ma boite", contact_email="contact@example.com")
        url = reverse("siae:detail", args=[siae.slug])
        response = self.client.get(url)
        self.assertNotContains(response, siae.contact_email)
