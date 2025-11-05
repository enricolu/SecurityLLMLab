# Security LLM Lab

Security LLM Lab 提供一個端到端的範例，示範如何彙整本地與公開的資訊安全資料集、串接 SIEM 與 SOAR，再以 Retrieval-Augmented Generation (RAG) 與微調 (fine-tuning) 技術建置安全領域的語言模型。整體流程仿照 UTMStack 與 BackdoorLLM 等專案的設計精神，使用者可以依照實際環境調整。

## 功能

- **資料匯入**：支援 LogHub、CyberLLMInstruct 等開源資源，並能掃描本地端的情資與日誌檔案。
- **SIEM 與 SOAR 串接**：提供向 UTMStack 及其他相容 REST API 的 SIEM/SOAR 平台匯出事件的範例。
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
```

## 設定檔

`config.yaml` 範例

```yaml
workspace: ./workspace
local_sources:
  - path: /var/log
    glob: "**/*.log"
    metadata:
      source: local-log
siem:
  base_url: "https://utmstack.example/api"
  api_key: "YOUR_KEY"
  verify_ssl: true
  default_index: "security-events"
soar:
  base_url: "https://soar.example/api"
  api_key: "YOUR_SOAR_KEY"
rag:
  index_name: security-rag
training:
  model_name: "mistralai/Mistral-7B-Instruct"
  dataset_name: security_llm_lab/security_corpus
  max_steps: 1000
```

## 重要說明

- 此專案提供的是參考範本，實際部署時請依環境與資安政策調整。
- 下載開源資料集時請確認授權條款並遵循資料保護與匿名化政策。
- 進行模型微調需具備足夠的硬體資源；若在 CPU 環境請調整批次大小或使用 LoRA 等技術。
