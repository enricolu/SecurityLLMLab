"""Logic for generating security rules using LLMs."""

from typing import Optional
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

from security_llm_lab.config import AppConfig
from security_llm_lab.llm_client import get_llm_client

SIGMA_PROMPT = """You are an expert detection engineer. Your task is to write a Sigma rule based on the following description.

Description: {description}

Return ONLY the YAML content of the Sigma rule. Do not include markdown backticks or explanations.
"""

SPLUNK_PROMPT = """You are an expert detection engineer. Your task is to write a Splunk SPL query based on the following description.

Description: {description}

Return ONLY the SPL query string. Do not include markdown backticks or explanations.
"""

class RuleGenerator:
    def __init__(self, config: AppConfig):
        self.llm_client = get_llm_client(config.llm)

    def generate_sigma(self, description: str) -> str:
        """Generate a Sigma rule from a description."""
        llm = self.llm_client.get_chat_model()
        prompt = PromptTemplate.from_template(SIGMA_PROMPT)
        message = prompt.format(description=description)
        
        response = llm.invoke([HumanMessage(content=message)])
        return response.content.strip()

    def generate_splunk(self, description: str) -> str:
        """Generate a Splunk query from a description."""
        llm = self.llm_client.get_chat_model()
        prompt = PromptTemplate.from_template(SPLUNK_PROMPT)
        message = prompt.format(description=description)
        
        response = llm.invoke([HumanMessage(content=message)])
        return response.content.strip()
