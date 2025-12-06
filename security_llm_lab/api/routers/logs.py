from fastapi import APIRouter, HTTPException, Query
from ..elastic import search_logs
from typing import Optional

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/")
async def get_logs(q: Optional[str] = Query(None), limit: int = 50):
    """
    Search logs in Elasticsearch.
    If 'q' is provided, performs a simple match query on 'message'.
    Otherwise returns recent logs.
    """
    query = {
        "size": limit,
        "sort": [{"timestamp": "desc"}],
        "query": {"match_all": {}}
    }
    
    if q:
        query["query"] = {
            "multi_match": {
                "query": q,
                "fields": ["message", "event_action", "user.name", "host.name"]
            }
        }

    try:
        # In dual mode, we might switch index name or assume it's 'winlogbeat-*'
        # For Demo, we used 'winlogbeat-demo'.
        # Let's search both or wildcard.
        result = await search_logs("winlogbeat-*", query)
        hits = result["hits"]["hits"]
        return [hit["_source"] for hit in hits]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
