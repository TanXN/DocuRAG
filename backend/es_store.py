from elasticsearch import Elasticsearch

ES_URL = "http://localhost:9200"
INDEX_NAME = "docurag_chunks"

es = Elasticsearch(ES_URL)

def create_es_index() -> None:
    """
    创建es索引
    content用于关键词全文检索
    其他字段来源引用和过滤
    """
    if es.indices.exists(index=INDEX_NAME):
        return

    mapping = {
        "mappings": {
            "properties": {
                "chunk_id": {
                    "type": "keyword",
                },
                "file_name": {
                    "type": "keyword",
                },
                "file_type": {
                    "type": "keyword",
                },
                "page": {
                    "type": "integer",
                },
                "chunk_index": {
                    "type": "integer",
                },
                "content": {
                    "type":"text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                }
            }
        }
    }

    es.indices.create(index=INDEX_NAME, body=mapping)

def index_chunk_to_es(
    chunk_id: str,
    content: str,
    metadata: dict
) -> None:
    """
    把一个chunk写入Elasticsearch

    """
    doc = {
        "chunk_id": chunk_id,
        "content": content,
        "file_name": metadata["file_name"],
        "file_type": metadata["file_type"],
        "page": metadata["page"],
        "chunk_index": metadata["chunk_index"],
    }

    es.index(
        index = INDEX_NAME,
        id = chunk_id,
        document = doc
    )

def keyword_search_es(question: str, top_k: int = 5 ) -> list[dict]:
    response = es.search(
        # explain=True,
        index=INDEX_NAME,
        size=top_k,
        query={
            "match": {
                "content": question
            }
        }
    )

    result = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]

        result.append({
            "document": source["content"],
            "metadata": {
                "chunk_id": source.get("chunk_id"),
                "file_name": source.get("file_name"),
                "file_type": source.get("file_type"),
                "page": source.get("page"),
                "chunk_index": source.get("chunk_index"),
            },
            "bm25_score": hit["_score"],
            "retrieval_type": "keyword",
            "explanation": hit.get("_explanation")
        })

    return result