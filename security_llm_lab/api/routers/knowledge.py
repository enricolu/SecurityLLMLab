from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.knowledge_base import add_knowledge, search_knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

class DocumentCreate(BaseModel):
    text: str
    source: str

@router.post("/")
async def ingest_document(doc: DocumentCreate):
    try:
        doc_id = await add_knowledge(doc.text, doc.source)
        return {"id": doc_id, "status": "indexed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def query_knowledge(q: str):
    return await search_knowledge(q)
