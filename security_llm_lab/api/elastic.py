import os
from elasticsearch import AsyncElasticsearch
from datetime import datetime

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

es_client = AsyncElasticsearch(hosts=[ELASTICSEARCH_URL])

async def index_log(index_name: str, document: dict):
    if "timestamp" not in document:
        document["timestamp"] = datetime.utcnow().isoformat()
    await es_client.index(index=index_name, document=document)

async def search_logs(index_name: str, query: dict):
    return await es_client.search(index=index_name, body=query)

async def create_index(index_name: str):
    ignore_existing = {"ignore": 400}
    # Basic mapping for security logs
    mapping = {
        "mappings": {
            "properties": {
                "timestamp": {"type": "date"},
                "event_id": {"type": "keyword"},
                "event_action": {"type": "keyword"},
                "host": {
                    "properties": {
                        "name": {"type": "keyword"}
                    }
                },
                "user": {
                    "properties": {
                        "name": {"type": "keyword"}
                    }
                },
                 "message": {"type": "text"}
            }
        }
    }
    if not await es_client.indices.exists(index=index_name):
        await es_client.indices.create(index=index_name, body=mapping)
