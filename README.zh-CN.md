# 云购生活 —— 企业级数据仓库与经营分析可视化系统

面向新零售企业的端到端数据平台：原始 CSV 接入 → 四层 Hive 数仓 → 时间序列预测 → NL2SQL 自然语言查询 → 可视化看板 → 一键部署。

> 课程项目 · 团队 **云仓五号** · 五周交付
> English version: [README.md](README.md)

---

## 项目亮点

| 指标 | 数值 |
|---|---|
| 接入原始数据 | 6 张业务表共 **114,809 行** |
| 数据质量问题 | **16 项指标，14 项修复率 100%** |
| 数仓分层 | ODS → DWD → DWS → ADS（4 业务维表 + 7 枚举维表 + 3 事实表） |
| 核心 KPI | GMV **3,611.67 万元**、14,398 单、客单价 **2,508.45 元** |
| NL2SQL 准确率 | **10/10**，端到端平均 5.95 秒 |
| 端到端重建 | 从 CSV 到 BI 可用 **3.2 分钟** |
| 编排服务 | **6 个容器**，4 个带健康检查 |

---

## 架构

```
ODS（贴源） → DWD（清洗+星型建模） → DWS（汇总） → ADS（指标/排行）
                                                        │ 同步
                                                        ▼
                                                  MySQL BI 集市
                                                        │
                        ┌───────────────┬───────────────┴──────────┐
                        ▼               ▼                          ▼
                   Superset         ECharts 大屏              Streamlit 问答
                   仪表板            自适应大屏                 NL2SQL 闭环
```

**为什么加 MySQL 集市**：Superset 直连 Hive 需要 `pyhive + thrift + sasl`，`sasl` 需 C 编译，容器内失败率高。因此 Hive 负责计算，MySQL 负责服务 BI——这也是真实企业的分层做法。

---

## 功能清单

| 模块 | 内容 |
|---|---|
| 数据接入 | 6 个 CSV 建表导入，ORC 存储，行数校验全通过 |
| 数据治理 | 枚举标准化（7 组映射表）、异常金额、日期/手机号/时间格式、去重 |
| 数仓建模 | 星型模型，事实表按月分区、明细表分 8 桶 |
| 汇总与应用 | 5 张 DWS 汇总表 + 5 张 ADS 应用表 |
| 预测建模 | ACF 诊断 + 线性回归/随机森林对比 + 7 天预测 + 边界说明 |
| NL2SQL | Schema 抽取 + Prompt 约束 + 白名单校验 + 自动重试 |
| AI 洞察 | 程序化异常检测 + 大模型归因 + 逐条验证记录 |
| 可视化 | Superset 6 图仪表板、ECharts 6 类图表大屏（含中国地图） |
| 部署 | 6 服务 Compose 编排、健康检查、密钥注入 |
| 工程 | 压测脚本、查询优化记录、CDP 自动截图工具 |

---

## 快速开始

```bash
git clone https://github.com/liuwu-123/hive-project.git
cd hive-project

# 1. 密钥（不要提交 Git）
cat > .env <<'EOF'
DEEPSEEK_API_KEY=sk-xxxxxxxx
SUPERSET_SECRET_KEY=<40 位随机字符串>
EOF

# 2. 启动全部服务
docker compose up -d
docker compose ps

# 3. 首次初始化 Superset（仅一次）
docker exec hive-project-superset-1 superset db upgrade
docker exec hive-project-superset-1 superset fab create-admin \
  --username admin --firstname Admin --lastname User \
  --email admin@example.com --password admin123
docker exec hive-project-superset-1 superset init

# 4. 从原始 CSV 重建整个数仓（约 3 分钟）
powershell -ExecutionPolicy Bypass -File scripts/rebuild_end2end.ps1
```

| 服务 | 地址 | 账号 |
|---|---|---|
| Superset 仪表板 | http://localhost:8088 | admin / admin123 |
| ECharts 大屏 | http://localhost:5000 | — |
| Streamlit 问答 | http://localhost:8501 | — |
| HiveServer2 | `jdbc:hive2://localhost:10000/` | — |
| MySQL 集市 | `localhost:3306` | root / root |

---

## 技术栈

| 层次 | 技术 |
|---|---|
| 存储与计算 | Apache Hive 4.0.0、Tez、ORC |
| 元数据 | MySQL 8.0 |
| BI 集市 | MySQL 8.0（`ydsh_ads`） |
| 分析与建模 | Python 3.12、pandas、scikit-learn、matplotlib |
| 大模型接入 | DeepSeek Chat API（OpenAI 兼容）+ 自研 JSON 校验 |
| 可视化 | Apache Superset 3.1、ECharts 5.5、Streamlit |
| 编排 | Docker Compose v2、PowerShell 自动化 |

---

## 目录结构

```
sql/          ODS/清洗/DWD/DWS/ADS 各层脚本 + MySQL 初始化
sync/         Hive → MySQL 集市同步
analysis/     时间序列诊断与预测
nl2sql/       Schema 抽取、Prompt、校验、CLI、测试集
insight/      AI 异常归因与报告生成
superset/     镜像、配置、数据集与图表初始化脚本
web/          Flask 接口 + ECharts 大屏
app/          Streamlit 问答应用
bench/        并发压测
tools/        一致性核对表生成、CDP 截图工具
scripts/      rebuild_end2end.ps1 等自动化脚本
docs/         各周文档、截图、KPI 结果表
```

---

## 团队分工

| 角色 | 姓名 | 职责 |
|---|---|---|
| 项目经理 / 数据开发 | 刘祎炫 | 数仓建模、KPI、预测、NL2SQL、可视化、部署、文档 |
| 环境与运维 | 张业彬 | Docker/Hive 环境、容器排障、配色与文档校对 |
| 数据接入 | 闫洪伟 | ODS 建表导入、指标口径讨论、图表选型 |
| 数据分析 | 柴传兴 | 数据质量评估、清洗策略、压测方案 |
| 可视化 | 邓克超 | 看板与大屏设计、部署手册排错、答辩串词 |

---

## 已知局限

- 数据集为合成均匀分布，复购率饱和在 100%、日 GMV 近似白噪声，文档中如实说明，不掩盖。
- 明细表 `item_amount` 合计约为订单 GMV 的 14 倍（原价与实付口径不同），报告中两者不混用。
- Superset 连的是 MySQL 集市而非 Hive（原因见架构说明）。
- Streamlit 容器挂载了 Docker socket 以调用 beeline，生产环境应改用 JDBC 连接池。

---

## 许可

仅用于课程与作品集展示；数据为合成数据，不含任何真实客户信息。
