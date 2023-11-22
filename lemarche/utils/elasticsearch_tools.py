from django.conf import settings
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import ElasticVectorSearch


def siaes_similarity_search(search_text):
    # Create the HuggingFace Transformer
    model_name = "sentence-transformers/all-mpnet-base-v2"
    hf = HuggingFaceEmbeddings(model_name=model_name)

    # Elasticsearch as a vector db
    url = (
        f"https://{settings.ELASTICSEARCH_USERNAME}:{settings.ELASTICSEARCH_PASSWORD}@"
        f"{settings.ELASTICSEARCH_HOST}:443",
    )
    db = ElasticVectorSearch(embedding=hf, elasticsearch_url=url, index_name=settings.ELASTICSEARCH_INDEX_SIAES)

    # Start the search
    similar_docs = db.similarity_search_with_score(search_text, k=10)
    siaes_id = []
    for similar_doc, score in similar_docs:
        siaes_id.append(similar_doc.metadata["id"])

    return siaes_id
