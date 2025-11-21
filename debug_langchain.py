import langchain.agents
print(f"Has initialize_agent: {hasattr(langchain.agents, 'initialize_agent')}")
print(f"Has AgentExecutor: {hasattr(langchain.agents, 'AgentExecutor')}")
