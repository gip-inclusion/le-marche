from datetime import timedelta

from django.contrib.postgres.search import TrigramSimilarity
from django.utils import timezone

from lemarche.companies.models import Company, CompanySiaeClientReferenceMatch
from lemarche.siaes.models import SiaeClientReference
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    """
    Find potential matches between Company and SiaeClientReference using trigram similarity.

    Usage:
    - poetry run python manage.py find_company_siae_client_reference_matches
    - poetry run python manage.py find_company_siae_client_reference_matches --days 30
    - poetry run python manage.py find_company_siae_client_reference_matches --min-score 0.3
    - poetry run python manage.py find_company_siae_client_reference_matches --wet-run
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to look back for recent SiaeClientReference (default: 30)",
        )
        parser.add_argument(
            "--min-score", type=float, default=0.3, help="Minimum similarity score to consider a match (default: 0.3)"
        )
        parser.add_argument("--wet-run", action="store_true", help="Create matches in database (default: dry run)")
        parser.add_argument(
            "--limit", type=int, default=100, help="Maximum number of matches to process (default: 100)"
        )

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Finding Company <-> SiaeClientReference matches using trigram similarity")

        days = options["days"]
        min_score = options["min_score"]
        wet_run = options["wet_run"]
        limit = options["limit"]

        # Get recent SiaeClientReference
        cutoff_date = timezone.now() - timedelta(days=days)
        recent_client_references = SiaeClientReference.objects.filter(created_at__gte=cutoff_date).exclude(name="")

        self.stdout_info(f"Found {recent_client_references.count()} recent SiaeClientReference")

        if not recent_client_references.exists():
            self.stdout_warning("No recent SiaeClientReference found")
            return

        # Get companies with names
        companies = Company.objects.exclude(name="")
        self.stdout_info(f"Found {companies.count()} companies to match against")

        matches_found = 0
        matches_created = 0

        for client_reference in recent_client_references:
            if matches_found >= limit:
                self.stdout_info(f"Reached limit of {limit} matches")
                break

            # check if match already exists for this client reference
            existing_match = (
                CompanySiaeClientReferenceMatch.objects.filter(siae_client_reference=client_reference)
                .order_by("-updated_at")
                .first()
            )
            if existing_match:
                # if match update date is more recent than reference update date, do nothing
                if existing_match.updated_at > client_reference.updated_at:
                    continue

                # else search for a better match with the same company
                new_similarity = (
                    companies.filter(id=existing_match.company_id)
                    .annotate(similarity=TrigramSimilarity("name", client_reference.name))
                    .filter(similarity__gte=min_score)
                    .first()
                )
                if new_similarity and round(new_similarity.similarity, 6) > existing_match.similarity_score:
                    self.stdout_info(
                        f"Match already exists for {client_reference.name} but better match found, updating it"
                    )
                    existing_match.client_reference_name = client_reference.name
                    existing_match.similarity_score = new_similarity.similarity
                    existing_match.save()
                    continue
                else:
                    self.stdout_info(
                        f"Match already exists for {client_reference.name} but no better match found, deleting it"
                    )
                    existing_match.delete()

            # find companies with similar names using trigram similarity
            similar_companies = (
                companies.annotate(similarity=TrigramSimilarity("name", client_reference.name))
                .filter(similarity__gte=min_score)
                .order_by("-similarity")
            )

            # link to only one company per reference, the most similar one
            if similar_company := similar_companies.first():
                matches_found += 1
                self.stdout_info(
                    f"Potential match: {similar_company.name} <-> {client_reference.name} "
                    f"(score: {similar_company.similarity:.6f})"
                )

                if wet_run:
                    # Create the match
                    CompanySiaeClientReferenceMatch.objects.create(
                        company=similar_company,
                        siae_client_reference=client_reference,
                        similarity_score=similar_company.similarity,
                        company_name=similar_company.name,
                        client_reference_name=client_reference.name,
                        moderation_status=CompanySiaeClientReferenceMatch.ModerationStatus.PENDING,
                    )
                    matches_created += 1
                    self.stdout_success(f"Created match #{matches_created}")

        # Summary
        msg_success = [
            "----- Company <-> SiaeClientReference Matching -----",
            f"Processed {recent_client_references.count()} recent SiaeClientReference",
            f"Found {matches_found} potential matches",
            (
                f"Created {matches_created} new matches"
                if wet_run
                else f"Would create {matches_found} matches (dry run)"
            ),
            f"Minimum similarity score: {min_score}",
            f"Days back: {days}",
        ]
        self.stdout_messages_success(msg_success)
