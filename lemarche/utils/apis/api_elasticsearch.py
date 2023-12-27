from django.conf import settings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.elasticsearch import ElasticsearchStore


BASE_URL = f"{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"
URL = f"{settings.ELASTICSEARCH_SCHEME}://{BASE_URL}"
URL_WITH_USER = (
    f"{settings.ELASTICSEARCH_SCHEME}://{settings.ELASTICSEARCH_USERNAME}:{settings.ELASTICSEARCH_PASSWORD}@{BASE_URL}"
)


def siaes_similarity_search(search_text):
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

    similar_docs = db.similarity_search(search_text, k=10)
    siaes_id = []
    for similar_doc in similar_docs:
        siaes_id.append(similar_doc.metadata["id"])

    return siaes_id
