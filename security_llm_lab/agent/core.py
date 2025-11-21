"""Core logic for the Security Agent."""

import re
from typing import List, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from security_llm_lab.config import AppConfig
from security_llm_lab.llm_client import get_llm_client
from security_llm_lab.agent.tools import get_tools

# Default React Prompt
REACT_PROMPT = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:"""

class SecurityAgent:
    def __init__(self, config: AppConfig):
        self.config = config
        self.llm_client = get_llm_client(config.llm)
        self.tools = get_tools(config)
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.max_iterations = config.agent.max_iterations

    def run(self, query: str) -> str:
        """Run the agent with the given query using a manual ReAct loop."""
        llm = self.llm_client.get_chat_model()
        
        tool_desc = "\n".join([f"{t.name}: {t.description}" for t in self.tools])
        tool_names = ", ".join([t.name for t in self.tools])
        
        prompt = PromptTemplate.from_template(REACT_PROMPT)
        formatted_prompt = prompt.format(
            tools=tool_desc,
            tool_names=tool_names,
            input=query
        )
        
        history = formatted_prompt
        
        for _ in range(self.max_iterations):
            # Call LLM
            response = llm.invoke([HumanMessage(content=history)])
            output = response.content
            history += output
            
            # Parse Action
            action_match = re.search(r"Action: (.*?)\nAction Input: (.*)", output, re.DOTALL)
            if "Final Answer:" in output:
                return output.split("Final Answer:")[-1].strip()
            
            if action_match:
                action = action_match.group(1).strip()
                action_input = action_match.group(2).strip().split("\n")[0] # Take only the first line of input
                
                observation = f"\nObservation: Error: Tool '{action}' not found."
                if action in self.tool_map:
                    try:
                        tool_result = self.tool_map[action].invoke(action_input)
                        observation = f"\nObservation: {tool_result}"
                    except Exception as e:
                        observation = f"\nObservation: Error executing tool: {e}"
                
                history += observation + "\nThought:"
            else:
                # If no action found but no final answer, force a thought or stop
                if "Thought:" not in output:
                     history += "\nThought:"
                else:
                     # Maybe the model just stopped generating?
                     pass

        return "Agent stopped due to max iterations."
