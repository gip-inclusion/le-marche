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
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_login(self.user)

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
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_login(self.user)

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
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_login(self.user)

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
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_login(self.user)

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
        cls.user = UserFactory()
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
        form = SiaeFilterForm(data={"perimeters": [""]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 14)

    def test_search_perimeter_not_exist(self):
        form = SiaeFilterForm(data={"perimeters": ["-1"]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 14)
        self.assertFalse(form.is_valid())
        self.assertIn("perimeters", form.errors.keys())
        self.assertIn("Sélectionnez un choix valide", form.errors["perimeters"][0])

    def test_search_perimeter_region(self):
        form = SiaeFilterForm(data={"perimeters": [self.auvergne_rhone_alpes_perimeter.slug]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 10)

    def test_search_perimeter_department(self):
        form = SiaeFilterForm(data={"perimeters": [self.isere_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 6)

    def test_search_perimeter_city(self):
        """
        We should return:
        - all the Siae exactly in the city - Grenoble (4 Siae)
        + all the Siae in the city's department (except GEO_RANGE_CUSTOM) - Isere (0 new Siae)
        + all the Siae with geo_range=GEO_RANGE_CUSTOM + coords in the geo_range_custom_distance range of Grenoble (1 new Siae: La Tronche. Chamrousse is outside)  # noqa
        """
        form = SiaeFilterForm(data={"perimeters": [self.grenoble_perimeter.slug]})
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
        form = SiaeFilterForm(data={"perimeters": [self.chamrousse_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 1 + 3 + 0)

    def test_search_perimeter_multiperimeter_1(self):
        """
        We should return:
        - all the Siae exactly in these cities - Grenoble & Chamrousse (4 + 1 Siae)
        + all the Siae in the cities departments (except GEO_RANGE_CUSTOM) - Isere (0 new Siae)
        + all the Siae with geo_range=GEO_RANGE_CUSTOM + coords in the geo_range_custom_distance range of Grenoble or Chamrousse (2 Siae, 1 new) # noqa
        """
        form = SiaeFilterForm(data={"perimeters": [self.grenoble_perimeter, self.chamrousse_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 5 + 0 + 1)

    def test_search_perimeter_multiperimeter_2(self):
        """
        We should return:
        - all the Siae exactly in these cities - Grenoble & Quimper (4 + 4)
        + all the Siae in the cities departments (except GEO_RANGE_CUSTOM) - Isere & 29 (0 new Siae)
        + all the Siae with geo_range=GEO_RANGE_CUSTOM + coords in the geo_range_custom_distance range of Grenoble or Quimper (1 new Siae) # noqa
        """
        form = SiaeFilterForm(data={"perimeters": [self.grenoble_perimeter, self.quimper_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 8 + 0 + 1)

    def test_search_perimeter_multiperimeter_error(self):
        """
        test one perimeter is good and the other one is not
        We should return the default qs with error
        """
        form = SiaeFilterForm(data={"perimeters": [self.grenoble_perimeter, "-1"]})
        qs = form.filter_queryset()
        self.assertFalse(form.is_valid())
        self.assertIn("perimeters", form.errors.keys())
        self.assertIn("Sélectionnez un choix valide", form.errors["perimeters"][0])
        self.assertEqual(qs.count(), 14)

    def test_search_location_empty(self):
        form = SiaeFilterForm(data={"locations": [""]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 14)

    def test_search_location_not_exist(self):
        form = SiaeFilterForm(data={"locations": ["-1"]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 14)
        self.assertFalse(form.is_valid())
        self.assertIn("locations", form.errors.keys())
        self.assertIn("Sélectionnez un choix valide", form.errors["locations"][0])

    def test_search_location_region(self):
        form = SiaeFilterForm(data={"locations": [self.auvergne_rhone_alpes_perimeter.slug]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 10)

    def test_search_location_department(self):
        form = SiaeFilterForm(data={"locations": [self.isere_perimeter]})
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 6)

    def test_search_location_city(self):
        """
        We should return all the Siae exactly in the city - Grenoble (4 Siae)
        """
        form = SiaeFilterForm(data={"locations": [self.grenoble_perimeter.slug]})
        self.assertTrue(form.is_valid())
        qs = form.filter_queryset()
        self.assertEqual(qs.count(), 4)


class SiaeFilterFormAvancedSearchTest(TestCase):
    def test_disabled_fields_activated(self):
        form = SiaeFilterForm(advanced_search=False)
        for _field in form.DISABLED_FOR_ANONYMOUS:
            self.assertTrue(form.fields.get(_field).disabled)

    def test_disabled_fields_deactivated(self):
        form = SiaeFilterForm()
        for _field in form.DISABLED_FOR_ANONYMOUS:
            self.assertFalse(form.fields.get(_field).disabled)

    def test_is_advanced_search_true(self):
        form = SiaeFilterForm(data={"kind": ["ETTI"]})
        self.assertTrue(form.is_advanced_search())

    def test_is_advanced_search_false(self):
        form_1 = SiaeFilterForm(data={})
        self.assertFalse(form_1.is_advanced_search())

        form_2 = SiaeFilterForm(data={"perimeters": ["paris-75"]})
        self.assertFalse(form_2.is_advanced_search())

        form_3 = SiaeFilterForm(data={"kind": []})
        self.assertFalse(form_3.is_advanced_search())


class SiaeHasClientReferencesFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_with_client_reference = SiaeFactory()
        SiaeClientReferenceFactory(siae=cls.siae_with_client_reference)
        cls.siae_with_client_reference.save()  # to set client_reference_count=1
        cls.siae_without_client_reference = SiaeFactory()  # client_reference_count=0
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_login(self.user)

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
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_login(self.user)

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


class SiaeCAFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_without_ca_and_ca_api = SiaeFactory()
        cls.siae_50k = SiaeFactory(ca=50000)
        cls.siae_110k = SiaeFactory(ca=110000)
        cls.siae_120k = SiaeFactory(api_entreprise_ca=120000)
        cls.siae_550k = SiaeFactory(ca=550000, api_entreprise_ca=80000)
        cls.siae_2m = SiaeFactory(ca=2000000, api_entreprise_ca=0)
        cls.siae_7m = SiaeFactory(api_entreprise_ca=7000000)
        cls.siae_50m = SiaeFactory(ca=0, api_entreprise_ca=50000000)
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_login(self.user)

    def test_search_query_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 8)

    def test_search_ca_less_100k_filter(self):
        url = reverse("siae:search_results") + "?ca=-100000"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_50k.id)

    def test_search_ca_more_100k_filter(self):
        url = reverse("siae:search_results") + "?ca=100000-500000"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)
        self.assertEqual(siaes[0].id, self.siae_120k.id)
        self.assertEqual(siaes[1].id, self.siae_110k.id)

    def test_search_ca_more_500k_filter(self):
        url = reverse("siae:search_results") + "?ca=500000-1000000"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_550k.id)

    def test_search_ca_more_1m_filter(self):
        url = reverse("siae:search_results") + "?ca=1000000-5000000"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_2m.id)

    def test_search_ca_more_5m_filter(self):
        url = reverse("siae:search_results") + "?ca=5000000-10000000"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_7m.id)

    def test_search_ca_more_10m_filter(self):
        url = reverse("siae:search_results") + "?ca=10000000-"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_50m.id)


class SiaeLegalFormFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_legal_form_sarl = SiaeFactory(legal_form="SARL")
        cls.siae_legal_form_sa = SiaeFactory(legal_form="SA")
        cls.siae_legal_form_empty = SiaeFactory(legal_form="")
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_login(self.user)

    def test_search_legal_form_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 3)

    def test_search_legal_form_empty_string(self):
        url = reverse("siae:search_results") + "?legal_form="
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 3)

    def test_search_legal_form_should_filter(self):
        # single
        url = reverse("siae:search_results") + "?legal_form=SARL"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_legal_form_sarl.id)

    def test_search_legal_form_multiple_should_filter(self):
        url = reverse("siae:search_results") + "?legal_form=SARL&legal_form=SA"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1 + 1)


class SiaeEmployeesFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_without_employees = SiaeFactory()
        cls.siae_3 = SiaeFactory(employees_insertion_count=3)
        cls.siae_9 = SiaeFactory(employees_permanent_count=9)
        cls.siae_10 = SiaeFactory(c2_etp_count=9, employees_permanent_count=1)
        cls.siae_49 = SiaeFactory(employees_insertion_count=40, employees_permanent_count=9)
        cls.siae_50 = SiaeFactory(c2_etp_count=49.5)
        cls.siae_100 = SiaeFactory(api_entreprise_employees="100 à 199 salariés")
        cls.siae_150 = SiaeFactory(employees_insertion_count=150, api_entreprise_employees="200 à 249 salariés")
        cls.siae_252 = SiaeFactory(
            employees_insertion_count=150,
            employees_permanent_count=102,
            api_entreprise_employees="1 000 à 1 999 salariés",
        )
        cls.siae_550 = SiaeFactory(employees_insertion_count=550, c2_etp_count=490)
        cls.siae_3000 = SiaeFactory(api_entreprise_employees="2 000 à 4 999 salariés")

    def test_search_query_empty(self):
        url = reverse("siae:search_results")
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 11)

    def test_search_employees_1_to_9_filter(self):
        url = reverse("siae:search_results") + "?employees=1-9"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)
        self.assertEqual(siaes[0].id, self.siae_9.id)
        self.assertEqual(siaes[1].id, self.siae_3.id)

    def test_search_employees_10_to_49_filter(self):
        url = reverse("siae:search_results") + "?employees=10-49"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)
        self.assertEqual(siaes[0].id, self.siae_49.id)
        self.assertEqual(siaes[1].id, self.siae_10.id)

    def test_search_employees_50_to_99_filter(self):
        url = reverse("siae:search_results") + "?employees=50-99"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_50.id)

    def test_search_employees_100_to_249_filter(self):
        url = reverse("siae:search_results") + "?employees=100-249"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)
        self.assertEqual(siaes[0].id, self.siae_150.id)
        self.assertEqual(siaes[1].id, self.siae_100.id)

    def test_search_employees_250_to_499_filter(self):
        url = reverse("siae:search_results") + "?employees=250-499"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 1)
        self.assertEqual(siaes[0].id, self.siae_252.id)

    def test_search_employees_more_500_filter(self):
        url = reverse("siae:search_results") + "?employees=500-"
        response = self.client.get(url)
        siaes = list(response.context["siaes"])
        self.assertEqual(len(siaes), 2)
        self.assertEqual(siaes[0].id, self.siae_3000.id)
        self.assertEqual(siaes[1].id, self.siae_550.id)


class SiaeFullTextSearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_1 = SiaeFactory(name="Ma boite", siret="11111111111111")
        cls.siae_2 = SiaeFactory(name="Une autre activité", siret="22222222222222")
        cls.siae_3 = SiaeFactory(name="ABC Insertion", siret="33333333344444")
        cls.siae_4 = SiaeFactory(name="Empty", brand="ETHICOFIL", siret="55555555555555")
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_login(self.user)

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
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_login(self.user)

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
