"""Tools for the Security Agent."""

from typing import List, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field

from security_llm_lab.config import AppConfig
from security_llm_lab.integrations.siem import UTMStackClient
from security_llm_lab.rag.retriever import RagRetriever
from security_llm_lab.rules.generator import RuleGenerator

class SIEMQueryInput(BaseModel):
    query: str = Field(description="The search query string (e.g., 'source_ip:1.2.3.4')")
    time_range: str = Field(description="Time range for the search (e.g., 'last_24h')", default="last_24h")

@tool("query_siem", args_schema=SIEMQueryInput)
def query_siem(query: str, time_range: str = "last_24h") -> str:
    """Query the SIEM for security events matching the criteria."""
    # TODO: Implement actual search in UTMStackClient
    # For now, return mock data
    return f"Found 5 events for query '{query}' in {time_range}:\n1. [High] Failed login from {query.split(':')[-1] if ':' in query else 'unknown'}\n2. [Medium] Port scan detected"

class ThreatIntelInput(BaseModel):
    indicator: str = Field(description="The IOC to check (IP, Hash, Domain)")

@tool("check_threat_intel", args_schema=ThreatIntelInput)
def check_threat_intel(indicator: str) -> str:
    """Check a threat indicator against threat intelligence sources."""
    # Mock implementation
    if "1.2.3.4" in indicator:
        return f"Indicator {indicator} is MALICIOUS. Confidence: High. Source: AlienVault."
    return f"Indicator {indicator} is CLEAN. No records found."

class KnowledgeBaseInput(BaseModel):
    query: str = Field(description="The question to ask the knowledge base")

@tool("search_knowledge_base", args_schema=KnowledgeBaseInput)
def search_knowledge_base(query: str) -> str:
    """Search the internal security knowledge base (RAG)."""
    # This is a placeholder. The actual implementation is injected in get_tools.
    return "Error: Knowledge base not initialized."

def get_tools(config: AppConfig) -> List[any]:
    """Return a list of tools enabled in the configuration."""
    
    # Initialize RAG Retriever if available
    rag_retriever = None
    index_path = config.rag_dir / f"{config.rag.index_name}.joblib"
    if index_path.exists():
        rag_retriever = RagRetriever(index_path)

    def _search_kb(query: str) -> str:
        """Search the knowledge base."""
        if not rag_retriever:
            return "Knowledge base index not found. Please run 'collect' first."
        results = rag_retriever.query(query, top_k=3)
        if not results:
            return "No relevant information found in the knowledge base."
        
        context = "\n".join([f"- {r['content']} (Source: {r.get('source', 'unknown')})" for r in results])
        return f"Retrieved context:\n{context}"

    # Create the tool with the closure
    search_kb_tool = tool("search_knowledge_base", args_schema=KnowledgeBaseInput)(_search_kb)

    # Initialize Rule Generator
    rule_generator = RuleGenerator(config)

    class RuleGenInput(BaseModel):
        description: str = Field(description="Description of the rule to generate")

    @tool("generate_sigma_rule", args_schema=RuleGenInput)
    def generate_sigma_rule(description: str) -> str:
        """Generate a Sigma rule from a description."""
        return rule_generator.generate_sigma(description)

    @tool("generate_splunk_query", args_schema=RuleGenInput)
    def generate_splunk_query(description: str) -> str:
        """Generate a Splunk query from a description."""
        return rule_generator.generate_splunk(description)

    enabled_tools = []
    tool_map = {
        "query_siem": query_siem,
        "check_threat_intel": check_threat_intel,
        "search_knowledge_base": search_kb_tool,
        "generate_sigma_rule": generate_sigma_rule,
        "generate_splunk_query": generate_splunk_query,
    }
    
    for tool_name in config.agent.tools:
        if tool_name in tool_map:
            enabled_tools.append(tool_map[tool_name])
            
    return enabled_tools
