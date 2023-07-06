from django.test import TestCase

from lemarche.labels.factories import LabelFactory
from lemarche.networks.factories import NetworkFactory
from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeFactory, SiaeGroupFactory, SiaeLabelOldFactory, SiaeOfferFactory
from lemarche.siaes.models import Siae, SiaeGroup, SiaeLabel, SiaeUser
from lemarche.users.factories import UserFactory


class SiaeGroupModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_group = SiaeGroupFactory(name="Mon groupement")

    def test_slug_field(self):
        self.assertEqual(self.siae_group.slug, "mon-groupement")

    def test_str(self):
        self.assertEqual(str(self.siae_group), "Mon groupement")


class SiaeGroupModelSaveTest(TestCase):
    def test_update_last_updated_fields(self):
        siae_group = SiaeGroupFactory()
        self.assertEqual(siae_group.employees_insertion_count, None)
        self.assertEqual(siae_group.employees_insertion_count_last_updated, None)
        # new value: last_updated field will be set
        siae_group = SiaeGroup.objects.get(id=siae_group.id)  # we need to fetch it again to pass through the __init__
        siae_group.employees_insertion_count = 10
        siae_group.save()
        self.assertEqual(siae_group.employees_insertion_count, 10)
        self.assertNotEqual(siae_group.employees_insertion_count_last_updated, None)
        employees_insertion_count_last_updated = siae_group.employees_insertion_count_last_updated
        # same value: last_updated field will not be updated
        siae_group = SiaeGroup.objects.get(id=siae_group.id)
        siae_group.employees_insertion_count = 10
        siae_group.save()
        self.assertEqual(siae_group.employees_insertion_count, 10)
        self.assertEqual(siae_group.employees_insertion_count_last_updated, employees_insertion_count_last_updated)
        # updated value: last_updated field will be updated
        siae_group = SiaeGroup.objects.get(id=siae_group.id)
        siae_group.employees_insertion_count = 15
        siae_group.save()
        self.assertEqual(siae_group.employees_insertion_count, 15)
        self.assertNotEqual(siae_group.employees_insertion_count_last_updated, employees_insertion_count_last_updated)


class SiaeModelTest(TestCase):
    def setUp(self):
        pass

    def test_str(self):
        siae = SiaeFactory(name="Ma boite")
        self.assertEqual(str(siae), "Ma boite")

    def test_name_display_property(self):
        siae_without_brand = SiaeFactory(name="Ma raison sociale")
        siae_with_brand = SiaeFactory(name="Ma raison sociale", brand="Mon enseigne")
        self.assertEqual(siae_without_brand.name_display, "Ma raison sociale")
        self.assertEqual(siae_with_brand.name_display, "Mon enseigne")

    def test_siret_display_property(self):
        siae_with_siret = SiaeFactory(siret="12312312312345")
        self.assertEqual(siae_with_siret.siret_display, "123 123 123 12345")
        siae_with_siren = SiaeFactory(siret="123123123")
        self.assertEqual(siae_with_siren.siret_display, "123 123 123")
        siae_with_anormal_siret = SiaeFactory(siret="123123123123")
        self.assertEqual(siae_with_anormal_siret.siret_display, "123123123123")

    def test_geo_range_pretty_display_property(self):
        siae_country = SiaeFactory(geo_range=siae_constants.GEO_RANGE_COUNTRY)
        self.assertEqual(siae_country.geo_range_pretty_display, "France entière")
        siae_region = SiaeFactory(geo_range=siae_constants.GEO_RANGE_REGION, region="Guadeloupe")
        self.assertEqual(siae_region.geo_range_pretty_display, "région (Guadeloupe)")
        siae_department = SiaeFactory(
            geo_range=siae_constants.GEO_RANGE_DEPARTMENT, region="Bretagne", department="29"
        )
        self.assertEqual(siae_department.geo_range_pretty_display, "département (29)")
        siae_custom = SiaeFactory(
            geo_range=siae_constants.GEO_RANGE_CUSTOM,
            region="Bretagne",
            department="29",
            city="Quimper",
            geo_range_custom_distance=50,
        )
        self.assertEqual(siae_custom.geo_range_pretty_display, "50 km")
        siae_custom_empty = SiaeFactory(
            geo_range=siae_constants.GEO_RANGE_CUSTOM, region="Bretagne", department="29", city="Quimper"
        )
        self.assertEqual(siae_custom_empty.geo_range_pretty_display, "non disponible")

    def test_is_missing_contact_property(self):
        siae_nok = SiaeFactory(name="Ma boite", contact_email="")
        self.assertTrue(siae_nok.is_missing_contact)
        siae_ok = SiaeFactory(
            name="Ma boite",
            contact_email="email@example.com",
        )
        self.assertFalse(siae_ok.is_missing_contact)

    def test_is_missing_content_property(self):
        siae_missing: Siae = SiaeFactory(name="Ma boite", contact_email="")
        score_completion_before = siae_missing.completion_percent
        self.assertTrue(siae_missing.is_missing_content)
        siae_full: Siae = SiaeFactory(
            name="Ma boite",
            contact_website="https://example.com",
            contact_email="email@example.com",
            contact_phone="0000000000",
            description="test",
        )
        self.assertTrue(score_completion_before < siae_full.completion_percent)
        score_completion_before = siae_full.completion_percent
        sector = SectorFactory()
        siae_full.sectors.add(sector)
        SiaeOfferFactory(siae=siae_full)
        SiaeLabelOldFactory(siae=siae_full)
        siae_full.save()  # to update stats
        self.assertFalse(siae_full.is_missing_content)
        self.assertTrue(score_completion_before < siae_full.completion_percent)

        siae_full_2: Siae = SiaeFactory(
            name="Ma boite",
            contact_website="https://example.com",
            # contact_email="email@example.com",
            # contact_phone="0000000000",
            description="test",
        )
        siae_full_2.sectors.add(sector)
        SiaeOfferFactory(siae=siae_full_2)
        SiaeLabelOldFactory(siae=siae_full_2)
        siae_full_2.save()  # to update stats
        self.assertFalse(siae_full_2.is_missing_content)

    def test_kind_is_esat_or_ea_property(self):
        siae_esat = SiaeFactory(kind=siae_constants.KIND_ESAT)
        self.assertTrue(siae_esat.kind_is_esat_or_ea)
        siae_ea = SiaeFactory(kind=siae_constants.KIND_EA)
        self.assertTrue(siae_ea.kind_is_esat_or_ea)
        siae_ei = SiaeFactory(kind=siae_constants.KIND_EI)
        self.assertFalse(siae_ei.kind_is_esat_or_ea)


class SiaeModelSaveTest(TestCase):
    def setUp(self):
        pass

    def test_slug_field_on_save(self):
        siae = SiaeFactory(name="L'Insertion par le HAUT", department="01")
        self.assertEqual(siae.slug, "linsertion-par-le-haut-01")
        siae = SiaeFactory(name="Structure sans département", department="")
        self.assertEqual(siae.slug, "structure-sans-departement-")
        siae_doublon_1 = SiaeFactory(name="Structure doublon", department="01")
        siae_doublon_2 = SiaeFactory(name="Structure doublon", department="15")
        siae_doublon_3 = SiaeFactory(name="Structure doublon", department="15")
        self.assertEqual(siae_doublon_1.slug, "structure-doublon-01")
        self.assertEqual(siae_doublon_2.slug, "structure-doublon-15")
        self.assertTrue(siae_doublon_3.slug.startswith("structure-doublon-15-"))  # uuid4 at the end
        self.assertTrue(len(siae_doublon_2.slug) < len(siae_doublon_3.slug))
        siae_doublon_10 = SiaeFactory(name="Structure doublon sans departement", department="")
        siae_doublon_11 = SiaeFactory(name="Structure doublon sans departement", department="")
        self.assertEqual(siae_doublon_10.slug, "structure-doublon-sans-departement-")
        self.assertTrue(siae_doublon_11.slug.startswith("structure-doublon-sans-departement--"))  # uuid4 at the end
        self.assertTrue(len(siae_doublon_10.slug) < len(siae_doublon_11.slug))

    def test_update_related_offer_count_on_save(self):
        siae = SiaeFactory()
        self.assertEqual(siae.offer_count, 0)
        SiaeOfferFactory(siae=siae)
        self.assertEqual(siae.offers.count(), 1)
        # self.assertEqual(siae.offer_count, 1)  # won't work, need to call save() method to update stat fields
        siae.save()
        self.assertEqual(siae.offer_count, 1)

    def test_update_m2m_sector_count_on_save(self):
        siae = SiaeFactory()
        sector = SectorFactory()
        self.assertEqual(siae.sector_count, 0)
        siae.sectors.add(sector)
        self.assertEqual(siae.sectors.count(), 1)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.sector_count, 1)

    def test_update_m2m_network_count_on_save(self):
        siae = SiaeFactory()
        network = NetworkFactory()
        self.assertEqual(siae.network_count, 0)
        siae.networks.add(network)
        self.assertEqual(siae.networks.count(), 1)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.network_count, 1)

    def test_update_m2m_group_count_on_save(self):
        siae = SiaeFactory()
        group = SiaeGroupFactory()
        self.assertEqual(siae.group_count, 0)
        siae.groups.add(group)
        self.assertEqual(siae.groups.count(), 1)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.group_count, 1)

    def test_update_m2m_through_user_count_on_save(self):
        siae = SiaeFactory()
        user = UserFactory()
        self.assertEqual(siae.user_count, 0)
        siae.users.add(user)
        self.assertEqual(siae.users.count(), 1)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.user_count, 1)
        user_2 = UserFactory()
        siaeuser = SiaeUser(siae=siae, user=user_2)
        siaeuser.save()
        self.assertEqual(siae.users.count(), 1 + 1)
        self.assertEqual(siae.user_count, 1 + 1)
        # works also in the opposite direction
        siae_2 = SiaeFactory()
        user_3 = UserFactory()
        user_3.siaes.add(siae_2)
        user_3.siaes.add(siae)
        self.assertEqual(siae.users.count(), 2 + 1)
        # we need to fetch it again
        siae = Siae.objects.get(id=siae.id)
        self.assertEqual(siae.user_count, 2 + 1)
        # works with set()
        siae_3 = SiaeFactory()
        self.assertEqual(siae_3.users.count(), 0)
        self.assertEqual(siae_3.user_count, 0)
        siae_3.users.set([user, user_2, user_3])
        self.assertEqual(siae_3.users.count(), 3)
        self.assertEqual(siae_3.user_count, 3)
        # TODO: but not in the opposite direction

    def test_update_content_fill_date_on_save(self):
        # siae to update
        siae = SiaeFactory(description="")
        user = UserFactory()
        siae.users.add(user)
        sector = SectorFactory()
        siae.sectors.add(sector)
        self.assertEqual(siae.content_filled_basic_date, None)
        siae.description = "test"
        siae.save()
        self.assertNotEqual(siae.content_filled_basic_date, None)
        # siae should be skipped now
        fill_date = siae.content_filled_basic_date
        siae.description = "another test"
        siae.save()
        self.assertEqual(siae.content_filled_basic_date, fill_date)

    def test_update_signup_date_on_save(self):
        siae = SiaeFactory()
        user = UserFactory()
        self.assertEqual(siae.signup_date, None)
        siae.users.add(user)
        self.assertEqual(siae.users.count(), 1)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.user_count, 1)
        self.assertNotEqual(siae.signup_date, None)
        # siae should be skipped now
        user_2 = UserFactory()
        signup_date = siae.signup_date
        siae.users.add(user_2)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.signup_date, signup_date)

    def test_update_last_updated_fields(self):
        siae = SiaeFactory()
        self.assertEqual(siae.employees_insertion_count, None)
        self.assertEqual(siae.employees_insertion_count_last_updated, None)
        # new value: last_updated field will be set
        siae = Siae.objects.get(id=siae.id)  # we need to fetch it again to pass through the __init__
        siae.employees_insertion_count = 10
        siae.save()
        self.assertEqual(siae.employees_insertion_count, 10)
        self.assertNotEqual(siae.employees_insertion_count_last_updated, None)
        employees_insertion_count_last_updated = siae.employees_insertion_count_last_updated
        # same value: last_updated field will not be updated
        siae = Siae.objects.get(id=siae.id)
        siae.employees_insertion_count = 10
        siae.save()
        self.assertEqual(siae.employees_insertion_count, 10)
        self.assertEqual(siae.employees_insertion_count_last_updated, employees_insertion_count_last_updated)
        # updated value: last_updated field will be updated
        siae = Siae.objects.get(id=siae.id)
        siae.employees_insertion_count = 15
        siae.save()
        self.assertEqual(siae.employees_insertion_count, 15)
        self.assertNotEqual(siae.employees_insertion_count_last_updated, employees_insertion_count_last_updated)

    # this test needs to call an outside API to work...
    # def test_update_address_coords_field(self):
    #     siae = SiaeFactory(address="", post_code="", city="", department="", region="")
    #     self.assertEqual(siae.address, "")
    #     self.assertEqual(siae.coords, None)
    #     siae.address = "20 Avenue de Segur"
    #     siae.city = "Paris"
    #     siae.save()
    #     siae = Siae.objects.get(id=siae.id)  # we need to fetch it again to make sure
    #     self.assertNotEqual(siae.coords, None)


class SiaeModelQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_is_live_queryset(self):
        SiaeFactory(is_active=True, is_delisted=True)
        SiaeFactory(is_active=False, is_delisted=True)
        SiaeFactory(is_active=True, is_delisted=False)  # live
        SiaeFactory(is_active=False, is_delisted=False)
        self.assertEqual(Siae.objects.count(), 4)
        self.assertEqual(Siae.objects.is_live().count(), 1)
        self.assertEqual(Siae.objects.is_not_live().count(), 3)

    def test_has_user_queryset(self):
        SiaeFactory()
        siae = SiaeFactory()
        user = UserFactory()
        siae.users.add(user)
        self.assertEqual(Siae.objects.count(), 2)
        self.assertEqual(Siae.objects.has_user().count(), 1)

    # def test_annotate_with_user_favorite_list_ids(self):
    # see favorites > tests.py

    # def test_with_tender_stats(self):
    # see tenders > tests.py > TenderModelQuerysetStatsTest

    def test_annotate_with_brand_or_name(self):
        siae_1 = SiaeFactory(name="ZZZ", brand="ABC")
        siae_2 = SiaeFactory(name="Test", brand="")
        siae_queryset = Siae.objects.annotate_with_brand_or_name()
        self.assertEqual(siae_queryset.get(id=siae_1.id).brand_or_name, siae_1.brand)
        self.assertEqual(siae_queryset.get(id=siae_2.id).brand_or_name, siae_2.name)
        self.assertEqual(siae_queryset.first(), siae_2)  # default order is by "name"
        siae_queryset_with_order_by = Siae.objects.annotate_with_brand_or_name().order_by("brand_or_name")
        self.assertEqual(siae_queryset_with_order_by.first(), siae_1)
        siae_queryset_with_order_by_parameter = Siae.objects.annotate_with_brand_or_name(with_order_by=True)
        self.assertEqual(siae_queryset_with_order_by_parameter.first(), siae_1)

    def test_with_content_filled_stats(self):
        siae_empty = SiaeFactory(name="Empty")
        siae_filled_basic = SiaeFactory(name="Filled basic", user_count=1, sector_count=2, description="desc")
        siae_queryset = Siae.objects.with_content_filled_stats()
        self.assertEqual(siae_queryset.get(id=siae_empty.id).content_filled_basic, False)
        self.assertEqual(siae_queryset.get(id=siae_filled_basic.id).content_filled_basic, True)

    def test_with_employees_count(self):
        siae_1 = SiaeFactory()
        siae_2 = SiaeFactory(employees_insertion_count=10)
        siae_3 = SiaeFactory(c2_etp_count=19.5)
        siae_4 = SiaeFactory(employees_permanent_count=155)
        siae_5 = SiaeFactory(employees_insertion_count=22, c2_etp_count=55)
        siae_6 = SiaeFactory(employees_insertion_count=280, employees_permanent_count=105)
        siae_7 = SiaeFactory(c2_etp_count=2550, employees_permanent_count=1500)
        siae_8 = SiaeFactory(employees_insertion_count=125, c2_etp_count=158, employees_permanent_count=88)

        siae_queryset = Siae.objects.with_employees_count()
        self.assertEqual(siae_queryset.get(id=siae_1.id).employees_insertion_count_with_c2_etp, None)
        self.assertEqual(siae_queryset.get(id=siae_1.id).employees_count, None)

        self.assertEqual(siae_queryset.get(id=siae_2.id).employees_insertion_count_with_c2_etp, 10)
        self.assertEqual(siae_queryset.get(id=siae_2.id).employees_count, 10)

        self.assertEqual(siae_queryset.get(id=siae_3.id).employees_insertion_count_with_c2_etp, 20)
        self.assertEqual(siae_queryset.get(id=siae_3.id).employees_count, 20)

        self.assertEqual(siae_queryset.get(id=siae_4.id).employees_insertion_count_with_c2_etp, None)
        self.assertEqual(siae_queryset.get(id=siae_4.id).employees_count, 155)

        self.assertEqual(siae_queryset.get(id=siae_5.id).employees_insertion_count_with_c2_etp, 22)
        self.assertEqual(siae_queryset.get(id=siae_5.id).employees_count, 22)

        self.assertEqual(siae_queryset.get(id=siae_6.id).employees_insertion_count_with_c2_etp, 280)
        self.assertEqual(siae_queryset.get(id=siae_6.id).employees_count, 280 + 105)

        self.assertEqual(siae_queryset.get(id=siae_7.id).employees_insertion_count_with_c2_etp, 2550)
        self.assertEqual(siae_queryset.get(id=siae_7.id).employees_count, 2550 + 1500)

        self.assertEqual(siae_queryset.get(id=siae_8.id).employees_insertion_count_with_c2_etp, 125)
        self.assertEqual(siae_queryset.get(id=siae_8.id).employees_count, 125 + 88)


class SiaeModelPerimeterQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.auvergne_rhone_alpes_perimeter = PerimeterFactory(
            name="Auvergne-Rhône-Alpes", kind=Perimeter.KIND_REGION, insee_code="R84"
        )
        cls.guadeloupe_perimeter = PerimeterFactory(name="Guadeloupe", kind=Perimeter.KIND_REGION, insee_code="R01")
        cls.finistere_perimeter = PerimeterFactory(
            name="Finistère", kind=Perimeter.KIND_DEPARTMENT, insee_code="29", region_code="53"
        )
        cls.grenoble_perimeter = PerimeterFactory(
            name="Grenoble",
            kind=Perimeter.KIND_CITY,
            insee_code="38185",
            department_code="38",
            region_code="84",
            post_codes=["38000", "38100", "38700"],
            # coords=Point(5.7301, 45.1825),
        )
        cls.chamrousse_perimeter = PerimeterFactory(
            name="Chamrousse",
            kind=Perimeter.KIND_CITY,
            insee_code="38567",
            department_code="38",
            region_code="84",
            post_codes=["38410"],
            # coords=Point(5.8862, 45.1106),
        )
        SiaeFactory()
        SiaeFactory(region="Guadeloupe")
        SiaeFactory(region="Bretagne", department="29")
        SiaeFactory(
            city=cls.grenoble_perimeter.name,
            department=cls.grenoble_perimeter.department_code,
            region=cls.auvergne_rhone_alpes_perimeter.name,
            post_code=cls.grenoble_perimeter.post_codes[0],
        )
        SiaeFactory(
            city=cls.chamrousse_perimeter.name,
            department=cls.chamrousse_perimeter.department_code,
            region=cls.auvergne_rhone_alpes_perimeter.name,
            post_code=cls.chamrousse_perimeter.post_codes[0],
            geo_range=siae_constants.GEO_RANGE_DEPARTMENT,
        )

    def test_address_in_perimeter_list(self):
        self.assertEqual(Siae.objects.address_in_perimeter_list([]).count(), 5)
        self.assertEqual(Siae.objects.address_in_perimeter_list([self.guadeloupe_perimeter]).count(), 1)
        self.assertEqual(Siae.objects.address_in_perimeter_list([self.grenoble_perimeter]).count(), 1)
        self.assertEqual(
            Siae.objects.address_in_perimeter_list([self.guadeloupe_perimeter, self.finistere_perimeter]).count(), 2
        )

    def test_geo_range_in_perimeter_list(self):
        self.assertEqual(Siae.objects.geo_range_in_perimeter_list([]).count(), 5)
        self.assertEqual(Siae.objects.geo_range_in_perimeter_list([self.guadeloupe_perimeter]).count(), 1)
        self.assertEqual(Siae.objects.geo_range_in_perimeter_list([self.grenoble_perimeter]).count(), 2)
        self.assertEqual(
            Siae.objects.geo_range_in_perimeter_list([self.guadeloupe_perimeter, self.finistere_perimeter]).count(), 2
        )


class SiaeLabelModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.label_1 = LabelFactory()
        cls.label_2 = LabelFactory()

    def test_siae_labels(self):
        siae = SiaeFactory()
        siae.labels.add(self.label_1)
        self.assertEqual(siae.labels.count(), 1)

    def test_siae_labels_through(self):
        siae = SiaeFactory()
        SiaeLabel.objects.create(siae=siae, label=self.label_2)
        self.assertEqual(siae.labels.count(), 1)
