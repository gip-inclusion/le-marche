from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.db.models import Q
from django.test import TestCase
from django.utils import timezone

from lemarche.companies.models import Company, CompanySiaeClientReferenceMatch
from tests.companies.factories import CompanyFactory
from tests.siaes.factories import SiaeClientReferenceFactory, SiaeFactory
from tests.tenders.factories import TenderFactory
from tests.users.factories import UserFactory


class CompanyModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = CompanyFactory(name="Mon entreprise")

    def test_slug_field(self):
        self.assertEqual(self.company.slug, "mon-entreprise")

    def test_str(self):
        self.assertEqual(str(self.company), "Mon entreprise")


class CompanyQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = UserFactory()
        cls.user_2 = UserFactory()
        TenderFactory(author=cls.user_1)
        TenderFactory(author=cls.user_1)
        cls.company_with_users = CompanyFactory(users=[cls.user_1, cls.user_2])
        cls.company = CompanyFactory()

    def test_with_user_stats(self):
        company_queryset = Company.objects.with_user_stats()
        # user_count
        self.assertEqual(company_queryset.get(id=self.company.id).user_count_annotated, 0)
        self.assertEqual(company_queryset.get(id=self.company_with_users.id).user_count_annotated, 2)
        # user_tender_count
        self.assertEqual(company_queryset.get(id=self.company.id).user_tender_count_annotated, 0)
        self.assertEqual(company_queryset.get(id=self.company_with_users.id).user_tender_count_annotated, 2)


class CompanySiaeClientReferenceMatchCommandTest(TestCase):
    def setUp(self):
        self.siae1 = SiaeFactory()
        self.siae2 = SiaeFactory()
        self.siae3 = SiaeFactory()

        self.company1 = CompanyFactory(name="Serenity Solutions")
        self.company2 = CompanyFactory(name="Bativia")
        self.company3 = CompanyFactory(name="Heliosys")

    def test_command_with_no_recent_client_references(self):
        """Test when there are no recent client references"""

        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=StringIO())
        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 0)

    def test_command_with_default_parameters(self):
        """Test command with default parameters"""
        SiaeClientReferenceFactory(
            name=self.company1.name, siae=self.siae1, created_at=timezone.now() - timedelta(days=1)
        )
        call_command("find_company_siae_client_reference_matches", stdout=StringIO())

        # Verify no match is created in dry-run mode
        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 0)

    def test_command_with_wet_run(self):
        """Test command in wet-run mode (actual creation)"""
        client_ref1 = SiaeClientReferenceFactory(
            name=self.company1.name, siae=self.siae1, created_at=timezone.now() - timedelta(days=1)
        )
        SiaeClientReferenceFactory(name="Optimizia", siae=self.siae1, created_at=timezone.now() - timedelta(days=1))
        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=StringIO())

        # Verify match is created
        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 1)
        match = CompanySiaeClientReferenceMatch.objects.first()
        self.assertEqual(match.company, self.company1)
        self.assertEqual(match.siae_client_reference, client_ref1)
        self.assertEqual(match.similarity_score, 1.0)
        self.assertEqual(match.company_name, self.company1.name)
        self.assertEqual(match.client_reference_name, client_ref1.name)
        self.assertEqual(match.moderation_status, CompanySiaeClientReferenceMatch.ModerationStatus.PENDING)
        self.assertIsNone(match.moderated_by)

        # admin action ?
        client_ref1.updated_at = timezone.now() - timedelta(days=1)
        client_ref1.save()

        call_command("find_company_siae_client_reference_matches", wet_run=False, stdout=StringIO())

        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 1)

    def test_command_with_custom_days(self):
        """Test command with custom number of days"""
        # Create an old client reference
        SiaeClientReferenceFactory(
            name=self.company2.name, siae=self.siae2, created_at=timezone.now() - timedelta(days=20)
        )

        # Test with 10 days - should exclude the old reference
        call_command("find_company_siae_client_reference_matches", days=10, wet_run=True, stdout=StringIO())
        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 0)

        # Test with 30 days (default) - should include the old reference
        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=StringIO())
        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 1)

    def test_command_with_custom_min_score(self):
        """Test command with custom similarity score"""

        # Create a new client reference with a similar name : Serenity Solutions <-> Sérénité Solutions (score: 0.440)
        SiaeClientReferenceFactory(
            name="Sérénité Solutions", siae=self.siae3, created_at=timezone.now() - timedelta(days=1)
        )

        # Test with high score (0.8)
        call_command("find_company_siae_client_reference_matches", min_score=0.8, wet_run=True, stdout=StringIO())
        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 0)

        # Test with low score (0.1)
        call_command("find_company_siae_client_reference_matches", min_score=0.1, wet_run=True, stdout=StringIO())
        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 1)

    def test_command_with_limit(self):
        """Test command with match limit"""
        # Create multiple companies and references to have many potential matches
        for i in range(6):
            company_name = f"TestCorp {i}"
            CompanyFactory(name=company_name)
            SiaeClientReferenceFactory(
                name=company_name, siae=self.siae1, created_at=timezone.now() - timedelta(days=1)
            )

        # Test with limit of 5
        stdout = StringIO()
        call_command("find_company_siae_client_reference_matches", limit=5, wet_run=True, stdout=stdout)
        self.assertIn("Reached limit of 5 matches", stdout.getvalue())
        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 5)

    def test_command_excludes_empty_names(self):
        """Test that command excludes empty names"""

        # create a company with empty name
        CompanyFactory(name="")
        # create a client reference with empty name
        SiaeClientReferenceFactory(name="", siae=self.siae1, created_at=timezone.now() - timedelta(days=1))

        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=StringIO())

        # Verify no match is created with empty names
        matches = CompanySiaeClientReferenceMatch.objects.filter(Q(company_name="") | Q(client_reference_name=""))
        self.assertEqual(matches.count(), 0)

    def test_command_handles_existing_match_with_better_similarity_score(self):
        """Test that command handles existing match with better similarity score"""

        client_ref = SiaeClientReferenceFactory(
            name="Sérénité Solutions", siae=self.siae1, created_at=timezone.now() - timedelta(days=1)
        )

        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=StringIO())

        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 1)
        match = CompanySiaeClientReferenceMatch.objects.first()
        self.assertEqual(match.company, self.company1)
        self.assertEqual(match.siae_client_reference, client_ref)
        self.assertEqual(match.similarity_score, Decimal("0.44"))
        self.assertEqual(match.company_name, self.company1.name)
        self.assertEqual(match.client_reference_name, client_ref.name)

        # simulate moderation approval
        match.moderation_status = CompanySiaeClientReferenceMatch.ModerationStatus.APPROVED
        match.save()

        # remove accent from client reference name to test small better similarity score
        client_ref.name = "Serenité Solutions"
        client_ref.save()

        stdout = StringIO()
        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=stdout)
        self.assertIn(
            f"Match already exists for {client_ref.name} but better match found, updating it", stdout.getvalue()
        )

        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 1)
        match = CompanySiaeClientReferenceMatch.objects.first()
        self.assertEqual(match.company, self.company1)
        self.assertEqual(match.siae_client_reference, client_ref)  # same client reference
        self.assertEqual(match.similarity_score, Decimal("0.8"))  # similarity score updated
        self.assertEqual(match.company_name, self.company1.name)
        self.assertEqual(match.client_reference_name, client_ref.name)  # client reference name updated
        self.assertEqual(match.moderation_status, CompanySiaeClientReferenceMatch.ModerationStatus.APPROVED)

    def test_command_handles_existing_match_with_lower_similarity_score_under_limit(self):
        """Test that command handles existing match with lower similarity score"""

        client_ref = SiaeClientReferenceFactory(
            name="Sérénité Solutions", siae=self.siae1, created_at=timezone.now() - timedelta(days=1)
        )

        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=StringIO())

        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 1)
        match = CompanySiaeClientReferenceMatch.objects.first()
        self.assertEqual(match.company, self.company1)
        self.assertEqual(match.siae_client_reference, client_ref)
        self.assertEqual(match.similarity_score, Decimal("0.44"))
        self.assertEqual(match.company_name, self.company1.name)
        self.assertEqual(match.client_reference_name, client_ref.name)

        # simulate moderation approval
        match.moderation_status = CompanySiaeClientReferenceMatch.ModerationStatus.APPROVED
        match.save()

        # update client reference name to test lower similarity score under limit
        client_ref.name = "Serenité Problème"
        client_ref.save()

        stdout = StringIO()
        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=stdout)
        self.assertIn(
            f"Match already exists for {client_ref.name} but no better match found, deleting it", stdout.getvalue()
        )
        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 0)

    def test_command_handles_existing_match_with_lower_similarity_score_over_limit(self):
        """Test that command handles existing match with lower similarity score over limit"""

        client_ref = SiaeClientReferenceFactory(
            name="Sérénité Solutions", siae=self.siae1, created_at=timezone.now() - timedelta(days=1)
        )

        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=StringIO())

        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 1)
        match1 = CompanySiaeClientReferenceMatch.objects.first()
        self.assertEqual(match1.company, self.company1)
        self.assertEqual(match1.siae_client_reference, client_ref)
        self.assertEqual(match1.similarity_score, Decimal("0.44"))
        self.assertEqual(match1.company_name, self.company1.name)
        self.assertEqual(match1.client_reference_name, client_ref.name)

        # update client reference name to test lower similarity score over limit
        client_ref.name = "Sérénité Solutiont"
        client_ref.save()

        stdout = StringIO()
        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=stdout)
        self.assertIn(
            f"Match already exists for {client_ref.name} but no better match found, deleting it", stdout.getvalue()
        )
        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 1)
        match2 = CompanySiaeClientReferenceMatch.objects.first()
        self.assertNotEqual(match2.pk, match1.pk)
        self.assertEqual(match2.company, self.company1)
        self.assertEqual(match2.siae_client_reference, client_ref)
        self.assertEqual(match2.similarity_score, Decimal("0.333333"))
        self.assertEqual(match2.company_name, self.company1.name)
        self.assertEqual(match2.client_reference_name, client_ref.name)

    def test_command_matches_are_ordered_by_similarity_score(self):
        """Test that matches are ordered by similarity score"""

        CompanyFactory(name="Bati")

        client_ref = SiaeClientReferenceFactory(
            name="Bativi", siae=self.siae1, created_at=timezone.now() - timedelta(days=1)
        )

        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=StringIO())

        # self.company2 (Bativia) should be the first match (similarity score is 0.6666667)
        # Bativi is more similar to Bativia than Bati
        self.assertEqual(CompanySiaeClientReferenceMatch.objects.count(), 1)
        match = CompanySiaeClientReferenceMatch.objects.first()
        self.assertEqual(match.company, self.company2)
        self.assertEqual(match.siae_client_reference, client_ref)
        self.assertEqual(match.similarity_score, Decimal("0.666667"))
        self.assertEqual(match.company_name, self.company2.name)
        self.assertEqual(match.client_reference_name, client_ref.name)

    def test_command_with_spaces(self):
        """Test with spaces"""
        client_ref_spaces = SiaeClientReferenceFactory(
            name="  Bati via ", siae=self.siae1, created_at=timezone.now() - timedelta(days=1)
        )

        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=StringIO())

        # Verify a match is created despite spaces
        self.assertIsNotNone(
            CompanySiaeClientReferenceMatch.objects.filter(
                company=self.company2, siae_client_reference=client_ref_spaces
            ).first()
        )

    def test_command_with_special_characters(self):
        # Test with similar special characters
        company_accents = CompanyFactory(name="Café & Co")
        client_ref_accents = SiaeClientReferenceFactory(
            name="Cafe et Co", siae=self.siae1, created_at=timezone.now() - timedelta(days=1)
        )

        call_command("find_company_siae_client_reference_matches", wet_run=True, stdout=StringIO())

        # Verify a match is created despite accent differences (Café & Co <-> Cafe et Co)
        self.assertIsNotNone(
            CompanySiaeClientReferenceMatch.objects.filter(
                company=company_accents, siae_client_reference=client_ref_accents
            ).first()
        )
