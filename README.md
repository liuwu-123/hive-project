# Yundu Life — Enterprise Data Warehouse & Analytics System

An end-to-end data platform for a fictional new-retail company: from raw CSV ingestion to a four-layer Hive data warehouse, time-series forecasting, natural-language-to-SQL (NL2SQL) querying, interactive dashboards and one-command deployment.

> Course project · Team **Cloud Warehouse No.5** · 5-week delivery cycle
> Chinese documentation: [README.zh-CN.md](README.zh-CN.md)

---

## Highlights

| Metric | Value |
|---|---|
| Raw data ingested | **114,809 rows** across 6 business tables |
| Data quality issues fixed | **16 metrics, 14 at 100% repair rate** |
| Warehouse layers | ODS → DWD → DWS → ADS (4 business dims + 7 enum dims + 3 fact tables) |
| Core KPI | GMV **¥36,116,687.06**, 14,398 orders, AOV **¥2,508.45** |
| NL2SQL accuracy | **10/10** test questions, ~5.9 s average end-to-end |
| End-to-end rebuild | **3.2 minutes** from CSV to a BI-ready MySQL mart |
| Services orchestrated | **6 containers** with health checks |

---

## Architecture

```
┌─────────────┐   ┌──────────────┐   ┌─────────────┐   ┌──────────────┐
│     ODS     │──▶│     DWD      │──▶│     DWS     │──▶│     ADS      │
│ raw import  │   │ clean + star │   │ aggregated  │   │ KPI / top-N  │
│  6 tables   │   │4 dim+3 fact  │  │  5 tables   │   │  5 tables    │
└─────────────┘   └──────────────┘   └─────────────┘   └──────┬───────┘
                                                              │ sync
        ┌─────────────────────────────────────────────────────┘
        ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ MySQL mart   │──▶│  Superset    │   │   ECharts    │   │  Streamlit   │
│  (BI mart)   │   │  dashboard   │   │  big screen  │   │  NL2SQL chat │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                                          ▲
                       ┌──────────────────┴──────────────────┐
                       │ Forecasting (scikit-learn) ·        │
                       │ AI insight (DeepSeek API)           │
                       └─────────────────────────────────────┘
```

**Why a MySQL mart?**
Superset cannot reach Hive without `pyhive + thrift + sasl`, and `sasl` needs a C toolchain that often fails inside containers. Hive therefore stays the compute layer, while aggregated results are synced into MySQL for the BI layer — mirroring how production systems separate compute from serving.

---

## Features

### Data engineering
- 6 raw CSVs → Hive tables (header skipped, comma-separated, ORC storage)
- Two-stage enum normalisation: `map_*` lookup tables → `dim_*` dimensions (7 mapping sets)
- Anomaly handling: negative amounts, extreme values (>¥100k), malformed dates and phone numbers
- Star schema: `dim_user / dim_product / dim_store / dim_date` plus `fact_order / fact_order_item / fact_behavior`
- Monthly partitioning (12 partitions) and bucketing (8 buckets on `order_id`)

### Analytics & ML
- DWS aggregates by day / month × store / channel / category
- ADS KPI layer: GMV, orders, AOV, active users, repurchase, user value tiers
- Time-series diagnosis (ACF, trend, weekday effect) followed by forecasting; the random forest reaches **MAPE 11.87% against an 11.93% mean baseline**, and the report states plainly that the series behaves like white noise
- AI insight: programmatic z-score anomaly detection feeds an LLM that may only cite facts supplied to it

### AI / NL2SQL
- Automatic Hive schema extraction (16 tables) injected into the prompt
- Guarded execution: `SELECT`-only whitelist, `ydsh_*` prefix check, one automatic retry that feeds the error back to the model
- CLI: `python -m nl2sql.main "2024 年 6 月 GMV 最高的前 3 家门店"`
- Web: Streamlit chat showing generated SQL, result table and an auto-selected chart

### Visualisation & deployment
- **Superset** dashboard: trend, category, payment pie, store top-10, monthly and province charts
- **ECharts** 1920×1080 big screen with `transform: scale()` responsive layout, China map, heatmap and scatter
- **Docker Compose**: 6 services, health checks, secrets injected through `.env`

---

## Quick start

```bash
git clone https://github.com/liuwu-123/hive-project.git
cd hive-project

# 1. secrets (never commit this file)
cat > .env <<'EOF'
DEEPSEEK_API_KEY=sk-xxxxxxxx
SUPERSET_SECRET_KEY=<40 random characters>
EOF

# 2. start all services
docker compose up -d
docker compose ps

# 3. first-run initialisation (once)
docker exec hive-project-superset-1 superset db upgrade
docker exec hive-project-superset-1 superset fab create-admin \
  --username admin --firstname Admin --lastname User \
  --email admin@example.com --password admin123
docker exec hive-project-superset-1 superset init

# 4. rebuild the warehouse from raw CSV (≈3 minutes)
powershell -ExecutionPolicy Bypass -File scripts/rebuild_end2end.ps1
```

| Service | URL | Credential |
|---|---|---|
| Superset dashboard | http://localhost:8088 | admin / admin123 |
| ECharts big screen | http://localhost:5000 | — |
| Streamlit NL2SQL chat | http://localhost:8501 | — |
| HiveServer2 (JDBC) | `jdbc:hive2://localhost:10000/` | — |
| MySQL mart | `localhost:3306` | root / root |

---

## Tech stack

| Layer | Technology |
|---|---|
| Storage & compute | Apache Hive 4.0.0, Tez, HDFS (container), ORC |
| Metadata | MySQL 8.0 |
| BI mart | MySQL 8.0 (`ydsh_ads`) |
| Analytics / ML | Python 3.12, pandas, scikit-learn, matplotlib |
| LLM integration | DeepSeek Chat API (OpenAI-compatible) with a hand-written JSON guard |
| Visualisation | Apache Superset 3.1, ECharts 5.5, Streamlit |
| Orchestration | Docker Compose v2, PowerShell automation |

---

## Project structure

```
.
├── sql/
│   ├── ods/            # create and load raw tables
│   ├── clean/          # enum mapping, dimensions, quality comparison
│   ├── dwd/            # fact tables and EDA
│   ├── dws/            # daily / monthly aggregates
│   ├── ads/            # KPI and top-N application tables
│   └── mysql/          # generated BI-mart init script
├── sync/               # Hive to MySQL mart synchronisation
├── analysis/           # time-series diagnosis and forecasting
├── nl2sql/             # schema loader, prompts, guard, CLI, test suite
├── insight/            # AI anomaly attribution and report generation
├── superset/           # image, config, dataset and chart bootstrap scripts
├── web/                # Flask API and ECharts big screen
├── app/                # Streamlit NL2SQL application
├── bench/              # concurrent stress test
├── tools/              # consistency workbook, CDP screenshot helpers
├── scripts/            # rebuild_end2end.ps1 and friends
└── docs/               # reports (zh-CN), screenshots, KPI workbook
```

---

## Documentation (Chinese)

| Document | Content |
|---|---|
| `docs/需求文档.docx` | Business background, requirements, KPI definitions |
| `docs/数据质量对比报告.docx` | Five quality dimensions, 16 metrics, repair rates |
| `docs/数仓架构设计文档.docx` | Four-layer design, star schema, technology choices |
| `docs/预测建模分析报告.docx` | ACF diagnosis, model comparison, 7-day forecast, limits |
| `docs/第3周_AI经营分析摘要.docx` | AI attribution with a verification log |
| `docs/第3周_AI应用反思.docx` | Three real failures, AI limits, improvements |
| `docs/第4周_部署手册.docx` | Deployment steps, troubleshooting, demo script |
| `docs/第4周_API配置指南.docx` | Secret management, rotation, least privilege |
| `docs/第4周_查询优化记录.docx` | Partition pruning evidence (−92.3% rows scanned) |
| `docs/第4周_压测记录.docx` | Concurrency results at 10 / 20 / 50 |
| `docs/第5周_数据一致性核对表.xlsx` | 23-table row counts, KPI reconciliation |

---

## Verification

```bash
# row counts across 23 tables (≈20 s)
powershell -ExecutionPolicy Bypass -File scripts/rebuild_end2end.ps1 -VerifyOnly

# NL2SQL accuracy on 10 questions
.\.venv\Scripts\python.exe -m nl2sql.tests

# concurrency test
.\.venv\Scripts\python.exe bench\stress_test.py
```

---

## Known limitations

- The dataset is synthetic and uniformly distributed, so the repurchase rate saturates at 100% and daily GMV behaves close to white noise. Both facts are documented rather than hidden.
- `fact_order_item` sums to roughly 14× the order GMV because the detail table carries pre-discount prices; the two calibres are never mixed in reports.
- Superset connects to the MySQL mart rather than Hive directly (see the architecture note).
- The Streamlit container mounts the Docker socket so it can call `beeline`; production deployments should use a JDBC connection pool instead.

---

## Team

**Cloud Warehouse No.5** — Liu Yixuan (data engineering & analytics), Zhang Yebin, Yan Hongwei, Chai Chuanxing, Deng Kechao.

## License

Released for coursework and portfolio purposes. The synthetic dataset contains no real customer information.
