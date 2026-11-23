# -*- coding: utf-8 -*-
"""第 5 周：在现有《数仓架构设计文档》后追加 AI 层、可视化层、部署架构与技术取舍。"""
from docx import Document
from docx.shared import Pt

PATH = r"E:\hive-project\docs\数仓架构设计文档.docx"
doc = Document(PATH)

# 更新标题为终版
for p in doc.paragraphs:
    if p.style.name == "Title":
        for r in p.runs:
            r.text = ""
        p.runs[0].text = "架构设计文档（第 5 周终版）"
        break

H1 = "Heading 1"


def h1(text):
    doc.add_paragraph(text, style=H1)


def para(text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(4)
    return p


def bullet(text):
    doc.add_paragraph(text, style="List Bullet")


def table(header, rows):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Light Grid Accent 1"
    for j, h in enumerate(header):
        c = t.rows[0].cells[j]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
    for row in rows:
        cells = t.add_row().cells
        for j, v in enumerate(row):
            cells[j].text = str(v)
    doc.add_paragraph()


h1("七、AI 层设计")
para("AI 层位于数仓之上，包含两个能力：NL2SQL 自然语言查询、经营异常归因。两者共用同一个大模型客户端，"
     "但数据来源不同——前者直连 Hive 执行 SQL，后者只读取由 SQL 产出的事实清单。")

para("7.1 NL2SQL 链路", )
bullet("① Schema 抽取：对 16 张表执行 describe，得到字段名、类型、注释，缓存为 schema.json")
bullet("② Prompt 组装：系统提示词包含 Schema 描述、业务口径（amount_invalid=0 等）、3 个 few-shot 示例")
bullet("③ 模型生成：要求只输出 JSON（sql + reason），temperature=0 保证稳定")
bullet("④ 安全校验：只允许 SELECT、表名必须带 ydsh_ 前缀、禁止写操作关键字")
bullet("⑤ 执行：通过 docker exec beeline 提交 HiveServer2，结果解析为表头 + 行数据")
bullet("⑥ 容错：执行失败时把报错回传给模型重试一次，仍失败则返回错误")

para("7.2 AI 洞察链路")
bullet("① 程序先算事实：Hive 取 KPI、按 z-score 检测日 GMV 异常（|z| ≥ 2）")
bullet("② 事实清单序列化为 JSON，作为唯一信息来源交给模型")
bullet("③ Prompt 约束：只能引用清单中的数字，禁止引入外部信息，无法解释时必须写“数据不足”")
bullet("④ 输出经营分析摘要，并附人工验证记录表（数字一致性、外部信息、因果支撑、绝对化表述）")

para("7.3 为什么把“算数”和“表达”分开")
para("模型不参与任何数值计算：指标由 SQL 算出，异常由 z-score 判定，模型只负责组织语言。"
     "这样报告中的每个数字都能回溯到一条查询，避免模型编造数据。实测中模型确实主动写出了"
     "“现有数据不足以判断原因”，印证了约束有效。")

h1("八、可视化层设计")
para("可视化分三层，分别服务不同场景，共用同一份 MySQL 集市数据。")

table(["层次", "技术", "服务对象", "特征"],
      [["自助分析", "Apache Superset", "分析师 / 管理者", "可筛选、可下钻、图表自助配置"],
       ["固定大屏", "ECharts + Flask", "展厅 / 汇报现场", "1920×1080 设计稿，等比缩放，离线可用"],
       ["对话式问答", "Streamlit + NL2SQL", "非技术同事", "中文提问，返回 SQL、表格与图表"]])

para("8.1 为什么 Superset 不直连 Hive")
para("Superset 连接 Hive 需要 pyhive + thrift + sasl，其中 sasl 依赖 C 编译环境，在容器内构建失败率高；"
     "因此本项目的做法是：Hive 负责计算，ADS/DWS 结果同步到 MySQL，Superset 直连 MySQL。"
     "这既是工程上的稳妥选择，也符合“计算与 Serving 分离”的常见架构。")

para("8.2 大屏自适应方案")
para("按 1920×1080 设计稿绝对布局，通过 transform: scale() 整体缩放并居中，窗口任意尺寸都不错位。"
     "相比逐图表响应式，方案实现简单、视觉效果稳定。ECharts 与地图 JSON 均本地化，断网可演示。")

h1("九、部署架构")
para("全部服务通过 Docker Compose 编排，共 6 个容器，4 个配置健康检查。")

table(["服务", "端口", "职责", "依赖", "健康检查"],
      [["mysql", "3306", "BI 集市（ydsh_ads）+ Superset 元数据", "—", "mysqladmin ping"],
       ["hive-metastore", "9083", "Hive 元数据服务", "mysql", "—"],
       ["hive-server", "10000", "HiveServer2，beeline 入口", "hive-metastore", "—"],
       ["superset", "8088", "仪表板", "mysql（healthy）", "/health"],
       ["web", "5000", "ECharts 大屏 + Flask 数据接口", "mysql（healthy）", "/api/kpi"],
       ["app", "8501", "Streamlit 问答（调用 beeline）", "hive-server, web", "/healthz"]])

para("9.1 启动顺序控制")
para("mysql 健康后才启动 hive-metastore、superset 与 web；app 依赖 hive-server 与 web。"
     "健康检查间隔 15~20 秒，避免“容器 Up 但服务未就绪”的假成功。")

para("9.2 密钥与配置")
para("DEEPSEEK_API_KEY 与 SUPERSET_SECRET_KEY 存放于 .env，通过 env_file 注入容器；"
     "compose 文件中只出现 ${VAR} 引用，不写明文。.env 已在 .gitignore 中，且用 git check-ignore 验证。")

h1("十、技术选型与取舍")
table(["决策点", "选择", "放弃的方案", "原因"],
      [["计算引擎", "Hive 4.0 + Tez", "Spark / ClickHouse", "课程环境已具备，SQL 生态成熟；数据量 11 万行无需分布式"],
       ["存储格式", "ORC", "Text / Parquet", "列裁剪 + 压缩，Hive 原生支持好"],
       ["BI 连接方式", "MySQL 集市", "Superset 直连 Hive", "sasl 编译失败率高，集市更稳定且快"],
       ["分区粒度", "按月 12 分区", "按天 366 分区", "内嵌 Derby 元数据无法承载 366 分区（实测报 savepoint 回滚）"],
       ["预测模型", "线性回归 + 随机森林", "XGBoost / LSTM", "数据量小、特征少，复杂模型无收益；且已证明序列接近白噪声"],
       ["大屏方案", "原生 ECharts", "Superset 内置图表", "需要地图、热力等复杂图表与统一视觉设计"],
       ["问答界面", "Streamlit", "Vue/React 自研", "一天内可交付，聚焦 NL2SQL 能力本身"]])

h1("十一、演进方向")
bullet("计算层：数据量增长后迁移到 Spark，元数据换成独立 MySQL 实例")
bullet("调度：引入 DolphinScheduler/Airflow，把 rebuild_end2end 的步骤编排为 DAG")
bullet("实时：新增 Kafka + Flink 链路，支撑实时大屏")
bullet("NL2SQL：支持多轮上下文与查询结果追问（已登记 Issue #2）")
bullet("治理：补充数据血缘与指标血缘，做到“指标可溯源到字段”")

doc.save(PATH)
print("架构文档已追加，当前段落数:", len(doc.paragraphs), "表格数:", len(doc.tables))
