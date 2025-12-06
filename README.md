# Security LLM Lab: AI-Powered SIEM Pilot

**Security LLM Lab** 是一個現代化的 AI-SOC 平台，展示如何將傳統 SIEM (日志管理、告警) 與先進的 Generative AI 技術 (RAG、Agent) 結合。本專案目前採用 Microservices 架構，並支援 Demo Mode 讓使用者快速體驗。

## 核心功能

### 1. 現代化 SIEM 核心
- **Elasticsearch Log Storage**: 高效能日誌儲存與搜尋。
- **PostgreSQL Alert DB**: 結構化的告警與事件管理資料庫。
- **FastAPI Backend**: 非同步、高效能的 REST API 服務。
- **React Frontend**: (開發中) 直觀的儀表板與操作介面。

### 2. AI 賦能 (Agentic Security)
- **Natural Language Query**: 讓資安分析師用自然語言 ("Show me failed logins from China") 查詢日誌，自動轉換為 Elasticsearch DSL。
- **RAG Knowledge Base**:
    - 使用 **Qdrant** 向量資料庫儲存資安知識 (如 MITRE ATT&CK 手冊、企業 Playbook)。
    - **Context-Aware Chat**: 聊天機器人會先查詢知識庫 ("How to mitigate T1059?") 再回答問題，減少幻覺。
- **Automated Threat Analysis**: 自動關聯高風險告警，並使用 LLM (Local Ollama 或 OpenAI) 提供根因分析與建議。

## 系統架構

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, LangChain
- **Database**: PostgreSQL 15, Qdrant (Vector DB)
- **Log Engine**: Elasticsearch 8.11
- **AI Engine**: Ollama (Local Llama 3) 或 OpenAI API

## 安裝與執行

### 先決條件
- Docker & Docker Compose
- (選用) Local LLM: 安裝 [Ollama](https://ollama.com/) 並執行 `ollama run llama3`

### 步驟 1: 啟動基礎設施
您可以直接使用自動化腳本啟動：

**Windows:**
```powershell
.\start.bat
```

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

或者手動使用 Docker Compose：

```bash
# 複製環境變數範本
cp .env.example .env

# 啟動服務 (Backend, Postgres, Elastic, Kibana, Qdrant)
docker-compose up --build -d
```

### 步驟 2: 設定環境變數 (.env)
編輯 `.env` 檔案以切換 Demo 模式或設定 API Key：

```ini
# 若為 true，系統啟動時會自動建立假資料 (Log/Alert)
DEMO_MODE=true

# AI 模型設定 (macor: ollama, openai)
LLM_BACKEND=ollama
# 若使用 OpenAI，請填入 Key
OPENAI_API_KEY=sk-...
```

## 使用與操作

### 系統介面
啟動後，您可以透過瀏覽器存取以下服務：

- **Frontend Dashboard**: `http://localhost:5173` (主要操作介面)
- **Backend API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Kibana**: `http://localhost:5601` (日誌視覺化)
- **Qdrant Dashboard**: `http://localhost:6333/dashboard` (向量資料庫管理)

### 範例操作
你可以使用 Swagger UI 或 Postman 測試以下 Agent 功能：

1. **聊天與查詢 (RAG + Logs)**
   - `POST /agent/chat`
   - Payload: `{"message": "How to mitigate Brute Force?", "model": "ollama"}`
     - -> 系統會查詢 Qdrant 並回傳 Mitigation 建議。
   - Payload: `{"message": "Find all alerts with severity high", "model": "ollama"}`
     - -> 系統會生成 Elastic Query 並回傳日誌。

2. **威脅分析**
   - `POST /agent/analyze`
   - 系統會抓取最新的 High Severity Alerts，並由 LLM 產生一份綜合分析報告。

3. **管理知識庫**
   - `POST /knowledge/`
   - Payload: `{"text": "Company Policy: Always block port 445.", "source": "Internal Wiki"}`
   - 讓 Agent 學習新的規則。

## 測試

專案包含完整的整合測試，涵蓋 Database, Elastic, 與 RAG 流程。

```bash
# 安裝測試依賴
pip install pytest httpx

# 執行測試
python -m pytest tests/test_api_integration.py -v
```

## 開發指南
- **Backend**: 位於 `security_llm_lab/`，主要邏輯在 `api/` 目錄。
- **Frontend**: 位於 `frontend/` (React + Vite)，啟動後位於 `http://localhost:5173`。
- **Logs**: 預設掛載於 `./logs`。

---
*Built for Security Researchers & AI Enthusiasts.*
