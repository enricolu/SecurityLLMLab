from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import os
import uuid
from typing import List, Dict, Any

class QdrantRagEngine:
    def __init__(self, collection_name: str = "security-knowledge", lazy_init: bool = False):
        self.collection_name = collection_name
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=self.qdrant_url)
        # Load local embedding model (lightweight)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        if not lazy_init:
            self._ensure_collection()

    def _ensure_collection(self):
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            # Create collection if not exists
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.encoder.get_sentence_embedding_dimension(),
                    distance=models.Distance.COSINE
                )
            )

    async def add_document(self, text: str, metadata: Dict[str, Any] = None):
        """Encodes and indexes a document."""
        if metadata is None:
            metadata = {}
            
        vector = self.encoder.encode(text).tolist()
        doc_id = str(uuid.uuid4())
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=doc_id,
                    vector=vector,
                    payload={
                        "text": text,
                        **metadata
                    }
                )
            ]
        )
        return doc_id

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Semantic search."""
        vector = self.encoder.encode(query).tolist()
        
        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit
        )
        
        results = []
        for hit in hits:
            results.append({
                "text": hit.payload.get("text"),
                "score": hit.score,
                "metadata": {k:v for k,v in hit.payload.items() if k != "text"}
            })
        return results
