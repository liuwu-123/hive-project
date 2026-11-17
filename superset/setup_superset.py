# -*- coding: utf-8 -*-
"""第 4 周：通过 Superset REST API 自动注册数据库与数据集。

用法：
    python superset/setup_superset.py

做的事：
  1. 登录获取 access_token（admin / admin123）
  2. 注册 MySQL BI 集市（ydsh_ads）
  3. 为该库下 9 张表创建 Dataset（Superset 图表基于 Dataset）
"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:8088"
USER = "admin"
PASSWORD = "admin123"

SQLALCHEMY_URI = "mysql+pymysql://root:root@mysql:3306/ydsh_ads?charset=utf8mb4"
DB_NAME = "云购生活 BI 集市"

TABLES = [
    "ads_kpi_overview", "ads_sales_daily", "ads_category_topn", "ads_store_topn",
    "ads_user_value", "dws_sales_month", "dws_category_month", "dws_store_month",
    "dws_channel_month",
]


def call(path, payload=None, token=None, method=None):
    url = BASE + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        return e.code, detail


def main():
    # 1. 登录
    code, body = call("/api/v1/security/login",
                      {"username": USER, "password": PASSWORD, "provider": "db", "refresh": True})
    if code != 200:
        print("登录失败:", code, body)
        sys.exit(1)
    token = body["access_token"]
    print("登录成功，token 已获取")

    # 2. 查询是否已存在同名数据库
    code, body = call("/api/v1/database/", token=token)
    db_id = None
    if code == 200:
        for item in body.get("result", []):
            if item.get("database_name") == DB_NAME:
                db_id = item["id"]
                print(f"数据库已存在：{DB_NAME} (id={db_id})")

    if db_id is None:
        code, body = call("/api/v1/database/", {
            "database_name": DB_NAME,
            "sqlalchemy_uri": SQLALCHEMY_URI,
            "expose_in_sqllab": True,
            "allow_run_async": False,
            "allow_ctas": False,
            "allow_cvas": False,
            "allow_dml": False,
            "extra": json.dumps({"metadata_params": {}, "engine_params": {}}),
        }, token=token)
        if code not in (200, 201):
            print("创建数据库失败:", code, body)
            sys.exit(1)
        db_id = body["id"]
        print(f"数据库已创建：{DB_NAME} (id={db_id})")

    # 3. 创建数据集
    code, body = call("/api/v1/dataset/", token=token)
    existing = {r["table_name"] for r in body.get("result", [])} if code == 200 else set()

    created = 0
    for t in TABLES:
        if t in existing:
            print(f"  数据集已存在：{t}")
            continue
        code, body = call("/api/v1/dataset/", {
            "database": db_id,
            "schema": "ydsh_ads",
            "table_name": t,
        }, token=token)
        if code in (200, 201):
            created += 1
            print(f"  数据集已创建：{t} (id={body.get('id')})")
        else:
            print(f"  数据集创建失败：{t} -> {code} {body}")

    print(f"\n完成：数据库 1 个，新建数据集 {created} 个")
    print(f"访问地址：{BASE}　账号 {USER} / {PASSWORD}")


if __name__ == "__main__":
    main()
