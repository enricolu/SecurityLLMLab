from langchain_core.prompts import PromptTemplate
from ...config import LLMConfig
from ...llm_client import get_llm_client
from typing import List

class ThreatAnalyzer:
    def __init__(self, backend: str = "ollama", model_name: str = "llama3"):
        config = LLMConfig(backend=backend, model_name=model_name)
        self.client = get_llm_client(config)
        self.llm = self.client.get_chat_model()
        
        self.prompt = PromptTemplate(
            input_variables=["alerts"],
            template="""You are an expert Security Analyst (SOC Tier 3).
            Analyze the following list of alerts for potential correlation and identifying the root cause of a possible attack.
            
            Alerts:
            {alerts}
            
            Provide a concise analysis in markdown format:
            1. **Summary**: What is happening?
            2. **Correlation**: How are these alerts related? (e.g., same host, user, or attack chain)
            3. **Root Cause Hypothesis**: What started this?
            4. **Recommendations**: 3 key actions to take.
            """
        )

    async def analyze_alerts(self, alerts: List[dict]) -> str:
        # Format alerts for the prompt
        alerts_text = ""
        for alert in alerts:
            alerts_text += f"- [{alert.get('created_at')}] {alert.get('title')} (Sev: {alert.get('severity')}) on {alert.get('source')}\n"
            
        formatted_prompt = self.prompt.format(alerts=alerts_text)
        response = self.llm.invoke(formatted_prompt)
        return response.content
