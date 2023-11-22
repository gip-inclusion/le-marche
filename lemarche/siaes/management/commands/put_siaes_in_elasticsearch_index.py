from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import TextField
from django.db.models.functions import Length
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import ElasticVectorSearch

from lemarche.siaes.models import Siae


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("put siae to elasticsearch index started.."))

        # Create the HuggingFace Transformer
        model_name = "sentence-transformers/all-mpnet-base-v2"
        hf = HuggingFaceEmbeddings(model_name=model_name)

        # Elasticsearch as a vector db
        url = (
            f"https://{settings.ELASTICSEARCH_USERNAME}:{settings.ELASTICSEARCH_PASSWORD}@"
            f"{settings.ELASTICSEARCH_HOST}:443"
        )
        db = ElasticVectorSearch(embedding=hf, elasticsearch_url=url, index_name=settings.ELASTICSEARCH_INDEX_SIAES)

        # Siaes with completed description
        TextField.register_lookup(Length)  # at least 10 characters
        siaes = Siae.objects.filter(description__length__gt=9).all()

        for siae in siaes:
            text = siae.description
            if siae.offers.count() > 0:
                offers = "\n\nPrestations:\n"
                for offer in siae.offers.all():
                    offers += f"- {offer.name}:\n{offer.description}\n\n"
                text += offers

            db.from_texts(
                [text],
                metadatas=[{"id": siae.id, "name": siae.name, "website": siae.website if siae.website else ""}],
                embedding=hf,
                elasticsearch_url=url,
                index_name=settings.ELASTICSEARCH_INDEX_SIAES,
            )

            self.stdout.write(self.style.SUCCESS(f"{siae.name} added !"))
