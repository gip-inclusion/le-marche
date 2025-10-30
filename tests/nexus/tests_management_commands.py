from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from lemarche.nexus.management.commands.populate_metabase_nexus import create_table, get_connection
from tests.siaes.factories import SiaeFactory
from tests.users.factories import UserFactory


class TestCommand(TestCase):
    @freeze_time()
    def test_populate_metabase_nexus(db):
        user = UserFactory()
        siae = SiaeFactory(users=[user], address="3 impasse Jean Dupont", post_code="33330", city="Alizé")

        # company_1 = CompanyMembershipFactory(
        #     user=employer,
        #     company__uid="11111111-1111-1111-1111-111111111111",
        #     company__insee_city=create_city_saint_andre(),
        # ).company
        # company_2 = CompanyMembershipFactory(
        #     user=employer,
        #     is_admin=False,
        #     company__uid="22222222-2222-2222-2222-222222222222",
        # ).company
        # organization = PrescriberMembershipFactory(
        #     user=prescriber,
        #     organization__uid="33333333-3333-3333-3333-333333333333",
        # ).organization

        create_table()
        call_command("populate_metabase_nexus")

        with get_connection() as conn, conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users ORDER BY email")
            rows = cursor.fetchall()
            assert rows == [
                (
                    "le-marché",
                    str(user.pk),
                    f"le-marché--{user.pk}",
                    user.last_name,
                    user.first_name,
                    user.email,
                    user.phone,
                    user.last_login,
                    "Django",
                    "employeur",
                    timezone.now(),
                ),
            ]

            cursor.execute("SELECT * FROM memberships ORDER BY structure_id_unique")
            rows = cursor.fetchall()
            assert rows == [
                (
                    "le-marché",
                    f"le-marché--{user.pk}",
                    f"le-marché--{siae.pk}",
                    "administrateur",
                    timezone.now(),
                ),
            ]

            cursor.execute("SELECT * FROM structures ORDER BY id_unique")
            rows = cursor.fetchall()
            assert rows == [
                (
                    "le-marché",
                    str(siae.pk),
                    f"le-marché--{siae.pk}",
                    siae.siret,
                    siae.brand,
                    f"company--{siae.kind}",
                    "",
                    "3 impasse Jean Dupont, 33330 Alizé",
                    siae.post_code,
                    siae.latitude,
                    siae.longitude,
                    siae.email,
                    siae.phone,
                    timezone.now(),
                ),
            ]
