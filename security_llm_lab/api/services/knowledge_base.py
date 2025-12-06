from ...rag.engine import QdrantRagEngine

# Singleton instance
knowledge_base = QdrantRagEngine(lazy_init=True)

async def add_knowledge(text: str, source: str):
    return await knowledge_base.add_document(text, {"source": source})

async def search_knowledge(query: str):
    return await knowledge_base.search(query)
