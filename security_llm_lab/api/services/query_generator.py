import json
from langchain_core.prompts import PromptTemplate
from ...config import LLMConfig
from ...llm_client import get_llm_client

class QueryGenerator:
    def __init__(self, backend: str = "ollama", model_name: str = "llama3"):
        config = LLMConfig(backend=backend, model_name=model_name)
        self.client = get_llm_client(config)
        self.llm = self.client.get_chat_model()
        
        self.prompt = PromptTemplate(
            input_variables=["query"],
            template="""You are an expert in Elasticsearch. 
            Translate the following natural language query into a valid Elasticsearch JSON query DSL.
            Return ONLY the JSON object, no markdown formatting, no explanations. 
            The context is security logs with fields: timestamp, event_id, event_action, host.name, user.name, message.
            
            Query: {query}
            
            Elasticsearch DSL JSON:
            """
        )

    async def generate_dsl(self, query: str) -> dict:
        formatted_prompt = self.prompt.format(query=query)
        response = self.llm.invoke(formatted_prompt)
        content = response.content.strip()
        
        # Cleanup potential markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback or error handling
            raise ValueError(f"Failed to parse LLM response as JSON: {content}")
