from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from lemarche.labels.factories import LabelFactory
from lemarche.networks.factories import NetworkFactory
from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory
from lemarche.siaes import constants as siae_constants, utils as siae_utils
from lemarche.siaes.factories import (
    SiaeActivityFactory,
    SiaeClientReferenceFactory,
    SiaeFactory,
    SiaeGroupFactory,
    SiaeImageFactory,
    SiaeLabelOldFactory,
    SiaeOfferFactory,
)
from lemarche.siaes.models import Siae, SiaeGroup, SiaeLabel, SiaeUser
from lemarche.users.factories import UserFactory
from lemarche.utils.history import HISTORY_TYPE_CREATE, HISTORY_TYPE_UPDATE


PERIMETER_GRENOBLE = {
    "name": "Grenoble",
    "kind": Perimeter.KIND_CITY,
    "insee_code": "38185",
    "department_code": "38",
    "region_code": "84",
    "post_codes": ["38000", "38100", "38700"],
    # coords=Point(5.7301, 45.1825),
}


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
        self.assertIsNone(siae_group.employees_insertion_count)
        self.assertIsNone(siae_group.employees_insertion_count_last_updated)
        # new value: last_updated field will be set
        siae_group = SiaeGroup.objects.get(id=siae_group.id)  # we need to fetch it again to pass through the __init__
        siae_group.employees_insertion_count = 10
        siae_group.save()
        self.assertEqual(siae_group.employees_insertion_count, 10)
        self.assertIsNotNone(siae_group.employees_insertion_count_last_updated)
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


class SiaeGroupQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_1 = SiaeFactory()
        cls.siae_2 = SiaeFactory(is_active=False)
        cls.siae_group = SiaeGroupFactory()
        cls.siae_group_with_siaes = SiaeGroupFactory(siaes=[cls.siae_1, cls.siae_2])

    def test_with_siae_stats(self):
        siae_group_queryset = SiaeGroup.objects.with_siae_stats()
        self.assertEqual(siae_group_queryset.get(id=self.siae_group.id).siae_count_annotated, 0)
        self.assertEqual(siae_group_queryset.get(id=self.siae_group_with_siaes.id).siae_count_annotated, 2)


class SiaeModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_ei = SiaeFactory(kind=siae_constants.KIND_EI)
        cls.siae_ea = SiaeFactory(kind=siae_constants.KIND_EA)
        cls.siae_eatt = SiaeFactory(kind=siae_constants.KIND_EATT)
        cls.siae_esat = SiaeFactory(kind=siae_constants.KIND_ESAT)

    def test_str(self):
        siae = SiaeFactory(name="Ma boite")
        self.assertEqual(str(siae), "Ma boite")

    def test_is_live(self):
        siae_live = SiaeFactory(is_active=True, is_delisted=False)
        siae_not_live_1 = SiaeFactory(is_active=True, is_delisted=True)
        siae_not_live_2 = SiaeFactory(is_active=False, is_delisted=False)
        siae_not_live_3 = SiaeFactory(is_active=False, is_delisted=True)
        self.assertTrue(siae_live.is_live)
        for s in [siae_not_live_1, siae_not_live_2, siae_not_live_3]:
            self.assertFalse(s.is_live)

    def test_name_display_property(self):
        siae_without_brand = SiaeFactory(name="Ma raison sociale")
        siae_with_brand = SiaeFactory(name="Ma raison sociale", brand="Mon enseigne")
        self.assertEqual(siae_without_brand.name_display, "Ma raison sociale")
        self.assertEqual(siae_with_brand.name_display, "Mon enseigne")

    def test_kind_display(self):
        self.assertEqual(self.siae_ei.get_kind_display(), "Entreprise d'insertion (EI)")
        self.assertEqual(self.siae_eatt.get_kind_display(), "Entreprise adaptée de travail temporaire (EATT)")

    def test_siret_siren_nic_properties(self):
        # siret_display
        siae_with_siret = SiaeFactory(siret="12312312312345")
        self.assertEqual(siae_with_siret.siret_display, "123 123 123 12345")
        siae_with_siren = SiaeFactory(siret="123123123")
        self.assertEqual(siae_with_siren.siret_display, "123 123 123")
        siae_with_anormal_siret = SiaeFactory(siret="123123123123")
        self.assertEqual(siae_with_anormal_siret.siret_display, "123123123123")
        # siren
        self.assertEqual(siae_with_siret.siren, "123123123")
        # nic
        self.assertEqual(siae_with_siret.nic, "12345")

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
        score_completion_before = siae_missing.completion_rate_calculated
        self.assertTrue(siae_missing.is_missing_content)
        siae_full: Siae = SiaeFactory(
            name="Ma boite",
            contact_website="https://example.com",
            contact_email="email@example.com",
            contact_phone="0000000000",
            description="test",
        )
        self.assertTrue(score_completion_before < siae_full.completion_rate_calculated)
        score_completion_before = siae_full.completion_rate_calculated
        SiaeActivityFactory(siae=siae_full)
        SiaeOfferFactory(siae=siae_full)
        SiaeLabelOldFactory(siae=siae_full)
        siae_full.save()  # to update stats
        self.assertFalse(siae_full.is_missing_content)
        self.assertTrue(score_completion_before < siae_full.completion_rate_calculated)

        siae_full_2: Siae = SiaeFactory(
            name="Ma boite",
            contact_website="https://example.com",
            # contact_email="email@example.com",
            # contact_phone="0000000000",
            description="test",
        )
        SiaeActivityFactory(siae=siae_full_2)
        SiaeOfferFactory(siae=siae_full_2)
        SiaeLabelOldFactory(siae=siae_full_2)
        siae_full_2.save()  # to update stats
        self.assertFalse(siae_full_2.is_missing_content)

    def test_kind_is_esat_or_ea_or_eatt_property(self):
        for siae in [self.siae_esat, self.siae_ea, self.siae_eatt]:
            self.assertTrue(siae.kind_is_esat_or_ea_or_eatt)
        self.assertFalse(self.siae_ei.kind_is_esat_or_ea_or_eatt)

    def test_kind_parent_property(self):
        self.assertEqual(self.siae_ei.kind_parent, "Insertion")
        self.assertEqual(self.siae_esat.kind_parent, "Handicap")

    def test_super_badge_computed_property(self):
        siae_1 = SiaeFactory(user_count=0)
        siae_2 = SiaeFactory(user_count=1, completion_rate=50)
        siae_3 = SiaeFactory(
            user_count=1, completion_rate=80, tender_email_send_count=10, tender_email_link_click_count=3
        )
        siae_4 = SiaeFactory(
            user_count=1,
            completion_rate=80,
            tender_email_send_count=10,
            tender_email_link_click_count=3,
            tender_detail_contact_click_count=1,
        )
        siae_super_badge_1 = SiaeFactory(
            user_count=1,
            completion_rate=80,
            tender_email_send_count=10,
            tender_email_link_click_count=4,
            tender_detail_contact_click_count=1,
        )
        siae_super_badge_2 = SiaeFactory(
            user_count=1,
            completion_rate=80,
            tender_email_send_count=10,
            tender_email_link_click_count=3,
            tender_detail_contact_click_count=3,
        )
        for siae in [siae_1, siae_2, siae_3, siae_4]:
            self.assertFalse(siae.super_badge_calculated)
        for siae in [siae_super_badge_1, siae_super_badge_2]:
            self.assertTrue(siae.super_badge_calculated)


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

    def test_update_o2m_sector_count_on_save(self):
        siae = SiaeFactory()
        self.assertEqual(siae.sector_count, 0)
        SiaeActivityFactory(siae=siae)
        self.assertEqual(siae.activities.count(), 1)
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
        SiaeActivityFactory(siae=siae)
        self.assertIsNone(siae.content_filled_basic_date)
        siae.description = "test"
        siae.save()
        self.assertIsNotNone(siae.content_filled_basic_date)
        # siae should be skipped now
        fill_date = siae.content_filled_basic_date
        siae.description = "another test"
        siae.save()
        self.assertEqual(siae.content_filled_basic_date, fill_date)

    def test_update_signup_date_on_save(self):
        siae = SiaeFactory()
        user = UserFactory()
        self.assertIsNone(siae.signup_date)
        siae.users.add(user)
        self.assertEqual(siae.users.count(), 1)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.user_count, 1)
        self.assertIsNotNone(siae.signup_date)
        # siae should be skipped now
        user_2 = UserFactory()
        signup_date = siae.signup_date
        siae.users.add(user_2)
        # siae.save()  # no need to run save(), m2m_changed signal was triggered above
        self.assertEqual(siae.signup_date, signup_date)

    def test_update_last_updated_fields(self):
        siae = SiaeFactory()
        self.assertIsNone(siae.employees_insertion_count)
        self.assertIsNone(siae.employees_insertion_count_last_updated)
        # new value: last_updated field will be set
        siae = Siae.objects.get(id=siae.id)  # we need to fetch it again to pass through the __init__
        siae.employees_insertion_count = 10
        siae.save()
        self.assertEqual(siae.employees_insertion_count, 10)
        self.assertIsNotNone(siae.employees_insertion_count_last_updated)
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
    #     self.assertIsNone(siae.coords)
    #     siae.address = "20 Avenue de Segur"
    #     siae.city = "Paris"
    #     siae.save()
    #     siae = Siae.objects.get(id=siae.id)  # we need to fetch it again to make sure
    #     self.assertIsNotNone(siae.coords)

    def test_set_super_badge(self):
        # None -> True
        siae_super_badge_1 = SiaeFactory(
            user_count=1,
            completion_rate=80,
            tender_email_send_count=10,
            tender_email_link_click_count=4,
            tender_detail_contact_click_count=1,
        )
        self.assertIsNone(siae_super_badge_1.super_badge)
        self.assertIsNone(siae_super_badge_1.super_badge_last_updated)
        siae_super_badge_1.set_super_badge()
        self.assertTrue(siae_super_badge_1.super_badge)
        self.assertIsNotNone(siae_super_badge_1.super_badge_last_updated)
        # True -> True
        siae_super_badge_2 = SiaeFactory(
            user_count=1,
            completion_rate=80,
            tender_email_send_count=10,
            tender_email_link_click_count=3,
            tender_detail_contact_click_count=3,
            super_badge=True,
            super_badge_last_updated=timezone.now(),
        )
        self.assertTrue(siae_super_badge_2.super_badge)
        self.assertIsNotNone(siae_super_badge_2.super_badge_last_updated)
        siae_super_badge_last_updated_current_value = siae_super_badge_2.super_badge_last_updated
        siae_super_badge_2.set_super_badge()
        self.assertTrue(siae_super_badge_2.super_badge)
        self.assertEqual(siae_super_badge_2.super_badge_last_updated, siae_super_badge_last_updated_current_value)

    def test_brand_uniqueness(self):
        SiaeFactory(name="Name 1", brand="Brand 1")
        SiaeFactory(brand="Brand 2")
        siae_3 = SiaeFactory(brand="Brand 1")
        self.assertEqual(Siae.objects.filter(brand="Brand 1").count(), 2)

        # can update something else than brand
        siae_3.contact_first_name = "Contact 1"
        siae_3.clean()
        siae_3.save()

        self.assertEqual(Siae.objects.filter(brand="Brand 1").count(), 2)
        siae_3.refresh_from_db()
        self.assertEqual(siae_3.contact_first_name, "Contact 1")

        # can't update brand to an existing brand
        siae_3.brand = "Brand 2"
        with self.assertRaises(ValidationError):
            siae_3.clean()
            siae_3.save()
        self.assertEqual(Siae.objects.filter(brand="Brand 1").count(), 2)

        # can't update brand to an existing name
        siae_3.brand = "Name 1"
        with self.assertRaises(ValidationError):
            siae_3.clean()
            siae_3.save()

        siae_3.refresh_from_db()
        self.assertEqual(siae_3.brand, "Brand 1")

        # can update brand to a non existing brand
        siae_3.brand = "Brand 3"
        siae_3.name = "Name 3"
        siae_3.clean()
        siae_3.save()
        siae_3.refresh_from_db()
        self.assertEqual(siae_3.brand, "Brand 3")


class SiaeModelQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_is_live_queryset(self):
        SiaeFactory(is_active=True, is_delisted=False)  # live
        SiaeFactory(is_active=True, is_delisted=True)
        SiaeFactory(is_active=False, is_delisted=False)
        SiaeFactory(is_active=False, is_delisted=True)
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

    # def test_with_in_user_favorite_list_stats(self):
    # see favorites > tests.py

    # def test_with_tender_stats(self):
    # see tenders > tests.py > TenderModelQuerysetStatsTest

    def test_with_brand_or_name(self):
        siae_1 = SiaeFactory(name="ZZZ", brand="ABC")
        siae_2 = SiaeFactory(name="Test", brand="")
        siae_queryset = Siae.objects.with_brand_or_name()
        self.assertEqual(siae_queryset.get(id=siae_1.id).brand_or_name_annotated, siae_1.brand)
        self.assertEqual(siae_queryset.get(id=siae_2.id).brand_or_name_annotated, siae_2.name)
        self.assertEqual(siae_queryset.first(), siae_2)  # default order is by "name"
        siae_queryset_with_order_by = Siae.objects.with_brand_or_name().order_by("brand_or_name_annotated")
        self.assertEqual(siae_queryset_with_order_by.first(), siae_1)
        siae_queryset_with_order_by_parameter = Siae.objects.with_brand_or_name(with_order_by=True)
        self.assertEqual(siae_queryset_with_order_by_parameter.first(), siae_1)

    def test_with_content_filled_stats(self):
        siae_empty = SiaeFactory(name="Empty")
        siae_filled_basic = SiaeFactory(name="Filled basic", user_count=1, sector_count=1, description="desc")
        siae_filled_full = SiaeFactory(
            name="Filled full", user_count=1, sector_count=1, description="desc", logo_url="https://logo.png"
        )
        SiaeClientReferenceFactory(siae=siae_filled_full)
        SiaeImageFactory(siae=siae_filled_full)
        SiaeLabelOldFactory(siae=siae_filled_full)
        siae_filled_full.save()
        siae_queryset = Siae.objects.with_content_filled_stats()
        self.assertFalse(siae_queryset.get(id=siae_empty.id).content_filled_basic_annotated)
        self.assertFalse(siae_queryset.get(id=siae_empty.id).content_filled_full_annotated)
        self.assertTrue(siae_queryset.get(id=siae_filled_basic.id).content_filled_basic_annotated)
        self.assertFalse(siae_queryset.get(id=siae_filled_basic.id).content_filled_full_annotated)
        self.assertTrue(siae_queryset.get(id=siae_filled_full.id).content_filled_basic_annotated)
        self.assertTrue(siae_queryset.get(id=siae_filled_full.id).content_filled_full_annotated)

    def test_with_employees_stats(self):
        siae_1 = SiaeFactory()
        siae_2 = SiaeFactory(employees_insertion_count=10)
        siae_3 = SiaeFactory(c2_etp_count=19.5)
        siae_4 = SiaeFactory(employees_permanent_count=155)
        siae_5 = SiaeFactory(employees_insertion_count=22, c2_etp_count=55)
        siae_6 = SiaeFactory(employees_insertion_count=280, employees_permanent_count=105)
        siae_7 = SiaeFactory(c2_etp_count=2550, employees_permanent_count=1500)
        siae_8 = SiaeFactory(employees_insertion_count=125, c2_etp_count=158, employees_permanent_count=88)

        siae_queryset = Siae.objects.with_employees_stats()
        self.assertIsNone(siae_queryset.get(id=siae_1.id).employees_insertion_count_with_c2_etp_annotated)
        self.assertIsNone(siae_queryset.get(id=siae_1.id).employees_count_annotated)

        self.assertEqual(siae_queryset.get(id=siae_2.id).employees_insertion_count_with_c2_etp_annotated, 10)
        self.assertEqual(siae_queryset.get(id=siae_2.id).employees_count_annotated, 10)

        self.assertEqual(siae_queryset.get(id=siae_3.id).employees_insertion_count_with_c2_etp_annotated, 20)
        self.assertEqual(siae_queryset.get(id=siae_3.id).employees_count_annotated, 20)

        self.assertIsNone(siae_queryset.get(id=siae_4.id).employees_insertion_count_with_c2_etp_annotated)
        self.assertEqual(siae_queryset.get(id=siae_4.id).employees_count_annotated, 155)

        self.assertEqual(siae_queryset.get(id=siae_5.id).employees_insertion_count_with_c2_etp_annotated, 22)
        self.assertEqual(siae_queryset.get(id=siae_5.id).employees_count_annotated, 22)

        self.assertEqual(siae_queryset.get(id=siae_6.id).employees_insertion_count_with_c2_etp_annotated, 280)
        self.assertEqual(siae_queryset.get(id=siae_6.id).employees_count_annotated, 280 + 105)

        self.assertEqual(siae_queryset.get(id=siae_7.id).employees_insertion_count_with_c2_etp_annotated, 2550)
        self.assertEqual(siae_queryset.get(id=siae_7.id).employees_count_annotated, 2550 + 1500)

        self.assertEqual(siae_queryset.get(id=siae_8.id).employees_insertion_count_with_c2_etp_annotated, 125)
        self.assertEqual(siae_queryset.get(id=siae_8.id).employees_count_annotated, 125 + 88)


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
        cls.grenoble_perimeter = PerimeterFactory(**PERIMETER_GRENOBLE)
        cls.chamrousse_perimeter = PerimeterFactory(
            name="Chamrousse",
            kind=Perimeter.KIND_CITY,
            insee_code="38567",
            department_code="38",
            region_code="84",
            post_codes=["38410"],
            # coords=Point(5.8862, 45.1106),
        )
        SiaeFactory(city="Tours", department="37", region="Centre-Val de Loire", post_code="37000")
        SiaeFactory(city="Pointe-à-Pitre", department="971", region="Guadeloupe", post_code="97110")
        SiaeFactory(city="Brest", department="29", region="Bretagne", post_code="29200")
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
        )

    def test_address_in_perimeter_list(self):
        self.assertEqual(Siae.objects.address_in_perimeter_list([]).count(), 5)
        self.assertEqual(Siae.objects.address_in_perimeter_list([self.guadeloupe_perimeter]).count(), 1)
        self.assertEqual(Siae.objects.address_in_perimeter_list([self.grenoble_perimeter]).count(), 1)
        self.assertEqual(
            Siae.objects.address_in_perimeter_list([self.guadeloupe_perimeter, self.finistere_perimeter]).count(), 2
        )


class SiaeHistoryTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae_1 = SiaeFactory(name="ZZZ", brand="ABC")
        cls.siae_2 = SiaeFactory(name="Test", brand="")

    def test_history_object_on_create(self):
        self.assertEqual(self.siae_1.history.count(), 1)
        siae_1_create_history_item = self.siae_1.history.last()
        self.assertEqual(siae_1_create_history_item.history_type, HISTORY_TYPE_CREATE)
        self.assertEqual(siae_1_create_history_item.name, self.siae_1.name)

    def test_history_object_on_update(self):
        self.siae_2.brand = "test"
        self.siae_2.save()
        self.assertEqual(self.siae_2.history.count(), 1 + 1)
        siae_2_create_history_item = self.siae_2.history.last()
        self.assertEqual(siae_2_create_history_item.history_type, HISTORY_TYPE_CREATE)
        self.assertEqual(siae_2_create_history_item.brand, "")
        siae_2_update_history_item = self.siae_2.history.first()
        self.assertEqual(siae_2_update_history_item.history_type, HISTORY_TYPE_UPDATE)
        self.assertEqual(siae_2_update_history_item.brand, self.siae_2.brand)


class SiaeLabelModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.label_1 = LabelFactory(name="Un label")
        cls.label_2 = LabelFactory(name="Un autre label")

    def test_siae_labels(self):
        siae = SiaeFactory()
        siae.labels.add(self.label_1)
        self.assertEqual(siae.labels.count(), 1)

    def test_siae_labels_through(self):
        siae = SiaeFactory()
        SiaeLabel.objects.create(siae=siae, label=self.label_2)
        self.assertEqual(siae.labels.count(), 1)


class SiaeUtilsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_calculate_etablissement_count(self):
        self.siae_with_siret_1 = SiaeFactory(siret="12312312312345", is_active=True)
        self.siae_with_siret_2 = SiaeFactory(siret="12312312312346", is_active=True)
        self.siae_with_siret_inactive = SiaeFactory(siret="12312312312347", is_active=False)
        self.assertEqual(siae_utils.calculate_etablissement_count(self.siae_with_siret_1), 2)


class SiaeActivitiesTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        # cls.users = [UserFactory() for i in range(3)]
        cls.siae: Siae = SiaeFactory(siret="12312312312345", is_active=True)

    def test_last_activity_is_updated_at(self):
        self.assertEqual(self.siae.updated_at, self.siae.latest_activity_at)
        users = [UserFactory() for i in range(3)]
        self.siae.users.set(users)
        users[0].first_name = "test"
        users[0].save()
        self.assertNotEqual(self.siae.updated_at, self.siae.latest_activity_at)
        self.assertTrue(self.siae.updated_at < self.siae.latest_activity_at)
        self.siae.name = "test_siae"
        self.siae.save()
        self.assertTrue(self.siae.updated_at == self.siae.latest_activity_at)


class SiaeFilterWithPotentialThroughActivitiesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sector_1 = SectorFactory()
        cls.sector_2 = SectorFactory()
        cls.perimeter_1 = PerimeterFactory(
            name="Paris", kind=Perimeter.KIND_DEPARTMENT, insee_code="75", region_code="11"
        )
        cls.perimeter_2 = PerimeterFactory(
            name="Indre-et-Loire", kind=Perimeter.KIND_DEPARTMENT, insee_code="37", region_code="24"
        )

        cls.siae_1 = SiaeFactory()
        cls.siae_2 = SiaeFactory()
        cls.siae_3 = SiaeFactory()

        cls.siae_activity_1 = SiaeActivityFactory(
            siae=cls.siae_1,
            sector=cls.sector_1,
            presta_type=[siae_constants.PRESTA_BUILD],
            with_zones_perimeter=True,
        )
        cls.siae_activity_1.locations.set([cls.perimeter_1])

        cls.siae_activity_2 = SiaeActivityFactory(
            siae=cls.siae_2,
            sector=cls.sector_2,
            presta_type=[siae_constants.PRESTA_BUILD],
            with_zones_perimeter=True,
        )
        cls.siae_activity_2.locations.set([cls.perimeter_2])

        cls.siae_activity_3 = SiaeActivityFactory(
            siae=cls.siae_3,
            sector=cls.sector_1,
            presta_type=[siae_constants.PRESTA_BUILD],
            with_zones_perimeter=True,
        )
        cls.siae_activity_3.locations.set([cls.perimeter_2])

    def test_filter_with_potential_through_activities_with_sector(self):
        siae_queryset = Siae.objects.filter_with_potential_through_activities(self.sector_1)
        self.assertEqual(siae_queryset.count(), 2)
        self.assertQuerySetEqual(siae_queryset, [self.siae_1, self.siae_3])

    def test_filter_with_potential_through_activities_with_sector_and_perimeter(self):
        siae_queryset = Siae.objects.filter_with_potential_through_activities(self.sector_1, self.perimeter_1)
        self.assertEqual(siae_queryset.count(), 1)
        self.assertQuerySetEqual(siae_queryset, [self.siae_1])

    def test_filter_with_potential_through_activities_with_sector_and_perimeter_2(self):
        siae_queryset = Siae.objects.filter_with_potential_through_activities(self.sector_1, self.perimeter_2)
        self.assertEqual(siae_queryset.count(), 1)
        self.assertQuerySetEqual(siae_queryset, [self.siae_3])
