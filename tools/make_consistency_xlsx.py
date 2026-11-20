# -*- coding: utf-8 -*-
"""第 5 周：生成《数据一致性核对表.xlsx》

数据来源：scripts/rebuild_end2end.ps1 的核对结果（23 张表）+ 核心指标。
用法：python tools/make_consistency_xlsx.py
"""
import os

import pymysql
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

OUT = r"E:\hive-project\docs\第5周_数据一致性核对表.xlsx"

EXPECT = [
    ("ODS", "ydsh_ods.ods_user", 1000, "原始用户"),
    ("ODS", "ydsh_ods.ods_product", 600, "原始商品"),
    ("ODS", "ydsh_ods.ods_store", 60, "原始门店"),
    ("ODS", "ydsh_ods.ods_order", 15600, "原始订单（含 600 重复）"),
    ("ODS", "ydsh_ods.ods_order_item", 37549, "原始订单明细"),
    ("ODS", "ydsh_ods.ods_user_behavior", 60000, "原始行为"),
    ("DWD", "ydsh_dwd.dim_user", 1000, "用户维度（清洗+编码）"),
    ("DWD", "ydsh_dwd.dim_product", 600, "商品维度"),
    ("DWD", "ydsh_dwd.dim_store", 60, "门店维度"),
    ("DWD", "ydsh_dwd.dim_date", 1096, "日期维度 2023-2025"),
    ("DWD", "ydsh_dwd.fact_order", 15000, "订单事实（去重后）"),
    ("DWD", "ydsh_dwd.fact_order_item", 37549, "明细事实（分 8 桶）"),
    ("DWD", "ydsh_dwd.fact_behavior", 60000, "行为事实（3 个月分区）"),
    ("DWS", "ydsh_dws.dws_sales_day", 366, "日汇总"),
    ("DWS", "ydsh_dws.dws_sales_month", 12, "月汇总"),
    ("DWS", "ydsh_dws.dws_store_month", 720, "月×60 门店"),
    ("DWS", "ydsh_dws.dws_channel_month", 48, "月×4 渠道"),
    ("DWS", "ydsh_dws.dws_category_month", 96, "月×8 品类"),
    ("ADS", "ydsh_ads.ads_kpi_overview", 6, "KPI 总览"),
    ("ADS", "ydsh_ads.ads_sales_daily", 366, "销售日报"),
    ("ADS", "ydsh_ads.ads_category_topn", 8, "品类排行"),
    ("ADS", "ydsh_ads.ads_store_topn", 60, "门店排行"),
    ("ADS", "ydsh_ads.ads_user_value", 1000, "用户价值分层"),
]

EXPECT_KPI = [
    ("GMV（元）", 36116687.06, "SUM(pay_amount) WHERE amount_invalid=0"),
    ("订单量（笔）", 14398, "COUNT(DISTINCT order_id) WHERE amount_invalid=0"),
    ("客单价（元）", 2508.45, "GMV ÷ 订单量"),
    ("活跃用户（人）", 1000, "COUNT(DISTINCT user_id)"),
    ("复购用户（人）", 1000, "下单 ≥2 次的用户"),
    ("复购率（%）", 100.00, "复购用户 ÷ 下单用户（合成数据饱和）"),
]


def mysql_count(table):
    conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="root",
                           database="ydsh_ads", charset="utf8mb4")
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM `{table}`")
            return cur.fetchone()[0]
    finally:
        conn.close()


def style_header(ws):
    fill = PatternFill("solid", fgColor="4472C4")
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = fill
        c.alignment = Alignment(horizontal="center", vertical="center")
    ws.freeze_panes = "A2"
    for col in ws.columns:
        w = max(len(str(x.value or "")) for x in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max(w * 1.8, 10), 60)


def main():
    wb = Workbook()

    # Sheet 1：各层行数
    ws = wb.active
    ws.title = "一、各层行数核对"
    ws.append(["层级", "Hive 表", "期望行数", "说明"])
    for layer, table, cnt, note in EXPECT:
        ws.append([layer, table, cnt, note])
    style_header(ws)

    # Sheet 2：核心指标
    ws2 = wb.create_sheet("二、核心指标核对")
    ws2.append(["指标", "期望值", "计算口径"])
    for name, val, formula in EXPECT_KPI:
        ws2.append([name, val, formula])
    style_header(ws2)

    # Sheet 3：MySQL 集市
    ws3 = wb.create_sheet("三、MySQL 集市核对")
    ws3.append(["MySQL 表", "实际行数", "对应 Hive 表", "一致性"])
    mapping = {
        "ads_kpi_overview": "ydsh_ads.ads_kpi_overview",
        "ads_sales_daily": "ydsh_ads.ads_sales_daily",
        "ads_category_topn": "ydsh_ads.ads_category_topn",
        "ads_store_topn": "ydsh_ads.ads_store_topn",
        "ads_user_value": "ydsh_ads.ads_user_value",
        "dws_sales_month": "ydsh_dws.dws_sales_month",
        "dws_category_month": "ydsh_dws.dws_category_month",
        "dws_store_month": "ydsh_dws.dws_store_month",
        "dws_channel_month": "ydsh_dws.dws_channel_month",
    }
    exp = {t.split(".")[-1]: c for _l, t, c, _n in EXPECT}
    for mt, ht in mapping.items():
        try:
            n = mysql_count(mt)
            flag = "一致" if n == exp.get(ht.split(".")[-1]) else f"不一致（期望 {exp.get(ht.split('.')[-1])}）"
        except Exception as e:  # noqa
            n, flag = -1, f"查询失败：{e}"
        ws3.append([mt, n, ht, flag])
    style_header(ws3)

    # Sheet 4：链路说明
    ws4 = wb.create_sheet("四、端到端链路说明")
    rows = [
        ["步骤", "内容", "命令 / 脚本", "耗时"],
        ["1", "Docker 环境", "docker compose up -d", "冷启动约 2 分钟"],
        ["2", "ODS 建表 + 导入 6 个 CSV", "sql/ods/create_ods.sql、load_ods.sql", "约 20 秒"],
        ["3", "第 1 周清洗（用户/商品/订单去重）", "sql/clean/01~03", "约 30 秒"],
        ["4", "枚举 / 维度 / 事实建模", "sql/clean/10~13、sql/dwd/14~15", "约 60 秒"],
        ["5", "DWS 汇总层", "sql/dws/01_dws_sales.sql", "约 40 秒"],
        ["6", "ADS 应用层", "sql/ads/02_ads_kpi.sql", "约 30 秒"],
        ["7", "MySQL BI 集市", "sync/sync_ads_to_mysql.py + init_ydsh_ads.sql", "约 10 秒"],
        ["8", "行数核对 23 张表", "同一脚本第 8 步", "约 20 秒"],
        ["合计", "端到端全量重建", "scripts/rebuild_end2end.ps1", "3.2 分钟（实测）"],
    ]
    for r in rows:
        ws4.append(r)
    style_header(ws4)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print("已生成", OUT)


if __name__ == "__main__":
    main()
