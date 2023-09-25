from django.contrib.postgres.search import SearchVector
from django.db import models
from django.db.models import Value

from lemarche.siaes.models import Siae
from lemarche.utils.commands import BaseCommand


SIAE_COUNT = Siae.objects.count()
RANGE_STEP = 1000


class Command(BaseCommand):
    """
    Usage:
    - poetry run python manage.py set_search_vector_field
    """

    def handle(self, *args, **options):
        self.stdout_info("-" * 80)
        self.stdout_info("Reseting search_vector field...")
        progress = 0
        for i in range(0, SIAE_COUNT, RANGE_STEP):  # to avoid memory issues
            for siae in Siae.objects.prefetch_related("sectors", "offers", "labels").all()[i, i + RANGE_STEP]:
                siae_search_vector = (
                    SearchVector(
                        Value(siae.name, output_field=models.CharField()),
                        # weight="A",
                        # config="french",
                    )
                    + SearchVector(
                        Value(siae.brand, output_field=models.CharField()),
                        # weight="A",
                        # config="french",
                    )
                    + SearchVector(
                        Value(siae.siret, output_field=models.CharField()),
                        # weight="A",
                        # config="french",
                    )
                    + SearchVector(
                        Value(siae.city, output_field=models.CharField()),
                        # weight="A",
                        # config="french",
                    )
                    + SearchVector(
                        Value(siae.department, output_field=models.CharField()),
                        # weight="A",
                        # config="french",
                    )
                    + SearchVector(
                        Value(siae.region, output_field=models.CharField()),
                        # weight="A",
                        # config="french",
                    )
                    + SearchVector(
                        Value(siae.kind, output_field=models.CharField()),
                        # weight="A",
                        # config="french",
                    )
                    + SearchVector(
                        Value(siae.description, output_field=models.CharField()),
                        # weight="A",
                        config="french",
                    )
                )
                if siae.sectors:
                    siae_search_vector += SearchVector(
                        Value(
                            " ".join(str(sector.name) for sector in siae.sectors.all()),
                        ),
                        # weight="A",
                        config="french",
                    )
                if siae.offers:
                    siae_search_vector += SearchVector(
                        Value(
                            " ".join(str(offer.name) for offer in siae.offers.all()),
                        ),
                        # weight="A",
                        config="french",
                    )
                if siae.labels:
                    siae_search_vector += SearchVector(
                        Value(
                            " ".join(str(label.name) for label in siae.labels.all()),
                        ),
                        # weight="A",
                        config="french",
                    )
                siae.search_vector = siae_search_vector
                siae.save(update_fields=["search_vector"])
                progress += 1
                if (progress % 500) == 0:
                    print(f"{progress}...")
