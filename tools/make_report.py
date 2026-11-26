# -*- coding: utf-8 -*-
"""生成《企业项目实战实训报告》：填封面 + 写正文（宋体小四，1.5 倍行距）。"""
import copy

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Pt, Cm

SRC = r"E:\dssgz\report_src.docx"
OUT = r"E:\dssgz\企业项目实战实训报告_刘祎炫.docx"

doc = Document(SRC)

# ---------- 1. 填封面 ----------
fill = {
    "题   目：": "题   目：云购生活——企业级数据仓库与经营分析可视化系统",
    "学生姓名：": "学生姓名：刘祎炫",
    "学   院：": "学   院：青岛城市学院",
    "班   级：": "班   级：数据科学与大数据技术 2023 级",
    "年    月   日": "2026 年 11 月",
}
for p in doc.paragraphs:
    t = p.text.strip()
    if t in fill:
        for r in list(p.runs):
            r.text = ""
        run = p.runs[0] if p.runs else p.add_run()
        run.text = fill[t]

# 删除模板里的说明行（1000字提示与内容要求）
for p in list(doc.paragraphs):
    if p.text.strip().startswith("1000字") or p.text.strip().startswith("内容："):
        p._element.getparent().remove(p._element)

# ---------- 2. 正文样式 ----------
normal = doc.styles["Normal"]
normal.font.name = "宋体"
normal.font.size = Pt(12)          # 小四
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")


def para(text, indent=True, align=None, size=12, bold=False, space_after=0, first_line=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(space_after)
    pf.first_line_indent = Cm(0.85) if indent else Cm(0)
    if first_line is not None:
        pf.first_line_indent = Cm(first_line)
    if align:
        p.alignment = align
    r = p.add_run(text)
    r.font.name = "宋体"
    r.font.size = Pt(size)
    r.bold = bold
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    return p


def h(text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_before = Pt(10)
    pf.space_after = Pt(4)
    r = p.add_run(text)
    r.font.name = "宋体"
    r.font.size = Pt(14)
    r.bold = True
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    return p


# 分页，正文从新页开始
doc.add_page_break()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("企业项目实战实训报告")
r.font.name = "宋体"
r.font.size = Pt(16)
r.bold = True
r._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

# ---------- 3. 正文 ----------
h("一、项目概述")
para("本次实训以「云购生活」这家虚构的新零售企业为背景，目标是把它分散在各处的业务数据，"
     "建设成一套可复用、可追溯、可展示的数据仓库与分析系统。项目周期为五周，从环境搭建开始，"
     "依次完成原始数据接入、数据质量治理、四层数仓建模、探索性分析、预测建模、自然语言查询、"
     "可视化看板与容器化部署，最终交付一套能用一条命令复现的完整系统。")
para("交付物的最终形态是：六个容器组成的运行环境、二十三次提交的代码仓库、"
     "二十三张数仓表、六项核心指标、一份预测报告、一个自然语言查询接口、"
     "一个仪表板加一块数据大屏，以及一套从原始 CSV 到可视化三分钟重建的脚本。")

h("二、学习到的知识")
para("第一，理解了分层的意义。 ODS、DWD、DWS、ADS 四层并不是为了好看，"
     "而是让「口径」有唯一的落点。原始数据进 ODS 保持原样，清洗与建模放在 DWD，"
     "汇总放 DWS，面向业务的指标放 ADS。这样任何一张报表上的数字，都能沿着分层往回追到具体字段。")
para("第二，掌握了 Hive 的实用技能。包括外部表与分区表建表、ORC 列式存储、"
     "按订单号分桶、窗口函数做去重与累计、动态分区写入，以及用 explain 看执行计划来验证分区裁剪是否生效。")
para("第三，建立了「指标口径先定义」的习惯。同样是 GMV，含不含退款、含不含异常订单，"
     "结果能差一倍。项目中我把九个指标的口径写成了文档，并规定所有金额指标必须带有效订单过滤条件，"
     "这条规则后来在每一次复算中都省了大量沟通。")
para("第四，学会了把大模型用在「表达」而不是「计算」上。自然语言查询由模型生成 SQL，"
     "但数值一律由数据库算出；经营洞察也先由程序算好事实清单，再交给模型组织语言。"
     "这样报告里每个数字都能回溯到一条查询。")
para("第五，补上了工程化的一课。包括 Docker Compose 编排多服务与健康检查、"
     "密钥用环境变量注入、Git 分支与 Pull Request 协作、以及把手工步骤写成可重复执行的脚本。")

h("三、项目实施过程")
para("第一周搭建环境并接入数据。在 Windows 上用 Docker 部署了 Hive、MySQL 与元数据服务，"
     "解决了端口占用、镜像启动失败等问题，最终把六张业务表共十一万五千行数据导入 ODS 层，"
     "并做了行数校验。")
para("第二周做数据质量治理与建模。按完整性、唯一性、有效性、一致性、准确性五个维度扫描，"
     "定位了三十九项问题；完成十六项清洗指标，其中十四项修复率达到百分之百。"
     "随后建立星型模型，四张维度表加三张事实表，事实表按月分十二个区，明细表按订单号分八个桶。")
para("第三周建设汇总层与应用层并引入 AI。产出五张 DWS 汇总表与五张 ADS 应用表，"
     "算出 GMV 三千六百一十一万、订单一万四千三百九十八单、客单价两千五百零八元。"
     "同时完成时间序列预测与自然语言查询接口，后者用十个典型问题测试，全部通过。")
para("第四周做可视化与部署。把汇总结果同步到 MySQL 集市，用 Superset 做了六张图表的仪表板；"
     "用 ECharts 做了一块含折线、柱状、饼图、地图、散点与热力图的数据大屏；"
     "把自然语言查询接进 Streamlit 做成对话界面；最后用 Compose 编排六个服务，配健康检查。")
para("第五周整合与收尾。编写了端到端重建脚本，把「原始 CSV 到 BI 可用」压缩到三分半钟，"
     "并在结束时自动核对二十三张表的行数；补齐需求文档与架构设计文档，"
     "重写英文说明文档，整理提交历史与分支，最后完成答辩材料。")

h("四、遇到的难点与克服")
para("难点一：服务重启后数据服务起不来。 Hive 服务重启时因为残留的进程号文件，"
     "误判自己已在运行而直接退出。排查后把进程号目录改到临时文件系统上，"
     "容器每次启动该目录都是空的，问题彻底消失，并且重启后数据不再丢失。")
para("难点二：按天分区把元数据撑爆。 最初想按订单日期分三百六十六个区，"
     "执行到一半报错回滚。查清原因是容器内嵌的元数据库承受不了这么多分区，"
     "改为按月分十二个区后一次通过，并在文档里写明取舍依据。")
para("难点三：统计查询报计数器超限。 把十五项质量指标写在一条查询里，报「计数器超出上限」。"
     "先尝试调参数无效，最终改为每项指标一条独立查询，二十二条全部跑通。"
     "这件事让我明白，有些限制不是靠调参能绕过的。")
para("难点四：BI 工具连不上数据仓库。 Superset 直连 Hive 需要编译一个依赖 Kerberos 的底层库，"
     "在容器里反复失败。后来改为「仓库负责计算、MySQL 负责服务 BI」的结构，"
     "把汇总结果同步到 MySQL，BI 直连 MySQL，既稳定又快，这也是真实企业的常见做法。")
para("难点五：模型效果看起来好，其实没有意义。 预测模型的决定系数只有零点零一，"
     "平均绝对百分比误差是百分之十一点八七，而直接用历史平均值猜是百分之十一点九三。"
     "进一步做自相关检验才发现，日粒度销售额接近白噪声。于是报告里如实写明「不可预测」，"
     "而不是包装成一个漂亮但不真实的准确率。")

h("五、取得的收获")
para("从系统层面看，交付了一套端到端可运行的平台：六个服务一条命令启动，"
     "三个前端页面均返回正常，二十三张表的数据能在一分钟内完成核对，"
     "全量重建三分半钟，五十并发压测零失败、中位响应一百九十六毫秒。")
para("从数据层面看，形成了可复用的指标资产：六个核心指标口径统一，"
     "并得出两个有业务价值的结论——近两成订单未完成履约，以及会员等级与实际消费能力基本无关，"
     "这两条都写进了分析报告和答辩材料。")
para("从个人层面看，最大的变化是从「会写 SQL」变成「能交付项目」。"
     "以前写完查询就算完成，现在会先想口径怎么定、结果怎么验、别人怎么复现、文档怎么写清楚。"
     "这种从技术动作到交付意识的转变，是本次实训最重要的收获。")

h("六、个人成长与反思")
para("一是学会了先诊断再动手。 做预测前先看自相关与趋势，做优化前先看执行计划，"
     "做可视化前先想清楚指标口径。这些前置动作看起来慢，实际省掉了大量返工。")
para("二是学会了如实报告局限。 项目里有几处不完美：复购率因为数据是合成的而饱和在百分之百，"
     "品类销售额与订单实付存在十四倍的口径差异，容器里挂载了宿主权限。"
     "这些我都主动写进文档和答辩材料，因为在工程实践里，说清边界比掩盖问题更专业。")
para("三是认识到协作与留痕的价值。 通过功能分支加合并请求的方式提交文档，"
     "评审时对方还反过来指出我引入的字符错误，这让我体会到代码评审是双向的。"
     "每一次提交、每一条意见，最后都成了可以追溯的证据。")
para("四是明确了下一步方向。 技术上要补实时链路与任务调度；"
     "方法上要把用户分层从金额分档升级为完整的三维模型；"
     "业务上要把品类与订单的口径差异彻底核对清楚。这些都是本次实训暴露出来、"
     "并且值得继续深入的地方。")

doc.save(OUT)
print("已生成", OUT)
