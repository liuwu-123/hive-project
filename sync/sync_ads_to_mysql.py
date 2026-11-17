# -*- coding: utf-8 -*-
"""第 4 周 · 步骤 1：把 Hive 的 ADS / DWS 结果同步到 MySQL（BI 集市）。

为什么要有这一层：
  Superset 直连 Hive 需要 pyhive + thrift + sasl（需编译），容器内失败率高；
  把结果表同步到 MySQL，Superset / ECharts / Streamlit 都可直接读取，
  这也是真实企业常见做法：Hive 负责计算，MySQL 作为 BI 集市。

用法：
    python sync/sync_ads_to_mysql.py
输出：
    sql/mysql/init_ydsh_ads.sql  —— 建库建表 + 数据插入，供 MySQL 容器执行
"""
import csv
import os

SRC = r"E:\dssgz\mysql_sync"
OUT = r"E:\hive-project\sql\mysql\init_ydsh_ads.sql"

# 表结构定义：(列名, MySQL 类型)
SCHEMA = {
    "ads_kpi_overview": [
        ("kpi_name", "VARCHAR(64)"), ("kpi_value", "DECIMAL(18,2)"),
        ("kpi_unit", "VARCHAR(16)"), ("definition", "VARCHAR(255)"),
    ],
    "ads_sales_daily": [
        ("stat_date", "DATE"), ("order_cnt", "BIGINT"), ("gmv", "DECIMAL(18,2)"),
        ("aov", "DECIMAL(12,2)"), ("gmv_dod", "DECIMAL(10,4)"), ("gmv_ma7", "DECIMAL(18,2)"),
    ],
    "ads_category_topn": [
        ("rk", "INT"), ("category", "VARCHAR(64)"), ("order_cnt", "BIGINT"),
        ("qty", "BIGINT"), ("sales", "DECIMAL(18,2)"), ("sales_ratio", "DECIMAL(10,4)"),
    ],
    "ads_store_topn": [
        ("rk", "INT"), ("store_id", "VARCHAR(32)"), ("store_name", "VARCHAR(64)"),
        ("province", "VARCHAR(32)"), ("city", "VARCHAR(32)"), ("order_cnt", "BIGINT"),
        ("gmv", "DECIMAL(18,2)"), ("aov", "DECIMAL(12,2)"),
    ],
    "ads_user_value": [
        ("user_id", "VARCHAR(32)"), ("total_amount", "DECIMAL(18,2)"),
        ("order_cnt", "BIGINT"), ("last_order", "DATE"), ("value_level", "VARCHAR(32)"),
    ],
    "dws_sales_month": [
        ("stat_month", "VARCHAR(16)"), ("order_cnt", "BIGINT"), ("gmv", "DECIMAL(18,2)"),
        ("buyer_cnt", "BIGINT"), ("aov", "DECIMAL(12,2)"),
        ("cancel_rate", "DECIMAL(10,4)"), ("refund_rate", "DECIMAL(10,4)"),
    ],
    "dws_category_month": [
        ("stat_month", "VARCHAR(16)"), ("category", "VARCHAR(64)"), ("order_cnt", "BIGINT"),
        ("qty", "BIGINT"), ("sales", "DECIMAL(18,2)"), ("sales_ratio", "DECIMAL(10,4)"),
    ],
    "dws_store_month": [
        ("stat_month", "VARCHAR(16)"), ("store_id", "VARCHAR(32)"), ("store_name", "VARCHAR(64)"),
        ("province", "VARCHAR(32)"), ("city", "VARCHAR(32)"), ("order_cnt", "BIGINT"),
        ("gmv", "DECIMAL(18,2)"), ("buyer_cnt", "BIGINT"), ("aov", "DECIMAL(12,2)"),
    ],
    "dws_channel_month": [
        ("stat_month", "VARCHAR(16)"), ("channel_code", "VARCHAR(16)"), ("channel_name", "VARCHAR(32)"),
        ("order_cnt", "BIGINT"), ("gmv", "DECIMAL(18,2)"), ("buyer_cnt", "BIGINT"),
        ("aov", "DECIMAL(12,2)"),
    ],
}

HEADER = """-- 第 4 周：MySQL BI 集市初始化脚本
-- 由 sync/sync_ads_to_mysql.py 自动生成，数据来源：Hive 的 ydsh_ads / ydsh_dws
-- 执行方式：docker exec -i hive-project-mysql-1 mysql -uroot -proot < init_ydsh_ads.sql

CREATE DATABASE IF NOT EXISTS ydsh_ads DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ydsh_ads;
SET NAMES utf8mb4;
"""


def esc(v):
    if v is None or v == "" or v == "NULL":
        return "NULL"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


def num_or_null(v):
    if v is None or v == "" or v == "NULL":
        return "NULL"
    return v


def main():
    parts = [HEADER]
    total_rows = 0
    for table, cols in SCHEMA.items():
        path = os.path.join(SRC, table + ".csv")
        if not os.path.exists(path):
            print(f"  [跳过] {table} 无 CSV")
            continue
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
        if not rows:
            continue
        header = [h.strip() for h in rows[0]]
        body = rows[1:]

        col_defs = ",\n  ".join(f"`{c}` {t}" for c, t in cols)
        parts.append(f"\n-- ---------- {table}（{len(body)} 行） ----------\n")
        parts.append(f"DROP TABLE IF EXISTS `{table}`;\n")
        parts.append(f"CREATE TABLE `{table}` (\n  {col_defs}\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n")

        if body:
            col_names = ", ".join(f"`{c}`" for c, _ in cols)
            batch = []
            for r in body:
                vals = []
                for i, (_c, t) in enumerate(cols):
                    v = r[i] if i < len(r) else None
                    if t.startswith(("DECIMAL", "BIGINT", "INT")):
                        vals.append(num_or_null(v))
                    else:
                        vals.append(esc(v))
                batch.append("(" + ", ".join(vals) + ")")
            # 每 200 行一条 INSERT
            for i in range(0, len(batch), 200):
                chunk = batch[i:i + 200]
                parts.append(f"INSERT INTO `{table}` ({col_names}) VALUES\n" + ",\n".join(chunk) + ";\n")
        total_rows += len(body)
        print(f"  {table:<22} {len(body):>5} 行  列 {len(cols)}")

    parts.append("\n-- ---------- 校验 ----------\n")
    for table in SCHEMA:
        parts.append(f"SELECT '{table}' AS tbl, COUNT(*) AS cnt FROM `{table}`;\n")

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(parts))
    size = os.path.getsize(OUT) / 1024
    print(f"\n已生成 {OUT}（{size:.1f} KB，共 {total_rows} 行数据）")


if __name__ == "__main__":
    main()
