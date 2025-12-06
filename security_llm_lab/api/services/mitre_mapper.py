from langchain_core.prompts import PromptTemplate
from ...config import LLMConfig
from ...llm_client import get_llm_client
import json

class MitreMapper:
    def __init__(self, backend: str = "ollama", model_name: str = "llama3"):
        config = LLMConfig(backend=backend, model_name=model_name)
        self.client = get_llm_client(config)
        self.llm = self.client.get_chat_model()
        
        self.prompt = PromptTemplate(
            input_variables=["description"],
            template="""You are an expert in MITRE ATT&CK Framework.
            Analyze the following security event description and return the most relevant MITRE ATT&CK Technique ID and Name.
            Return ONLY the JSON object.
            
            Description: {description}
            
            JSON format: {{ "technique_id": "Txxxx", "technique_name": "Technique Name", "confidence": "high/medium/low", "justification": "short reason" }}
            """
        )

    async def map_to_mitre(self, description: str) -> dict:
        formatted_prompt = self.prompt.format(description=description)
        response = self.llm.invoke(formatted_prompt)
        content = response.content.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        try:
            return json.loads(content)
        except json.JSONDecodeError:
             return {"technique_id": "Unknown", "technique_name": "Unknown", "error": "Failed to parse LLM response"}
