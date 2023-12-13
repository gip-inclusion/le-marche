from django.conf import settings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.elasticsearch import ElasticsearchStore


def siaes_similarity_search(search_text):
    # Elasticsearch as a vector db
    url = f"https://{settings.ELASTICSEARCH_HOST}:443"
    db = ElasticsearchStore(
        embedding=OpenAIEmbeddings(),
        es_user=settings.ELASTICSEARCH_USERNAME,
        es_password=settings.ELASTICSEARCH_PASSWORD,
        es_url=url,
        index_name=settings.ELASTICSEARCH_INDEX_SIAES,
    )

    similar_docs = db.similarity_search(search_text, k=10)
    siaes_id = []
    for similar_doc in similar_docs:
        siaes_id.append(similar_doc.metadata["id"])

    return siaes_id
