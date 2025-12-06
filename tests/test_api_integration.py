import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, patch, MagicMock

from security_llm_lab.api.main import app
from security_llm_lab.api.database import Base, get_db

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_alert(test_db):
    alert_data = {
        "title": "Test Alert",
        "severity": "high",
        "source": "pytest",
        "description": "This is a test alert",
        "raw_data": {"foo": "bar"}
    }
    response = client.post("/alerts/", json=alert_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Alert"
    assert data["id"] is not None
    assert data["status"] == "new"

def test_read_alerts(test_db):
    response = client.get("/alerts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Test Alert"

@patch("security_llm_lab.api.routers.agent.QueryGenerator")
@patch("security_llm_lab.api.routers.agent.search_logs", new_callable=AsyncMock)
def test_agent_chat_search(mock_search, mock_generator_class):
    # Mock LLM generation
    mock_generator_instance = mock_generator_class.return_value
    mock_generator_instance.generate_dsl = AsyncMock(return_value={"query": {"match_all": {}}})
    
    # Mock Elastic Search
    mock_search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"message": "Test log entry"}}
            ]
        }
    }
    
    response = client.post("/agent/chat", json={"message": "Find all logs", "model": "ollama"})
    assert response.status_code == 200, f"Status: {response.status_code}, Response: {response.text}"
    data = response.json()
    assert "Test log entry" in str(data["data"])
    assert "dsl" in data

@patch("security_llm_lab.api.routers.agent.ThreatAnalyzer")
def test_agent_analyze_threats(mock_analyzer_class, test_db):
    # Ensure there is a high priority alert
    alert_data = {
        "title": "Critical Incident",
        "severity": "high",
        "source": "pytest",
        "description": "Critical breach",
        "raw_data": {}
    }
    client.post("/alerts/", json=alert_data)

    # Mock Analyzer
    mock_analyzer_instance = mock_analyzer_class.return_value
    mock_analyzer_instance.analyze_alerts = AsyncMock(return_value="Analysis: It's bad.")

@patch("security_llm_lab.api.services.knowledge_base.knowledge_base")
def test_knowledge_base(mock_kb, test_db):
    # Mock add_document
    mock_kb.add_document.return_value = "doc-123" # qdrant upsert is synchronous usually, check method signature
    # Wait, add_document IS async in my implementation.
    mock_kb.add_document = AsyncMock(return_value="doc-123")

    # Test Ingest
    response = client.post("/knowledge/", json={"text": "MITRE T1059: Powershell", "source": "mitre"})
    assert response.status_code == 200
    assert response.json() == {"id": "doc-123", "status": "indexed"}

    # Mock Search
    mock_kb.search = AsyncMock(return_value=[{"text": "Powershell usage", "score": 0.9}])
    
    # Test Search API
    response = client.get("/knowledge/search?q=powershell")
    assert response.status_code == 200
    assert len(response.json()) == 1

@patch("security_llm_lab.api.services.knowledge_base.search_knowledge", new_callable=AsyncMock)
def test_agent_chat_rag(mock_search_know, test_db):
    # Mock RAG hit
    mock_search_know.return_value = [{"text": "To mitigate T1059, use AppLocker.", "score": 0.9}]
    
    response = client.post("/agent/chat", json={"message": "How to mitigate T1059?", "model": "ollama"})
    assert response.status_code == 200
    data = response.json()
    assert "Based on my knowledge base" in data["response"]
    assert "AppLocker" in data["response"]
