import time

from django.conf import settings
from django.db.models import TextField
from django.db.models.functions import Length
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import ElasticVectorSearch

from lemarche.siaes.models import Siae
from lemarche.utils.apis.api_elasticsearch import URL_WITH_USER
from lemarche.utils.commands import BaseCommand


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        self.stdout_success("put siae to elasticsearch index started..")

        # Elasticsearch as a vector db
        embeddings = OpenAIEmbeddings()
        db = ElasticVectorSearch(
            embedding=embeddings, elasticsearch_url=URL_WITH_USER, index_name=settings.ELASTICSEARCH_INDEX_SIAES
        )

        # Siaes with completed description
        TextField.register_lookup(Length)  # at least 10 characters
        siaes = Siae.objects.filter(description__length__gt=9).all()

        for siae in siaes:
            db.from_texts(
                [siae.elasticsearch_index_text],
                metadatas=[siae.elasticsearch_index_metadata],
                embedding=embeddings,
                elasticsearch_url=URL_WITH_USER,
                index_name=settings.ELASTICSEARCH_INDEX_SIAES,
            )
            time.sleep(1)
            self.stdout_success(f"{siae.name} added !")
