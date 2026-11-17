# -*- coding: utf-8 -*-
"""第 4 周 · 子任务 2：ECharts 大屏数据接口

从 MySQL BI 集市（ydsh_ads）读取指标，以 JSON 提供给前端大屏。
启动：python web/api.py        访问 http://localhost:5000

接口：
    /api/kpi          核心 KPI
    /api/trend        日 GMV 趋势（近 90 天 + 7 日移动平均）
    /api/category     品类销售额
    /api/channel      渠道 GMV 占比
    /api/province     省份销售分布
    /api/store        门店 Top10（GMV vs 订单量，散点用）
    /api/heatmap      品类 × 月份 热力图
    /api/user-level   用户价值分层
    /api/pay          支付方式占比
"""
import json
import os

import pymysql
from flask import Flask, jsonify, send_from_directory

DB = dict(host=os.environ.get("DB_HOST", "127.0.0.1"),
          port=int(os.environ.get("DB_PORT", 3306)),
          user=os.environ.get("DB_USER", "root"),
          password=os.environ.get("DB_PASSWORD", "root"),
          database=os.environ.get("DB_NAME", "ydsh_ads"),
          charset="utf8mb4")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "static"))


def query(sql, args=None):
    conn = pymysql.connect(**DB)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, args or ())
            return cur.fetchall()
    finally:
        conn.close()


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/kpi")
def api_kpi():
    rows = query("SELECT kpi_name, kpi_value, kpi_unit FROM ads_kpi_overview")
    order = ["GMV", "订单量", "客单价 AOV", "活跃用户数", "复购用户数", "复购率"]
    data = {r["kpi_name"]: {"value": float(r["kpi_value"]), "unit": r["kpi_unit"]} for r in rows}
    return jsonify([{"name": k, **data[k]} for k in order if k in data])


@app.route("/api/trend")
def api_trend():
    rows = query("""
        SELECT stat_date, gmv, order_cnt, gmv_ma7
        FROM ads_sales_daily
        ORDER BY stat_date DESC LIMIT 90
    """)
    rows = list(reversed(rows))
    return jsonify([{
        "date": r["stat_date"].strftime("%m-%d"),
        "gmv": round(float(r["gmv"]), 2),
        "orders": int(r["order_cnt"]),
        "ma7": round(float(r["gmv_ma7"]), 2) if r["gmv_ma7"] is not None else None,
    } for r in rows])


@app.route("/api/category")
def api_category():
    rows = query("SELECT category, sales, qty FROM ads_category_topn ORDER BY rk")
    return jsonify([{"name": r["category"], "sales": round(float(r["sales"]) / 10000, 1),
                     "qty": int(r["qty"])} for r in rows])


@app.route("/api/channel")
def api_channel():
    rows = query("""
        SELECT channel_name, SUM(gmv) AS gmv, SUM(order_cnt) AS orders
        FROM dws_channel_month GROUP BY channel_name ORDER BY gmv DESC
    """)
    return jsonify([{"name": r["channel_name"], "value": round(float(r["gmv"]) / 10000, 1),
                     "orders": int(r["orders"])} for r in rows])


@app.route("/api/province")
def api_province():
    rows = query("""
        SELECT province, SUM(gmv) AS gmv, SUM(order_cnt) AS orders
        FROM dws_store_month GROUP BY province ORDER BY gmv DESC
    """)
    return jsonify([{"name": r["province"], "value": round(float(r["gmv"]) / 10000, 1),
                     "orders": int(r["orders"])} for r in rows])


@app.route("/api/store")
def api_store():
    rows = query("""
        SELECT store_name, gmv, order_cnt, aov, province
        FROM ads_store_topn ORDER BY rk LIMIT 30
    """)
    return jsonify([{
        "name": r["store_name"].replace("云购生活·", ""),
        "gmv": round(float(r["gmv"]) / 10000, 2),
        "orders": int(r["order_cnt"]),
        "aov": round(float(r["aov"]), 2),
        "province": r["province"],
    } for r in rows])


@app.route("/api/heatmap")
def api_heatmap():
    rows = query("""
        SELECT category, stat_month, sales
        FROM dws_category_month ORDER BY stat_month, category
    """)
    months = sorted({r["stat_month"] for r in rows})
    cats = sorted({r["category"] for r in rows})
    mi = {m: i for i, m in enumerate(months)}
    ci = {c: i for i, c in enumerate(cats)}
    data = [[mi[r["stat_month"]], ci[r["category"]], round(float(r["sales"]) / 10000, 1)] for r in rows]
    vmax = max(d[2] for d in data) if data else 1
    return jsonify({"months": months, "categories": cats, "data": data, "max": vmax})


@app.route("/api/pay")
def api_pay():
    rows = query("SELECT pay_name, gmv, orders FROM ads_pay_type ORDER BY gmv DESC")
    return jsonify([{"name": r["pay_name"], "value": round(float(r["gmv"]) / 10000, 1),
                     "orders": int(r["orders"])} for r in rows])


@app.route("/api/user-level")
def api_user_level():
    rows = query("""
        SELECT value_level, COUNT(*) AS users, SUM(total_amount) AS gmv
        FROM ads_user_value GROUP BY value_level ORDER BY value_level
    """)
    return jsonify([{"name": r["value_level"], "users": int(r["users"]),
                     "gmv": round(float(r["gmv"]) / 10000, 1)} for r in rows])


if __name__ == "__main__":
    print("ECharts 大屏数据接口启动：http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
