from django.conf import settings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.elasticsearch import ElasticsearchStore

from lemarche.perimeters.models import Perimeter


BASE_URL = f"{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"
URL = f"{settings.ELASTICSEARCH_SCHEME}://{BASE_URL}"
URL_WITH_USER = (
    f"{settings.ELASTICSEARCH_SCHEME}://{settings.ELASTICSEARCH_USERNAME}:{settings.ELASTICSEARCH_PASSWORD}@{BASE_URL}"
)


def siaes_similarity_search(search_text: str, search_filter: dict = {}):
    """Performs semantic search with Elasticsearch as a vector db

    Args:
        search_text (str): User search query

    Returns:
        list: list of siaes id that match the search query
    """
    db = ElasticsearchStore(
        embedding=OpenAIEmbeddings(),
        es_user=settings.ELASTICSEARCH_USERNAME,
        es_password=settings.ELASTICSEARCH_PASSWORD,
        es_url=URL,
        index_name=settings.ELASTICSEARCH_INDEX_SIAES,
    )
    similar_docs = db.similarity_search_with_score(search_text, k=50, filter=search_filter)
    siaes_id = []
    for similar_doc, similar_score in similar_docs:
        # Discussion to understand score :
        # https://github.com/langchain-ai/langchain/discussions/9984#discussioncomment-6860841
        if similar_score > settings.ELASTICSEARCH_MIN_SCORE:
            siaes_id.append(similar_doc.metadata["id"])

    return siaes_id


def siaes_similarity_search_with_geo_distance(
    search_text: str, geo_distance: int = None, geo_lat: float = None, geo_lon: float = None
):
    search_filter = []
    if geo_distance and geo_lat and geo_lon:
        search_filter = [
            {
                "geo_distance": {
                    "distance": f"{geo_distance}km",
                    "metadata.geo_location": {
                        "lat": geo_lat,
                        "lon": geo_lon,
                    },
                }
            }
        ]

    return siaes_similarity_search(search_text, search_filter)


def siaes_similarity_search_with_city(search_text: str, city: Perimeter):
    search_filter = [
        {
            "bool": {
                "should": [
                    {"bool": {"must": [], "filter": [{"match_phrase": {"metadata.geo_country": True}}]}},
                    {"bool": {"must": [], "filter": [{"match_phrase": {"metadata.geo_reg": city.region_code}}]}},
                    {"bool": {"must": [], "filter": [{"match_phrase": {"metadata.geo_dep": city.department_code}}]}},
                    {
                        "bool": {
                            "must": [],
                            "filter": [
                                {
                                    "geo_distance": {
                                        "distance": "50km",
                                        "metadata.geo_location": {
                                            "lat": city.latitude,
                                            "lon": city.longitude,
                                        },
                                    }
                                }
                            ],
                        }
                    },
                ],
                "minimum_should_match": 1,
            }
        }
    ]
    return siaes_similarity_search(search_text, search_filter)
