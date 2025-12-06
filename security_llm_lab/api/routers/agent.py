from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..services.query_generator import QueryGenerator
from ..services.threat_analyzer import ThreatAnalyzer
from ..elastic import search_logs
from ..models import Alert
from ..database import get_db

router = APIRouter(prefix="/agent", tags=["agent"])

class ChatRequest(BaseModel):
    message: str
    model: str = "ollama" 
    model_name: str = "llama3"

class AnalysisRequest(BaseModel):
    model: str = "ollama"
    model_name: str = "llama3"

@router.post("/analyze")
async def analyze_threats(request: AnalysisRequest, db: Session = Depends(get_db)):
    try:
        # Fetch high/medium severity alerts from DB
        # In a real scenario, we might filter by time window
        alerts = db.query(Alert).filter(Alert.severity.in_(["high", "medium"])).order_by(Alert.created_at.desc()).limit(10).all()
        
        if not alerts:
             return {"analysis": "No high or medium severity alerts found to analyze."}
        
        # Convert to dict
        alerts_data = [{"title": a.title, "severity": a.severity, "source": a.source, "created_at": str(a.created_at)} for a in alerts]
        
        analyzer = ThreatAnalyzer(backend=request.model, model_name=request.model_name)
        analysis = await analyzer.analyze_alerts(alerts_data)
        
        return {"analysis": analysis, "alerts_analyzed": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Detect intent (simple heuristic)
        # 1. Search Knowledge Base (RAG)
        if "how" in request.message.lower() or "what is" in request.message.lower() or "mitigate" in request.message.lower():
             from ..services.knowledge_base import search_knowledge
             hits = await search_knowledge(request.message)
             
             if hits:
                 context = "\n".join([f"- {h['text']}" for h in hits])
                 # Rerank/Summarize with LLM (simplified)
                 return {
                     "response": f"Based on my knowledge base:\n{context}",
                     "sources": hits
                 }

        # 2. Search Logs (Elastic)
        if "show" in request.message.lower() or "find" in request.message.lower() or "search" in request.message.lower():
            generator = QueryGenerator(backend=request.model, model_name=request.model_name)
            dsl = await generator.generate_dsl(request.message)
            
            # Execute search
            results = await search_logs("winlogbeat-*", dsl)
            return {
                "response": "I found the following logs based on your query.",
                "dsl": dsl,
                "data": [hit["_source"] for hit in results["hits"]["hits"]]
            }
        
        # 3. Fallback
        return {"response": f"I received your message: {request.message}. Try asking 'How to mitigate...' or 'Show me logs...'"}
             
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

