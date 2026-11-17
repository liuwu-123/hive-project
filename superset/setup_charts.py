# -*- coding: utf-8 -*-
"""第 4 周：批量创建 Superset 图表与仪表板。

用法：
    python superset/setup_charts.py

前提：已执行 setup_superset.py（数据库 + 数据集已就绪）。
"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:8088"
USER, PASSWORD = "admin", "admin123"


def call(path, payload=None, token=None, method=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method or ("POST" if data else "GET"))
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            b = r.read().decode("utf-8")
            return r.status, (json.loads(b) if b else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:400]


def metric(col, label, agg="SUM"):
    return {"expressionType": "SIMPLE", "column": {"column_name": col}, "aggregate": agg, "label": label}


def ds_id(token, table):
    code, body = call("/api/v1/dataset/", token=token)
    for r in body.get("result", []):
        if r["table_name"] == table:
            return r["id"]
    return None


def make_chart(token, name, viz, dsid, params):
    payload = {
        "slice_name": name,
        "viz_type": viz,
        "datasource_id": dsid,
        "datasource_type": "table",
        "params": json.dumps(params, ensure_ascii=False),
    }
    code, body = call("/api/v1/chart/", payload, token)
    if code in (200, 201):
        print(f"  [OK] {name}  (id={body.get('id')})")
        return body.get("id")
    print(f"  [X] {name} -> {code} {body}")
    return None


def main():
    code, body = call("/api/v1/security/login",
                      {"username": USER, "password": PASSWORD, "provider": "db", "refresh": True})
    if code != 200:
        print("登录失败", code, body)
        sys.exit(1)
    token = body["access_token"]

    d_sales = ds_id(token, "ads_sales_daily")
    d_cat = ds_id(token, "ads_category_topn")
    d_store = ds_id(token, "ads_store_topn")
    d_month = ds_id(token, "dws_sales_month")
    d_store_m = ds_id(token, "dws_store_month")
    d_pay = ds_id(token, "ads_pay_type")
    print(f"数据集 id：sales={d_sales} cat={d_cat} store={d_store} month={d_month} store_m={d_store_m} pay={d_pay}")

    base_common = {"time_range": "No filter", "adhoc_filters": [], "row_limit": 10000}

    charts = []

    # 1. 销售趋势（折线）
    charts.append(make_chart(token, "① 销售趋势（日 GMV）", "line", d_sales, {
        "viz_type": "line", "datasource": f"{d_sales}__table",
        "x_axis": "stat_date", "metrics": [metric("gmv", "GMV")],
        "groupby": [], "show_legend": True, "rich_tooltip": True,
        **base_common,
    }))

    # 2. 品类销售额（柱状）
    charts.append(make_chart(token, "② 品类销售额", "bar", d_cat, {
        "viz_type": "bar", "datasource": f"{d_cat}__table",
        "x_axis": "category", "metrics": [metric("sales", "销售额")],
        "groupby": [], "show_legend": False, "order_desc": True,
        **base_common,
    }))

    # 3. 支付方式占比（饼图）
    charts.append(make_chart(token, "③ 支付方式 GMV 占比", "pie", d_pay, {
        "viz_type": "pie", "datasource": f"{d_pay}__table",
        "groupby": ["pay_name"], "metric": metric("gmv", "GMV"),
        "show_labels": True, "show_legend": True, "label_type": "key_percent",
        **base_common,
    }))

    # 4. 门店 TopN（表格）
    charts.append(make_chart(token, "④ 门店销售 Top10", "table", d_store, {
        "viz_type": "table", "datasource": f"{d_store}__table",
        "groupby": ["store_name", "province"],
        "metrics": [metric("gmv", "GMV"), metric("order_cnt", "订单量"), metric("aov", "客单价")],
        "order_desc": True, "page_length": 10,
        **base_common,
    }))

    # 5. 月度 GMV（柱状）
    charts.append(make_chart(token, "⑤ 月度 GMV", "bar", d_month, {
        "viz_type": "bar", "datasource": f"{d_month}__table",
        "x_axis": "stat_month", "metrics": [metric("gmv", "GMV")],
        "groupby": [], "show_legend": False,
        **base_common,
    }))

    # 6. 省份销售分布（横向柱状，地图在大屏用 ECharts 实现）
    charts.append(make_chart(token, "⑥ 省份销售分布", "bar", d_store_m, {
        "viz_type": "bar", "datasource": f"{d_store_m}__table",
        "x_axis": "province", "metrics": [metric("gmv", "GMV")],
        "groupby": [], "show_legend": False, "order_desc": True,
        **base_common,
    }))

    ids = [c for c in charts if c]

    # 创建仪表板
    code, body = call("/api/v1/dashboard/", token=token)
    dash_id = None
    for r in body.get("result", []):
        if r["dashboard_title"] == "云购生活 · 经营分析看板":
            dash_id = r["id"]
    if dash_id is None:
        code, body = call("/api/v1/dashboard/", {
            "dashboard_title": "云购生活 · 经营分析看板",
            "published": True,
        }, token)
        if code in (200, 201):
            dash_id = body.get("id")
            print(f"  [OK] 仪表板已创建 (id={dash_id})")
        else:
            print(f"  [X] 仪表板创建失败 {code} {body}")

    print(f"\n图表 {len(ids)} 个，仪表板 id={dash_id}")
    print(f"打开：{BASE}/chart/list/ 与 {BASE}/dashboard/list/")


if __name__ == "__main__":
    main()
