# Security LLM Lab

Security LLM Lab 提供一個端到端的範例，示範如何彙整本地與公開的資訊安全資料集、串接 SIEM 與 SOAR，再以 Retrieval-Augmented Generation (RAG) 與微調 (fine-tuning) 技術建置安全領域的語言模型。整體流程仿照 UTMStack 與 BackdoorLLM 等專案的設計精神，使用者可以依照實際環境調整。

## 功能

- **資料匯入**：支援 LogHub、CyberLLMInstruct 等開源資源，並能掃描本地端的情資與日誌檔案。
- **SIEM 與 SOAR 串接**：提供向 UTMStack、Wazuh 及其他相容 REST API 的 SIEM/SOAR 平台匯出事件的範例。
- **資料湖管理**：統一將資料轉換成標準化 schema，並儲存於工作目錄供後續訓練。
- **模型訓練**：使用 Hugging Face `transformers` 與 `datasets` 套件，提供微調大型語言模型的流程。
- **RAG 管線**：以 TF-IDF 檢索與向量化索引，支援檢索強化生成的查詢流程。

## 快速開始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python main.py init --workspace ./workspace
python main.py collect --config ./workspace/config.yaml
python main.py train --config ./workspace/config.yaml
python main.py rag-query --workspace ./workspace --question "How do I respond to a brute force attack?"
python main.py self-test --workspace ./workspace  # 產出合成事件並驗證 SIEM 連線
python main.py serve-ingest --workspace ./workspace --port 8080 --api-key change-me  # 啟動本地代理匯聚 API
```

## Docker 化部署

專案提供 `Dockerfile` 與 `docker-compose.yml`，方便在容器中啟動收集/訓練流程：

```bash
# 建立 .env 並設定 API keys、是否啟用 metrics
cp env.example .env

# 以 docker-compose 啟動資料收集（會掛載 workspace 目錄）
docker compose up --build

# 進入容器執行其他指令
docker compose run --rm security-llm-lab python main.py self-test --workspace /workspace
```

若要暴露 Prometheus metrics，設定 `.env` 中的 `ENABLE_PIPELINE_METRICS=1`，預設會在 `9000` 埠啟動 `start_http_server`。

## 設定檔

### 環境變數支援

為了提高安全性，API keys 可以通過環境變數設定，環境變數優先於配置檔中的值：

```bash
export SIEM_API_KEY=your_siem_api_key_here
export SOAR_API_KEY=your_soar_api_key_here
```

參考 `env.example` 檔案以了解可用的環境變數。

### `config.yaml` 範例

```yaml
workspace: ./workspace
local_sources:
  - path: /var/log
    glob: "**/*.log"
    metadata:
      source: local-log
siem:
  base_url: "https://utmstack.example/api"
  api_key: "YOUR_KEY"  # 可選：如果設定了 SIEM_API_KEY 環境變數則會被覆蓋
  verify_ssl: true
  default_index: "security-events"
soar:
  base_url: "https://soar.example/api"
  api_key: "YOUR_SOAR_KEY"  # 可選：如果設定了 SOAR_API_KEY 環境變數則會被覆蓋
rag:
  index_name: security-rag
training:
  model_name: "mistralai/Mistral-7B-Instruct"
  dataset_name: security_llm_lab/security_corpus
  max_steps: 1000
```

**注意：** 請勿將包含真實 API keys 的配置檔提交到版本控制系統。使用環境變數或 `.env` 檔案（已包含在 `.gitignore` 中）來管理敏感資訊。

## 與 UTMStack API 互動

Security LLM Lab 內建的 `UTMStackClient` 可以用來驗證連線、送出事件或將收集到的 JSONL 檔轉入 UTMStack：

```python
from security_llm_lab.integrations import UTMStackClient

client = UTMStackClient(
    base_url="https://utmstack.example/api",
    api_key="<your-api-key>",
    verify_ssl=True,
    default_index="security-events",
)

# 驗證 REST API 狀態
client.test_connection()

# 送出自定義事件
client.send_events([
    {"message": "demo event from SecurityLLMLab", "severity": "low"}
])
```

若要將資料管線產出的 JSONL 檔同步到 UTMStack，只要在 `config.yaml` 中設定 `siem` 區塊並執行 `python main.py collect --config ./workspace/config.yaml`，即可自動轉送。

## 與 Wazuh API 互動

`WazuhClient` 提供存取 [wazuh/wazuh](https://github.com/wazuh/wazuh) API 的基本範例，包括取得 token、列出 agent、查詢告警與送出測試事件：

```python
from security_llm_lab.integrations import WazuhClient

client = WazuhClient(
    base_url="https://wazuh.example:55000",
    username="wazuh-user",
    password="<password>",
    verify_ssl=False,  # 依需求啟用/關閉驗證
)

# 列出 agent 與查詢告警
agents = client.list_agents(limit=100)
alerts = client.search_alerts(query="rule.level:>=8", limit=50)

# 送出測試事件（會經由 /manager/logtest）
client.submit_logtest("demo event from SecurityLLMLab")
```

如果已有 Wazuh API token，也可以在初始化時以 `token="..."` 直接傳入，跳過 username/password 驗證。

## 匯聚本地 Agent 蒐集的情資

使用 `serve-ingest` 指令啟動簡易 HTTP API，讓其他本地 Agent 以 JSON 將事件推送到 Security LLM Lab 的工作目錄：

```bash
python main.py serve-ingest --workspace ./workspace --host 0.0.0.0 --port 8080 --api-key change-me
```

API 授權透過 `X-API-Key` 標頭控制（可選），端點為 `POST /ingest`，接受單筆或陣列的 JSON 物件，並自動寫入 `workspace/data_lake/ingest_api/ingested.jsonl` 供後續訓練或轉送至 SIEM：

```bash
curl -X POST "http://localhost:8080/ingest" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: change-me" \
  -d '{"message": "from local agent", "source": "endpoint-1"}'
```

在匯聚 API 後端即可使用 `DataPipeline` 或自訂流程讀取 `ingested.jsonl`，並利用 `UTMStackClient` 或 `WazuhClient` 將資料轉送到對應的 SIEM/SOAR 平台。

## 測試

專案包含基本單元測試，使用 pytest 執行：

```bash
# 安裝開發依賴
pip install -e ".[dev]"

# 執行所有測試
pytest

# 執行特定測試檔案
pytest tests/test_config.py

# 顯示詳細輸出
pytest -v
```

測試涵蓋：
- 配置載入與驗證
- 環境變數支援
- 資料管道錯誤處理
- 本地收集器功能

## 改進項目

本專案已實作以下改進：

### 安全性
- ✅ 環境變數支援 API keys（優先於配置檔）
- ✅ 配置驗證（URL、路徑、參數範圍）
- ✅ `.gitignore` 排除敏感檔案

### 錯誤處理
- ✅ 完善的異常處理（資料收集、訓練流程）
- ✅ 網路請求重試機制（指數退避）
- ✅ 失敗時清理不完整檔案
- ✅ 詳細的錯誤日誌

### 程式碼品質
- ✅ 修復已棄用的 `datetime.utcnow()` 使用
- ✅ 完整的型別提示
- ✅ 改進的日誌記錄

### 測試
- ✅ 基本單元測試覆蓋核心功能
- ✅ pytest 配置與測試結構
- ✅ 自我健檢指令（self-test）產生合成事件並可轉送至 SIEM
- ✅ Prometheus metrics（可選）與 Docker 化部署

## 重要說明

- 此專案提供的是參考範本，實際部署時請依環境與資安政策調整。
- 下載開源資料集時請確認授權條款並遵循資料保護與匿名化政策。
- 進行模型微調需具備足夠的硬體資源；若在 CPU 環境請調整批次大小或使用 LoRA 等技術。
- 使用環境變數管理敏感資訊，避免將 API keys 提交到版本控制系統。
