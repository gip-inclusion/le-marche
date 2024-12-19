from django.test import TestCase
from django.urls import reverse

from lemarche.conversations.factories import TemplateTransactionalFactory
from lemarche.conversations.models import EmailGroup
from lemarche.perimeters.factories import PerimeterFactory
from lemarche.perimeters.models import Perimeter
from lemarche.sectors.factories import SectorFactory, SectorGroupFactory
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.factories import SiaeActivityFactory, SiaeFactory
from lemarche.siaes.models import SiaeUser
from lemarche.users.factories import UserFactory
from lemarche.users.models import User


class DashboardSiaeSearchAdoptViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.user_siae_2 = UserFactory(kind=User.KIND_SIAE)
        cls.user_buyer = UserFactory(kind=User.KIND_BUYER)
        cls.user_partner = UserFactory(kind=User.KIND_PARTNER)
        cls.user_admin = UserFactory(kind=User.KIND_ADMIN)
        cls.siae_with_user = SiaeFactory()
        cls.siae_with_user.users.add(cls.user_siae)
        cls.siae_without_user = SiaeFactory()
        EmailGroup.objects.all().delete()  # to avoid duplicate key error
        TemplateTransactionalFactory(code="SIAEUSERREQUEST_ASSIGNEE")

    def test_anonymous_user_cannot_adopt_siae(self):
        url = reverse("dashboard_siaes:siae_search_by_siret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_only_siae_user_or_admin_can_adopt_siae(self):
        ALLOWED_USERS = [self.user_siae, self.user_admin]
        for user in ALLOWED_USERS:
            self.client.force_login(user)
            url = reverse("dashboard_siaes:siae_search_by_siret")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        NOT_ALLOWED_USERS = [self.user_buyer, self.user_partner]
        for user in NOT_ALLOWED_USERS:
            self.client.force_login(user)
            url = reverse("dashboard_siaes:siae_search_by_siret")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/profil/")

    def test_only_siaes_without_users_can_be_adopted(self):
        self.client.force_login(self.user_siae)

        url = reverse("dashboard_siaes:siae_search_adopt_confirm", args=[self.siae_without_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse("dashboard_siaes:siae_search_adopt_confirm", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profil/")

    def test_only_new_siae_user_can_adopt_confirm(self):
        self.client.force_login(self.user_siae)
        self.assertEqual(self.siae_with_user.users.count(), 1)
        self.assertEqual(self.user_siae.siaes.count(), 1)  # setUpTestData

        url = reverse("dashboard_siaes:siae_search_adopt_confirm", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profil/")

    def test_siae_without_user_adopt_confirm(self):
        self.client.force_login(self.user_siae)
        self.assertEqual(self.siae_without_user.users.count(), 0)
        self.assertEqual(self.user_siae.siaes.count(), 1)  # setUpTestData

        url = reverse("dashboard_siaes:siae_search_adopt_confirm", args=[self.siae_without_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Je confirme")

        url = reverse("dashboard_siaes:siae_search_adopt_confirm", args=[self.siae_without_user.slug])
        response = self.client.post(url)  # data={}
        self.assertEqual(response.status_code, 302)  # redirect to success_url
        self.assertEqual(response.url, f"/profil/prestataires/{self.siae_without_user.slug}/modifier/")
        self.assertEqual(self.siae_without_user.users.count(), 1)
        self.assertEqual(self.user_siae.siaes.count(), 1 + 1)

    def test_siae_with_existing_user_adopt_confirm(self):
        self.client.force_login(self.user_siae_2)
        self.assertEqual(self.siae_with_user.users.count(), 1)
        self.assertEqual(self.user_siae_2.siaes.count(), 0)  # setUpTestData

        url = reverse("dashboard_siaes:siae_search_adopt_confirm", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demander le rattachement")

        url = reverse("dashboard_siaes:siae_search_adopt_confirm", args=[self.siae_with_user.slug])
        response = self.client.post(url)  # data={}
        self.assertEqual(response.status_code, 302)  # redirect to success_url
        self.assertEqual(response.url, "/profil/")
        self.assertEqual(self.siae_with_user.users.count(), 1)  # invitation workflow
        self.assertEqual(self.user_siae_2.siaes.count(), 0)


class DashboardSiaeEditViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.other_user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_user = SiaeFactory()
        cls.siae_with_user.users.add(cls.user_siae)
        cls.siae_without_user = SiaeFactory()

    def test_anonymous_user_cannot_edit_siae(self):
        url = reverse("dashboard_siaes:siae_search_by_siret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_only_siae_user_can_edit_siae(self):
        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/profil/prestataires/{self.siae_with_user.slug}/modifier/contact/")

        self.client.force_login(self.other_user_siae)
        url = reverse("dashboard_siaes:siae_edit", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # self.assertEqual(response.url, "/profil/")  # redirects first to siae_edit_search

    def test_only_siae_user_can_access_siae_edit_tabs(self):
        SIAE_EDIT_URLS = [
            "dashboard_siaes:siae_edit_activities",
            "dashboard_siaes:siae_edit_info",
            "dashboard_siaes:siae_edit_offer",
            "dashboard_siaes:siae_edit_links",
            "dashboard_siaes:siae_edit_contact",
        ]
        self.client.force_login(self.user_siae)
        for siae_edit_url in SIAE_EDIT_URLS:
            with self.subTest(siae_edit_url=siae_edit_url):
                url = reverse(siae_edit_url, args=[self.siae_with_user.slug])
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

        self.client.force_login(self.other_user_siae)
        for siae_edit_url in SIAE_EDIT_URLS:
            with self.subTest(siae_edit_url=siae_edit_url):
                url = reverse(siae_edit_url, args=[self.siae_with_user.slug])
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, "/profil/")

    def test_siae_edit_info_form(self):
        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_info", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "description": "Nouvelle description de l'activité",
            "ca": 1000000,
            "year_constitution": 2024,
            "employees_insertion_count": 10,
            "employees_permanent_count": 5,
            "labels_old-0-name": "Label 1",
            "labels_old-1-name": "Label 2",
            "labels_old-TOTAL_FORMS": 2,
            "labels_old-INITIAL_FORMS": 0,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_siaes:siae_edit_info", args=[self.siae_with_user.slug]))

        # Check that the data has been updated
        self.siae_with_user.refresh_from_db()
        self.assertEqual(self.siae_with_user.name_display, self.siae_with_user.name)
        self.assertEqual(self.siae_with_user.description, "Nouvelle description de l'activité")
        self.assertEqual(self.siae_with_user.ca, 1000000)
        self.assertEqual(self.siae_with_user.year_constitution, 2024)
        self.assertEqual(self.siae_with_user.employees_insertion_count, 10)
        self.assertEqual(self.siae_with_user.employees_permanent_count, 5)

        data["brand"] = "Nouveau nom commercial"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_siaes:siae_edit_info", args=[self.siae_with_user.slug]))
        self.siae_with_user.refresh_from_db()
        self.assertEqual(self.siae_with_user.brand, "Nouveau nom commercial")
        self.assertEqual(self.siae_with_user.name_display, "Nouveau nom commercial")

    def test_siae_edit_info_form_brand_unique(self):
        SiaeFactory(brand="Nouveau nom commercial")

        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_info", args=[self.siae_with_user.slug])

        data = {
            "brand": "Nouveau nom commercial",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ce nom commercial est déjà utilisé par une autre structure.")


class DashboardSiaeUserViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.user_siae_2 = UserFactory(kind=User.KIND_SIAE)
        cls.other_user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_users = SiaeFactory()
        cls.siae_with_users.users.add(cls.user_siae)
        cls.siae_with_users.users.add(cls.user_siae_2)
        cls.siae_without_user = SiaeFactory()

    def test_only_siae_user_can_access_siae_users(self):
        SIAE_USER_URLS = [
            "dashboard_siaes:siae_users",
        ]
        self.client.force_login(self.user_siae)
        for siae_edit_url in SIAE_USER_URLS:
            url = reverse(siae_edit_url, args=[self.siae_with_users.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        self.client.force_login(self.other_user_siae)
        for siae_edit_url in SIAE_USER_URLS:
            url = reverse(siae_edit_url, args=[self.siae_with_users.slug])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/profil/")

    def test_only_siae_user_can_delete_collaborator(self):
        self.assertEqual(self.siae_with_users.users.count(), 2)

        self.client.force_login(self.other_user_siae)
        siaeuser = SiaeUser.objects.get(siae=self.siae_with_users, user=self.user_siae)
        url = reverse("dashboard_siaes:siae_user_delete", args=[self.siae_with_users.slug, siaeuser.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profil/")

        self.client.force_login(self.user_siae)
        siaeuser = SiaeUser.objects.get(siae=self.siae_with_users, user=self.user_siae_2)
        url = reverse("dashboard_siaes:siae_user_delete", args=[self.siae_with_users.slug, siaeuser.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 302)  # 200? normal because redirects to dashboard_siaes:siae_users
        self.assertEqual(response.url, reverse("dashboard_siaes:siae_users", args=[self.siae_with_users.slug]))
        self.assertEqual(self.siae_with_users.users.count(), 1)
        # TODO: user should not be able to delete itself


class DashboardSiaeEditActivitiesViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_user = SiaeFactory()
        cls.siae_with_user.users.add(cls.user_siae)

    def test_only_siae_user_can_access_siae_activities(self):
        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_activities", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ajouter un secteur d'activité")

        self.client.force_login(UserFactory(kind=User.KIND_SIAE))
        url = reverse("dashboard_siaes:siae_edit_activities", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profil/")

    def test_siae_user_can_see_siae_activity_in_list(self):
        siae_activity = SiaeActivityFactory(siae=self.siae_with_user)
        sector = SectorFactory(group=siae_activity.sector_group)
        siae_activity.sectors.add(sector)

        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_activities", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ajouter un secteur d'activité")
        self.assertContains(
            response, reverse("dashboard_siaes:siae_edit_activities_create", args=[self.siae_with_user.slug])
        )

        self.assertContains(response, sector.name)
        self.assertContains(response, siae_activity.presta_type_display)
        self.assertContains(response, siae_activity.geo_range_pretty_display)

        self.assertContains(
            response,
            reverse("dashboard_siaes:siae_edit_activities_edit", args=[self.siae_with_user.slug, siae_activity.id]),
        )


class DashboardSiaeEditActivitiesCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_user = SiaeFactory()
        cls.siae_with_user.users.add(cls.user_siae)

        cls.sector_group = SectorGroupFactory()
        cls.sector1 = SectorFactory(group=cls.sector_group)
        cls.sector2 = SectorFactory(group=cls.sector_group)

    def test_only_siae_user_can_create_siae_activity(self):
        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_activities_create", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.force_login(UserFactory(kind=User.KIND_SIAE))
        url = reverse("dashboard_siaes:siae_edit_activities_create", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:home"))

    def test_siae_user_can_create_siae_activity_with_country_range(self):
        self.assertEqual(self.siae_with_user.activities.count(), 0)
        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_activities_create", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "sector_group": self.sector_group.id,
            "sectors": [self.sector1.id, self.sector2.id],
            "presta_type": [siae_constants.PRESTA_PREST],
            "geo_range": siae_constants.GEO_RANGE_COUNTRY,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("dashboard_siaes:siae_edit_activities", args=[self.siae_with_user.slug])
        )
        self.assertEqual(self.siae_with_user.activities.count(), 1)
        created_activity = self.siae_with_user.activities.first()
        self.assertEqual(created_activity.sector_group, self.sector_group)
        self.assertEqual(created_activity.sectors.count(), 2)
        self.assertIn(self.sector1, created_activity.sectors.all())
        self.assertIn(self.sector2, created_activity.sectors.all())
        self.assertEqual(created_activity.presta_type, [siae_constants.PRESTA_PREST])
        self.assertEqual(created_activity.geo_range, siae_constants.GEO_RANGE_COUNTRY)

    def test_siae_user_can_create_siae_activity_with_custom_range(self):
        self.assertEqual(self.siae_with_user.activities.count(), 0)
        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_activities_create", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "sector_group": self.sector_group.id,
            "sectors": [self.sector1.id],
            "presta_type": [siae_constants.PRESTA_DISP],
            "geo_range": siae_constants.GEO_RANGE_CUSTOM,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Une distance en kilomètres est requise pour cette option.")

        self.assertEqual(self.siae_with_user.activities.count(), 0)

        data["geo_range_custom_distance"] = 10
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("dashboard_siaes:siae_edit_activities", args=[self.siae_with_user.slug])
        )

        self.assertEqual(self.siae_with_user.activities.count(), 1)
        created_activity = self.siae_with_user.activities.first()
        self.assertEqual(created_activity.sector_group, self.sector_group)
        self.assertEqual(created_activity.sectors.count(), 1)
        self.assertEqual(created_activity.sectors.first(), self.sector1)
        self.assertEqual(created_activity.presta_type, [siae_constants.PRESTA_DISP])
        self.assertEqual(created_activity.geo_range, siae_constants.GEO_RANGE_CUSTOM)
        self.assertEqual(created_activity.geo_range_custom_distance, 10)

    def test_siae_user_can_create_siae_activity_with_zones_range(self):
        self.assertEqual(self.siae_with_user.activities.count(), 0)
        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_activities_create", args=[self.siae_with_user.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "sector_group": self.sector_group.id,
            "sectors": [self.sector2.id],
            "presta_type": [siae_constants.PRESTA_BUILD],
            "geo_range": siae_constants.GEO_RANGE_ZONES,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vous devez choisir au moins une zone")
        self.assertEqual(self.siae_with_user.activities.count(), 0)

        perimeter_city = PerimeterFactory(name="Azay-le-rideau", kind=Perimeter.KIND_CITY, insee_code="37190")
        perimeter_department = PerimeterFactory(
            name="Vienne", kind=Perimeter.KIND_DEPARTMENT, insee_code="86", region_code="75"
        )
        perimeter_region = PerimeterFactory(name="Nouvelle-Aquitaine", kind=Perimeter.KIND_REGION, insee_code="R75")

        data["locations"] = [perimeter_city.slug, perimeter_department.slug, perimeter_region.slug]
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("dashboard_siaes:siae_edit_activities", args=[self.siae_with_user.slug])
        )

        self.assertEqual(self.siae_with_user.activities.count(), 1)
        created_activity = self.siae_with_user.activities.first()
        self.assertEqual(created_activity.sector_group, self.sector_group)
        self.assertEqual(created_activity.sectors.count(), 1)
        self.assertEqual(created_activity.sectors.first(), self.sector2)
        self.assertEqual(created_activity.presta_type, [siae_constants.PRESTA_BUILD])
        self.assertEqual(created_activity.geo_range, siae_constants.GEO_RANGE_ZONES)
        self.assertEqual(created_activity.locations.count(), 3)
        self.assertIn(perimeter_city, created_activity.locations.all())
        self.assertIn(perimeter_department, created_activity.locations.all())
        self.assertIn(perimeter_region, created_activity.locations.all())


class DashboardSiaeEditActivitiesEditViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_user = SiaeFactory()
        cls.siae_with_user.users.add(cls.user_siae)

    def test_only_siae_user_can_edit_siae_activity(self):
        siae_activity = SiaeActivityFactory(siae=self.siae_with_user)
        self.assertEqual(self.siae_with_user.activities.count(), 1)

        self.client.force_login(UserFactory(kind=User.KIND_SIAE))
        url = reverse("dashboard_siaes:siae_edit_activities_edit", args=[self.siae_with_user.slug, siae_activity.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:home"))

        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_activities_edit", args=[self.siae_with_user.slug, siae_activity.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_siae_user_can_edit_siae_activity_to_custom_range(self):
        siae_activity = SiaeActivityFactory(
            siae=self.siae_with_user, with_country_perimeter=True, presta_type=[siae_constants.PRESTA_DISP]
        )
        sector_before = SectorFactory(group=siae_activity.sector_group)
        siae_activity.sectors.add(sector_before)
        self.assertEqual(self.siae_with_user.activities.count(), 1)
        self.assertEqual(siae_activity.geo_range, siae_constants.GEO_RANGE_COUNTRY)
        self.assertEqual(siae_activity.sectors.count(), 1)
        self.assertEqual(siae_activity.sectors.first(), sector_before)

        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_activities_edit", args=[self.siae_with_user.slug, siae_activity.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        sector_after = SectorFactory()
        data = {
            "sector_group": sector_after.group.id,
            "sectors": [sector_after.id],
            "presta_type": [siae_constants.PRESTA_BUILD],
            "geo_range": siae_constants.GEO_RANGE_CUSTOM,
            "geo_range_custom_distance": 42,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("dashboard_siaes:siae_edit_activities", args=[self.siae_with_user.slug])
        )
        self.assertEqual(self.siae_with_user.activities.count(), 1)
        updated_activity = self.siae_with_user.activities.first()
        self.assertEqual(updated_activity.sector_group, sector_after.group)
        self.assertEqual(updated_activity.sectors.count(), 1)
        self.assertEqual(updated_activity.sectors.first(), sector_after)
        self.assertEqual(updated_activity.presta_type, [siae_constants.PRESTA_BUILD])
        self.assertEqual(updated_activity.geo_range, siae_constants.GEO_RANGE_CUSTOM)

    def test_siae_user_can_edit_siae_activity_to_zones(self):
        siae_activity = SiaeActivityFactory(
            siae=self.siae_with_user, with_custom_distance_perimeter=True, presta_type=[siae_constants.PRESTA_DISP]
        )
        sector_before = SectorFactory(group=siae_activity.sector_group)
        siae_activity.sectors.add(sector_before)
        self.assertEqual(self.siae_with_user.activities.count(), 1)
        self.assertEqual(siae_activity.geo_range, siae_constants.GEO_RANGE_CUSTOM)
        self.assertIsNotNone(siae_activity.geo_range_custom_distance)
        self.assertEqual(siae_activity.sectors.count(), 1)
        self.assertEqual(siae_activity.sectors.first(), sector_before)
        self.assertEqual(siae_activity.locations.count(), 0)

        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_activities_edit", args=[self.siae_with_user.slug, siae_activity.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        sector_after = SectorFactory()
        perimeter_city = PerimeterFactory(name="Azay-le-rideau", kind=Perimeter.KIND_CITY, insee_code="37190")
        perimeter_department = PerimeterFactory(
            name="Vienne", kind=Perimeter.KIND_DEPARTMENT, insee_code="86", region_code="75"
        )
        data = {
            "sector_group": sector_after.group.id,
            "sectors": [sector_after.id],
            "presta_type": [siae_constants.PRESTA_BUILD],
            "geo_range": siae_constants.GEO_RANGE_ZONES,
            "locations": [perimeter_city.slug, perimeter_department.slug],
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("dashboard_siaes:siae_edit_activities", args=[self.siae_with_user.slug])
        )
        self.assertEqual(self.siae_with_user.activities.count(), 1)
        updated_activity = self.siae_with_user.activities.first()
        self.assertEqual(updated_activity.sector_group, sector_after.group)
        self.assertEqual(updated_activity.sectors.count(), 1)
        self.assertEqual(updated_activity.sectors.first(), sector_after)
        self.assertEqual(updated_activity.presta_type, [siae_constants.PRESTA_BUILD])
        self.assertEqual(updated_activity.geo_range, siae_constants.GEO_RANGE_ZONES)
        self.assertEqual(updated_activity.locations.count(), 2)
        self.assertIn(perimeter_city, updated_activity.locations.all())
        self.assertIn(perimeter_department, updated_activity.locations.all())
        self.assertIsNone(updated_activity.geo_range_custom_distance)

    def test_siae_user_can_edit_siae_activity_to_country(self):
        siae_activity = SiaeActivityFactory(
            siae=self.siae_with_user, with_zones_perimeter=True, presta_type=[siae_constants.PRESTA_DISP]
        )
        sector_before = SectorFactory(group=siae_activity.sector_group)
        siae_activity.sectors.add(sector_before)
        self.assertEqual(self.siae_with_user.activities.count(), 1)
        self.assertEqual(siae_activity.geo_range, siae_constants.GEO_RANGE_ZONES)
        self.assertEqual(siae_activity.sectors.count(), 1)
        self.assertEqual(siae_activity.sectors.first(), sector_before)

        perimeter_city = PerimeterFactory(name="Azay-le-rideau", kind=Perimeter.KIND_CITY, insee_code="37190")
        perimeter_department = PerimeterFactory(
            name="Vienne", kind=Perimeter.KIND_DEPARTMENT, insee_code="86", region_code="75"
        )
        siae_activity.locations.add(perimeter_city, perimeter_department)
        siae_activity.refresh_from_db()
        self.assertEqual(siae_activity.locations.count(), 2)

        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_activities_edit", args=[self.siae_with_user.slug, siae_activity.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        sector_after = SectorFactory()
        data = {
            "sector_group": sector_after.group.id,
            "sectors": [sector_after.id],
            "presta_type": [siae_constants.PRESTA_BUILD],
            "geo_range": siae_constants.GEO_RANGE_COUNTRY,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("dashboard_siaes:siae_edit_activities", args=[self.siae_with_user.slug])
        )
        self.assertEqual(self.siae_with_user.activities.count(), 1)
        updated_activity = self.siae_with_user.activities.first()
        self.assertEqual(updated_activity.sector_group, sector_after.group)
        self.assertEqual(updated_activity.sectors.count(), 1)
        self.assertEqual(updated_activity.sectors.first(), sector_after)
        self.assertEqual(updated_activity.presta_type, [siae_constants.PRESTA_BUILD])
        self.assertEqual(updated_activity.geo_range, siae_constants.GEO_RANGE_COUNTRY)
        self.assertEqual(updated_activity.locations.count(), 0)
        self.assertIsNone(updated_activity.geo_range_custom_distance)


class DashboardSiaeEditActivitiesDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_siae = UserFactory(kind=User.KIND_SIAE)
        cls.siae_with_user = SiaeFactory()
        cls.siae_with_user.users.add(cls.user_siae)

    def test_only_siae_user_can_delete_siae_activity(self):
        siae_activity = SiaeActivityFactory(siae=self.siae_with_user)
        self.assertEqual(self.siae_with_user.activities.count(), 1)

        self.client.force_login(UserFactory(kind=User.KIND_SIAE))
        url = reverse("dashboard_siaes:siae_edit_activities_delete", args=[self.siae_with_user.slug, siae_activity.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:home"))
        self.assertEqual(self.siae_with_user.activities.count(), 1)

        self.client.force_login(self.user_siae)
        url = reverse("dashboard_siaes:siae_edit_activities_delete", args=[self.siae_with_user.slug, siae_activity.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("dashboard_siaes:siae_edit_activities", args=[self.siae_with_user.slug])
        )
        self.assertEqual(self.siae_with_user.activities.count(), 0)
