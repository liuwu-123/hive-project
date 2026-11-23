# -*- coding: utf-8 -*-
"""第 5 周：生成答辩 PPT（16:9，10 页）

用法：python tools/make_ppt.py
输出：docs/第5周_答辩PPT.pptx
"""
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

OUT = r"E:\hive-project\docs\第5周_答辩PPT.pptx"
SHOTS = r"E:\hive-project\docs\screenshots"

NAVY = RGBColor(0x0B, 0x1F, 0x3A)
BLUE = RGBColor(0x1B, 0x5F, 0xBF)
CYAN = RGBColor(0x2E, 0xA8, 0xD8)
GREY = RGBColor(0x59, 0x59, 0x59)
LIGHT = RGBColor(0xF2, 0xF6, 0xFC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ORANGE = RGBColor(0xE8, 0x7A, 0x1E)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

W, H = prs.slide_width, prs.slide_height


def add_slide():
    return prs.slides.add_slide(BLANK)


def bg(slide, color):
    r = slide.shapes.add_shape(1, 0, 0, W, H)
    r.fill.solid()
    r.fill.fore_color.rgb = color
    r.line.fill.background()
    r.shadow.inherit = False
    return r


def text(slide, x, y, w, h, s, size=18, bold=False, color=NAVY, align=PP_ALIGN.LEFT,
         font="微软雅黑", anchor=MSO_ANCHOR.TOP, spacing=1.15):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    lines = s.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = font
    return tb


def header(slide, title, subtitle=""):
    bar = slide.shapes.add_shape(1, 0, 0, W, Inches(0.95))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    text(slide, Inches(0.55), Inches(0.18), Inches(9), Inches(0.5), title, 24, True, WHITE)
    if subtitle:
        text(slide, Inches(0.55), Inches(0.62), Inches(11), Inches(0.3), subtitle, 11, False,
             RGBColor(0x9F, 0xC4, 0xEA))
    line = slide.shapes.add_shape(1, 0, Inches(0.95), W, Inches(0.05))
    line.fill.solid()
    line.fill.fore_color.rgb = CYAN
    line.line.fill.background()


def card(slide, x, y, w, h, title, value, note="", color=BLUE):
    box = slide.shapes.add_shape(5, x, y, w, h)  # rounded rect
    box.fill.solid()
    box.fill.fore_color.rgb = LIGHT
    box.line.color.rgb = RGBColor(0xC9, 0xD9, 0xEE)
    box.shadow.inherit = False
    text(slide, x + Inches(0.15), y + Inches(0.1), w - Inches(0.3), Inches(0.3), title, 11, False, GREY)
    text(slide, x + Inches(0.15), y + Inches(0.38), w - Inches(0.3), Inches(0.5), value, 24, True, color)
    if note:
        text(slide, x + Inches(0.15), y + h - Inches(0.36), w - Inches(0.3), Inches(0.3), note, 9, False, GREY)


def table(slide, x, y, w, rows, col_widths=None, header_fill=NAVY, font_size=11, row_h=0.32):
    nrow, ncol = len(rows), len(rows[0])
    shape = slide.shapes.add_table(nrow, ncol, x, y, w, Inches(row_h * nrow))
    tbl = shape.table
    if col_widths:
        total = sum(col_widths)
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = Emu(int(w * cw / total))
    for r in range(nrow):
        for c in range(ncol):
            cell = tbl.cell(r, c)
            cell.text = str(rows[r][c])
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(font_size)
            p.font.name = "微软雅黑"
            if r == 0:
                p.font.bold = True
                p.font.color.rgb = WHITE
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_fill
            else:
                p.font.color.rgb = RGBColor(0x22, 0x2B, 0x38)
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if r % 2 else RGBColor(0xF4, 0xF7, 0xFB)
    return tbl


def pill(slide, x, y, w, h, s, fill=CYAN, color=WHITE, size=11):
    b = slide.shapes.add_shape(5, x, y, w, h)
    b.fill.solid()
    b.fill.fore_color.rgb = fill
    b.line.fill.background()
    b.shadow.inherit = False
    tf = b.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = s
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = color
    r.font.name = "微软雅黑"
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return b


# ============ 1 封面 ============
s = add_slide()
bg(s, NAVY)
band = s.shapes.add_shape(1, 0, Inches(4.6), W, Inches(0.06))
band.fill.solid()
band.fill.fore_color.rgb = CYAN
band.line.fill.background()
text(s, Inches(0.9), Inches(1.7), Inches(11.5), Inches(0.6), "云购生活 · 企业级数据仓库", 20, False,
     RGBColor(0x9F, 0xC4, 0xEA))
text(s, Inches(0.9), Inches(2.25), Inches(11.8), Inches(1.2), "经营分析可视化系统", 46, True, WHITE)
text(s, Inches(0.9), Inches(3.35), Inches(11.5), Inches(0.6),
     "从原始 CSV 到四层数仓 · 预测建模 · NL2SQL · 可视化大屏 · 一键部署", 16, False,
     RGBColor(0xC5, 0xD9, 0xF0))
text(s, Inches(0.9), Inches(4.95), Inches(6), Inches(0.4), "团队：云仓五号", 16, True, WHITE)
text(s, Inches(0.9), Inches(5.4), Inches(8), Inches(0.4),
     "刘祎炫 · 张业彬 · 闫洪伟 · 柴传兴 · 邓克超", 13, False, RGBColor(0x9F, 0xC4, 0xEA))
text(s, Inches(0.9), Inches(5.85), Inches(6), Inches(0.4), "企业项目实战实训 · 2026-11", 12, False,
     RGBColor(0x7F, 0xA8, 0xD8))

# ============ 2 全景 ============
s = add_slide()
header(s, "项目全景：一条数据链路，五个交付层次", "原始 CSV → 四层数仓 → 分析与 AI → 可视化 → 一键部署")
steps = [
    ("原始数据", "6 个 CSV\n114,809 行", CYAN),
    ("ODS", "贴源入库\n行数校验", BLUE),
    ("DWD", "清洗 + 星型模型\n7 维表 3 事实表", BLUE),
    ("DWS / ADS", "汇总 + 指标\n10 张表", BLUE),
    ("分析与 AI", "预测 / NL2SQL\nAI 洞察", ORANGE),
    ("可视化", "Superset\n大屏 / 问答", RGBColor(0x2E, 0x8B, 0x57)),
    ("部署", "6 服务\n一键启动", RGBColor(0x6A, 0x3D, 0x9A)),
]
x0, y0, bw, bh, gap = Inches(0.55), Inches(2.0), Inches(1.62), Inches(1.45), Inches(0.13)
for i, (title, desc, color) in enumerate(steps):
    x = x0 + i * (bw + gap)
    box = s.shapes.add_shape(5, x, y0, bw, bh)
    box.fill.solid()
    box.fill.fore_color.rgb = color
    box.line.fill.background()
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = title
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = WHITE
    r.font.name = "微软雅黑"
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    r2.text = desc
    r2.font.size = Pt(9)
    r2.font.color.rgb = RGBColor(0xE8, 0xEF, 0xF8)
    r2.font.name = "微软雅黑"
    if i < len(steps) - 1:
        arrow = s.shapes.add_shape(13, x + bw + Inches(0.005), y0 + bh / 2 - Inches(0.08),
                                   Inches(0.11), Inches(0.16))
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = RGBColor(0xB8, 0xC8, 0xDC)
        arrow.line.fill.background()

card(s, Inches(0.55), Inches(3.85), Inches(2.9), Inches(1.15), "数据规模", "11.5 万行", "6 张业务表 / 366 天")
card(s, Inches(3.62), Inches(3.85), Inches(2.9), Inches(1.15), "数仓对象", "23 张表", "ODS6 + DWD7 + DWS5 + ADS5")
card(s, Inches(6.69), Inches(3.85), Inches(2.9), Inches(1.15), "NL2SQL", "10/10", "测试集全通过，均 5.95 秒")
card(s, Inches(9.76), Inches(3.85), Inches(3.0), Inches(1.15), "端到端重建", "3.2 分钟", "CSV → BI 可用", ORANGE)

text(s, Inches(0.55), Inches(5.3), Inches(12.2), Inches(1.1),
     "设计原则：Hive 负责计算，MySQL 负责服务 BI；每一层都能用一条 SQL 复核行数与指标，口径统一后才能谈可视化。",
     13, False, GREY)

# ============ 3 数据与质量 ============
s = add_slide()
header(s, "数据接入与质量治理", "把「能用吗」变成「可信吗」：16 项指标逐项量化")
table(s, Inches(0.55), Inches(1.35), Inches(6.0), [
    ["数据表", "行数", "关键问题"],
    ["用户", "1,000", "性别 8 种写法、年龄越界"],
    ["商品", "600", "品类含空格、日期缺失"],
    ["门店", "60", "—"],
    ["订单", "15,600 → 15,000", "600 条重复、负金额、超大金额"],
    ["订单明细", "37,549", "数量 ≤0"],
    ["用户行为", "60,000", "时间格式不统一"],
], col_widths=[1.6, 2.2, 2.4], font_size=11, row_h=0.42)

card(s, Inches(6.9), Inches(1.35), Inches(2.85), Inches(1.2), "清洗指标", "16 项", "14 项修复率 100%")
card(s, Inches(9.95), Inches(1.35), Inches(2.85), Inches(1.2), "重复订单", "600 → 0", "row_number 按时间取最新")

text(s, Inches(6.9), Inches(2.8), Inches(5.9), Inches(0.4), "枚举收敛效果", 13, True, NAVY)
table(s, Inches(6.9), Inches(3.2), Inches(5.9), [
    ["字段", "清洗前", "清洗后"],
    ["性别", "8", "3（男/女/未知）"],
    ["会员等级", "12", "4"],
    ["订单状态", "12", "5"],
    ["支付方式", "7", "4"],
    ["渠道", "6", "4"],
    ["行为类型", "10", "4"],
], col_widths=[1.6, 1.4, 2.9], font_size=10, row_h=0.34)

text(s, Inches(0.55), Inches(5.5), Inches(12.2), Inches(1.4),
     "两条铁律：①「有效订单」= amount_invalid = 0，所有金额指标必须带这个条件；"
     "② 品类销售额（明细口径）与订单 GMV（实付口径）不可相加——实测相差 14.21 倍，报告中分别标注。",
     12, False, GREY)

# ============ 4 数仓建模 ============
s = add_slide()
header(s, "四层数仓与星型建模", "分层不是为了好看，是为了让口径有唯一的落点")
layers = [
    ("ADS 应用层", "ads_kpi_overview / ads_sales_daily / ads_category_topn / ads_store_topn / ads_user_value", RGBColor(0x2E, 0x8B, 0x57)),
    ("DWS 汇总层", "dws_sales_day 366 / dws_sales_month 12 / dws_store_month 720 / dws_channel_month 48 / dws_category_month 96", BLUE),
    ("DWD 明细层", "dim_user · dim_product · dim_store · dim_date ＋ fact_order · fact_order_item · fact_behavior", CYAN),
    ("ODS 贴源层", "6 张表原样接入，不做任何加工，便于回溯与复算", GREY),
]
y = Inches(1.3)
for name, desc, color in layers:
    bar = s.shapes.add_shape(5, Inches(0.55), y, Inches(7.6), Inches(0.95))
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()
    bar.shadow.inherit = False
    text(s, Inches(0.75), y + Inches(0.1), Inches(2.2), Inches(0.35), name, 13, True, WHITE)
    text(s, Inches(0.75), y + Inches(0.45), Inches(7.2), Inches(0.45), desc, 9, False,
         RGBColor(0xEA, 0xF2, 0xFA))
    y += Inches(1.08)

text(s, Inches(8.5), Inches(1.3), Inches(4.3), Inches(0.4), "关键设计决策", 13, True, NAVY)
decisions = [
    ("按月分区（12）", "366 个日分区撑爆内嵌 Derby 元数据，实测报 savepoint 回滚"),
    ("明细分 8 桶", "按 order_id 回查明细只命中 1 个桶"),
    ("ORC 存储", "列裁剪 + 压缩，谓词下推"),
    ("映射表两级", "脏值 → map_* → dim_*，新增脏值只加一行"),
]
yy = Inches(1.75)
for t_, d_ in decisions:
    b = s.shapes.add_shape(5, Inches(8.5), yy, Inches(4.3), Inches(0.95))
    b.fill.solid()
    b.fill.fore_color.rgb = LIGHT
    b.line.color.rgb = RGBColor(0xC9, 0xD9, 0xEE)
    b.shadow.inherit = False
    text(s, Inches(8.65), yy + Inches(0.08), Inches(4.0), Inches(0.3), t_, 11, True, BLUE)
    text(s, Inches(8.65), yy + Inches(0.38), Inches(4.0), Inches(0.5), d_, 9, False, GREY)
    yy += Inches(1.05)

# ============ 5 核心指标 ============
s = add_slide()
header(s, "核心 KPI：3611 万 GMV 背后的四个数字", "所有指标可从明细复算，口径写在《指标定义文档》里")
kpis = [
    ("GMV", "3,611.67 万", "有效订单实付合计"),
    ("订单量", "14,398 笔", "去重费用订单"),
    ("客单价", "2,508.45 元", "GMV ÷ 订单量"),
    ("活跃用户", "1,000 人", "有下单行为的用户"),
]
x = Inches(0.55)
for t_, v_, n_ in kpis:
    card(s, x, Inches(1.4), Inches(3.0), Inches(1.35), t_, v_, n_, BLUE)
    x += Inches(3.15)

text(s, Inches(0.55), Inches(3.05), Inches(6), Inches(0.4), "三个业务发现", 14, True, NAVY)
findings = [
    ("订单未履约率 19.3%", "已取消 13.9% + 退款中 5.4%，近两成订单没有走完交易"),
    ("会员体系失效", "四档会员客单价 2489~2522 元，极差仅 33.5 元，等级与实际消费无关"),
    ("复购率 100%（需说明）", "每用户下单 4~27 笔，合成数据必然复购，该指标无区分度——已在文档注明，不当作结论"),
]
yy = Inches(3.5)
for t_, d_ in findings:
    b = s.shapes.add_shape(5, Inches(0.55), yy, Inches(7.5), Inches(0.85))
    b.fill.solid()
    b.fill.fore_color.rgb = LIGHT
    b.line.color.rgb = RGBColor(0xC9, 0xD9, 0xEE)
    b.shadow.inherit = False
    text(s, Inches(0.7), yy + Inches(0.07), Inches(7.2), Inches(0.3), t_, 12, True, ORANGE)
    text(s, Inches(0.7), yy + Inches(0.37), Inches(7.2), Inches(0.4), d_, 9.5, False, GREY)
    yy += Inches(0.95)

table(s, Inches(8.3), Inches(3.5), Inches(4.5), [
    ["用户分层", "人数", "累计消费"],
    ["A 高价值", "116", "650.5 万"],
    ["B 中高价值", "579", "2,238.9 万"],
    ["C 中等", "282", "693.3 万"],
    ["D 普通", "23", "28.9 万"],
], col_widths=[1.9, 1.0, 1.6], font_size=10.5, row_h=0.4)

# ============ 6 预测建模 ============
s = add_slide()
header(s, "预测建模：模型打不过「平均值」，这本身是结论", "先诊断、再建模、最后诚实评估")
table(s, Inches(0.55), Inches(1.4), Inches(6.4), [
    ["检验项", "结果", "含义"],
    ["自相关 lag1", "-0.1788", "接近随机"],
    ["自相关 lag2~7", "-0.04 ~ +0.01", "无周周期"],
    ["星期均值极差", "7.05%", "星期效应弱"],
    ["全年趋势", "-2.63%", "几乎无趋势"],
    ["月度极差", "10.92%", "月度平稳"],
], col_widths=[2.0, 2.0, 2.4], font_size=10.5, row_h=0.4)

text(s, Inches(0.55), Inches(3.95), Inches(6.2), Inches(0.4), "模型对比（前 11 月训练 / 12 月验证）", 12, True, NAVY)
table(s, Inches(0.55), Inches(4.35), Inches(6.4), [
    ["模型", "MAE", "MAPE", "R²"],
    ["线性回归", "12,868", "11.89%", "-0.25"],
    ["随机森林", "12,338", "11.87%", "0.01"],
    ["基线（均值）", "—", "11.93%", "0"],
], col_widths=[1.8, 1.5, 1.5, 1.2], font_size=10.5, row_h=0.38)

card(s, Inches(7.3), Inches(1.4), Inches(5.5), Inches(1.2), "结论", "模型仅优于基线 0.06 个百分点", "序列近似白噪声，日粒度不可预测", ORANGE)
card(s, Inches(7.3), Inches(2.75), Inches(5.5), Inches(1.2), "聚合实验", "周粒度 MAPE 4.26%", "但复杂模型仍不如均值（7.7%），说明滞后特征是噪声", BLUE)
card(s, Inches(7.3), Inches(4.1), Inches(5.5), Inches(1.2), "7 天预测", "合计 69.02 万元", "95% 区间 ±3.1 万元/天，只能作区间参考")

text(s, Inches(7.3), Inches(5.55), Inches(5.5), Inches(1.3),
     "如实报告「不可预测」比强行吹准确率更有价值：数据本身是均匀随机的，"
     "把它包装成 95% 准确率会误导业务决策。", 11, False, GREY)

# ============ 7 NL2SQL ============
s = add_slide()
header(s, "NL2SQL：用中文问数，5 秒拿到结果", "Schema 抽取 → Prompt 约束 → 白名单校验 → 执行 → 结果")
flow = ["用户提问", "Schema\n16 张表", "Prompt\n口径+示例", "大模型\nJSON 输出", "SQL 校验\n只读白名单", "beeline\n执行", "结果表"]
x = Inches(0.55)
for i, f in enumerate(flow):
    pill(s, x, Inches(1.4), Inches(1.55), Inches(1.1), f, BLUE if i in (0, 6) else CYAN, WHITE, 10)
    if i < len(flow) - 1:
        a = s.shapes.add_shape(13, x + Inches(1.57), Inches(1.85), Inches(0.15), Inches(0.2))
        a.fill.solid()
        a.fill.fore_color.rgb = RGBColor(0xB8, 0xC8, 0xDC)
        a.line.fill.background()
    x += Inches(1.72)

card(s, Inches(0.55), Inches(2.85), Inches(2.6), Inches(1.1), "测试通过率", "10 / 10", "覆盖 KPI/品类/门店/会员")
card(s, Inches(3.35), Inches(2.85), Inches(2.6), Inches(1.1), "平均耗时", "5.95 秒", "模型 1~2s + Hive 3~4s")
card(s, Inches(6.15), Inches(2.85), Inches(2.6), Inches(1.1), "安全校验", "只读白名单", "禁写操作 / 表名前缀校验")

text(s, Inches(9.05), Inches(2.85), Inches(3.8), Inches(0.4), "演示问题（现场）", 12, True, NAVY)
for i, q in enumerate(["2024 年 6 月 GMV 最高的前 3 家门店", "各会员等级的客单价是多少",
                       "销量最高的前 5 个品类"]):
    text(s, Inches(9.05), Inches(3.3 + i * 0.42), Inches(3.9), Inches(0.35), "· " + q, 9.5, False, GREY)

text(s, Inches(0.55), Inches(4.2), Inches(8), Inches(0.4), "三个被修掉的真实坑", 13, True, NAVY)
table(s, Inches(0.55), Inches(4.6), Inches(12.2), [
    ["问题", "现象", "处理"],
    ["Schema 漏维表", "模型编字段名 member_level_name", "补 4 张枚举维表 + Prompt 固定字段名"],
    ["只读 stdout", "beeline 编译错误丢失，误判为「无结果」", "合并 stderr 判错，仅用 stdout 解析"],
    ["未限制相对时间", "生成 current_date() 查 2024 数据全空", "Prompt 禁止相对时间，换算具体月份"],
], col_widths=[2.4, 4.6, 5.2], font_size=10, row_h=0.42)

# ============ 8 可视化 ============
s = add_slide()
header(s, "可视化：三种形态，同一份数据", "Superset 自助分析 · ECharts 大屏 · Streamlit 对话")
# 上排两张 16:9 截图（宽 6.0in → 高 3.37in），下排左侧 Streamlit 竖图（宽 2.4in → 高 2.1in）
top_y = Inches(1.28)
s.shapes.add_picture(os.path.join(SHOTS, "week4_superset.png"), Inches(0.55), top_y, width=Inches(6.0))
s.shapes.add_picture(os.path.join(SHOTS, "week4_screen.png"), Inches(6.85), top_y, width=Inches(6.0))
text(s, Inches(0.55), Inches(4.72), Inches(6.0), Inches(0.3), "Superset 仪表板（6 图 + 筛选）", 9, False, GREY)
text(s, Inches(6.85), Inches(4.72), Inches(6.0), Inches(0.3), "ECharts 大屏（6 类图表 + 中国地图）", 9, False, GREY)

s.shapes.add_picture(os.path.join(SHOTS, "week4_streamlit.png"), Inches(0.55), Inches(5.08), width=Inches(2.25))
text(s, Inches(2.95), Inches(5.12), Inches(3.6), Inches(0.3), "Streamlit 问答", 10, True, NAVY)
text(s, Inches(2.95), Inches(5.45), Inches(3.7), Inches(1.6),
     "提问 → 生成 SQL → 执行 → 结果表 → 自动图表\n实测 8.17 秒返回，SQL 正确关联 3 张表", 9, False, GREY)

text(s, Inches(6.85), Inches(5.12), Inches(6.0), Inches(0.3), "关键设计", 12, True, NAVY)
for i, t_ in enumerate(["Superset 走 MySQL 集市，避开 Hive 驱动编译（sasl）",
                        "大屏 1920×1080 设计稿 + scale 等比缩放，任意分辨率不错位",
                        "ECharts 与地图 JSON 本地化，断网可演示"]):
    text(s, Inches(6.85), Inches(5.5 + i * 0.42), Inches(6.0), Inches(0.35), "· " + t_, 10, False, GREY)

# ============ 9 部署与优化 ============
s = add_slide()
header(s, "部署、性能与工程化", "一条命令起 6 个服务；分区裁剪减少 92.3% 扫描量")
table(s, Inches(0.55), Inches(1.35), Inches(6.1), [
    ["服务", "端口", "健康检查"],
    ["mysql", "3306", "✓"],
    ["hive-metastore", "9083", "—"],
    ["hive-server", "10000", "—"],
    ["superset", "8088", "✓"],
    ["web（大屏）", "5000", "✓"],
    ["app（问答）", "8501", "✓"],
], col_widths=[2.4, 1.5, 2.2], font_size=10.5, row_h=0.38)

card(s, Inches(6.9), Inches(1.35), Inches(2.85), Inches(1.05), "全量重建", "3.2 分钟", "CSV → BI 可用")
card(s, Inches(9.95), Inches(1.35), Inches(2.85), Inches(1.05), "压测（50 并发）", "P50 196ms", "零失败 / QPS 239", RGBColor(0x2E, 0x8B, 0x57))

text(s, Inches(6.9), Inches(2.6), Inches(5.9), Inches(0.35), "查询优化（explain 验证）", 12, True, NAVY)
table(s, Inches(6.9), Inches(3.0), Inches(5.9), [
    ["写法", "扫描行数"],
    ["where order_month = '2024-06'", "1,154"],
    ["where substr(order_timestamp,1,7)=…", "15,000"],
], col_widths=[4.2, 1.7], font_size=10, row_h=0.4)

text(s, Inches(0.55), Inches(4.3), Inches(6.2), Inches(0.35), "工程化规范", 12, True, NAVY)
for i, t_ in enumerate(["密钥 .env 注入，git check-ignore 验证不入库",
                        "feature 分支 + PR + Issue 记录（#2/#3/#4）",
                        "23 张表行数核对 + 10 题 NL2SQL 测试集可复现"]):
    text(s, Inches(0.55), Inches(4.7 + i * 0.42), Inches(6.2), Inches(0.35), "· " + t_, 10, False, GREY)

text(s, Inches(6.9), Inches(4.3), Inches(5.9), Inches(2.0),
     "压测的诚实结论：Hive 单次 6 秒里约 5 秒是 beeline 启动开销，"
     "这组数字反映的是客户端成本而非 Hive 吞吐——因此 Hive 不该被高频直连，"
     "必须经过预汇总与集市。这一点在报告中如实写明。", 10, False, GREY)

# ============ 10 复盘 ============
s = add_slide()
header(s, "复盘：做对了什么、局限在哪、下一步", "五周交付的自我评估")

text(s, Inches(0.55), Inches(1.3), Inches(3.9), Inches(0.35), "做对了", 14, True, RGBColor(0x2E, 0x8B, 0x57))
for i, t_ in enumerate(["口径先定义再写代码", "AI 只做表达，数字由 SQL 产出",
                        "架构分层（Hive 计算 / MySQL 服务）", "可复现：3.2 分钟全量重建"]):
    text(s, Inches(0.55), Inches(1.75 + i * 0.45), Inches(3.9), Inches(0.35), "✓ " + t_, 10.5, False, GREY)

text(s, Inches(4.75), Inches(1.3), Inches(3.9), Inches(0.35), "局限", 14, True, ORANGE)
for i, t_ in enumerate(["合成数据导致指标饱和（复购率 100%）", "品类与 GMV 口径差异待业务确认",
                        "Superset 未直连 Hive", "app 容器挂载 docker.sock 权限偏大"]):
    text(s, Inches(4.75), Inches(1.75 + i * 0.5), Inches(3.9), Inches(0.45), "· " + t_, 10, False, GREY)

text(s, Inches(8.95), Inches(1.3), Inches(3.9), Inches(0.35), "下一步", 14, True, BLUE)
for i, t_ in enumerate(["Spark / 调度 DAG / 实时链路", "NL2SQL 多轮上下文（Issue #2）",
                        "RFM 完整分层 + 指标血缘", "CI 自动化回归（数据 + 接口）"]):
    text(s, Inches(8.95), Inches(1.75 + i * 0.5), Inches(3.9), Inches(0.45), "→ " + t_, 10, False, GREY)

band2 = s.shapes.add_shape(5, Inches(0.55), Inches(4.4), Inches(12.2), Inches(1.15))
band2.fill.solid()
band2.fill.fore_color.rgb = NAVY
band2.line.fill.background()
text(s, Inches(0.85), Inches(4.55), Inches(11.6), Inches(0.4), "一句话总结", 11, False,
     RGBColor(0x9F, 0xC4, 0xEA))
text(s, Inches(0.85), Inches(4.9), Inches(11.6), Inches(0.5),
     "把 11 万行脏数据，变成 6 个可复现的服务和一套说得清口径的指标。", 16, True, WHITE)

text(s, Inches(0.55), Inches(5.85), Inches(12.2), Inches(0.5),
     "现场演示顺序：docker compose ps → Superset 仪表板 → ECharts 大屏 → Streamlit 现场提问 → 一键重建脚本",
     10.5, False, GREY)
text(s, Inches(0.55), Inches(6.35), Inches(12.2), Inches(0.4), "谢谢，请提问。", 14, True, NAVY)

prs.save(OUT)
print("已生成", OUT, "共", len(prs.slides.__iter__.__self__._sldIdLst), "页")
