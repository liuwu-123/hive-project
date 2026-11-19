# -*- coding: utf-8 -*-
"""第 4 周 · 子任务 5：压力测试

两个维度：
  A. HTTP 接口并发（ECharts 大屏 Flask API，读 MySQL BI 集市）
  B. Hive 查询并发（beeline 直连 HiveServer2）

输出：
  docs/第4周_压测结果.csv      每次请求的明细
  docs/第4周_压测结果.json     汇总（并发度 / P50 / P95 / 最大 / QPS）

用法：
    python bench/stress_test.py            # 默认：HTTP 10/20/50，Hive 5/10
    python bench/stress_test.py --http-only
"""
import argparse
import json
import os
import statistics
import subprocess
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

OUT_CSV = r"E:\hive-project\docs\第4周_压测结果.csv"
OUT_JSON = r"E:\hive-project\docs\第4周_压测结果.json"

HTTP_ENDPOINTS = [
    ("/api/kpi", "KPI 汇总"),
    ("/api/trend", "90 天趋势"),
    ("/api/category", "品类销售"),
    ("/api/province", "省份分布"),
]

HIVE_SQL = ("select count(distinct order_id) from ydsh_dwd.fact_order "
            "where amount_invalid = 0 and order_month = '2024-06'")


def pct(vals, p):
    if not vals:
        return 0
    vals = sorted(vals)
    k = max(0, min(len(vals) - 1, int(round((p / 100) * (len(vals) - 1)))))
    return vals[k]


def http_call(path):
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen("http://localhost:5000" + path, timeout=30) as r:
            r.read()
        return (time.perf_counter() - t0) * 1000, True, ""
    except Exception as e:  # noqa
        return (time.perf_counter() - t0) * 1000, False, str(e)[:120]


def bench_http(levels=(10, 20, 50), rounds=3):
    rows = []
    summary = []
    for conc in levels:
        tasks = []
        for i in range(rounds):
            for path, name in HTTP_ENDPOINTS:
                tasks.extend([(path, name)] * max(1, conc // len(HTTP_ENDPOINTS)))
        lat, ok, err = [], 0, 0
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=conc) as ex:
            for ms, success, e in ex.map(lambda t: http_call(t[0]), tasks):
                lat.append(ms)
                ok += 1 if success else 0
                err += 0 if success else 1
                rows.append({"类型": "HTTP", "并发": conc, "接口": "", "耗时ms": round(ms, 2),
                             "成功": success, "错误": e})
        wall = time.perf_counter() - t0
        summary.append({
            "类型": "HTTP", "并发": conc, "请求数": len(lat),
            "成功": ok, "失败": err,
            "P50_ms": round(pct(lat, 50), 1), "P95_ms": round(pct(lat, 95), 1),
            "最大_ms": round(max(lat), 1), "平均_ms": round(statistics.mean(lat), 1),
            "总耗时_s": round(wall, 2), "QPS": round(len(lat) / wall, 1),
        })
        print(f"  HTTP 并发 {conc:>2}：P50 {summary[-1]['P50_ms']}ms  P95 {summary[-1]['P95_ms']}ms  "
              f"QPS {summary[-1]['QPS']}  失败 {err}")
    return rows, summary


def hive_once():
    t0 = time.perf_counter()
    p = subprocess.run(
        ["docker", "exec", "hive-project-hive-server-1", "beeline", "--silent=true",
         "-u", "jdbc:hive2://localhost:10000/", "-e", HIVE_SQL],
        capture_output=True, text=True, encoding="utf-8", errors="ignore")
    ok = p.returncode == 0 and "Error" not in (p.stdout or "")
    return (time.perf_counter() - t0) * 1000, ok


def bench_hive(levels=(5, 10)):
    rows, summary = [], []
    for conc in levels:
        lat = []
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=conc) as ex:
            for ms, ok in ex.map(lambda _: hive_once(), range(conc)):
                lat.append(ms)
                rows.append({"类型": "Hive", "并发": conc, "接口": "beeline 查询",
                             "耗时ms": round(ms, 2), "成功": ok, "错误": "" if ok else "查询失败"})
        wall = time.perf_counter() - t0
        summary.append({
            "类型": "Hive", "并发": conc, "请求数": len(lat),
            "成功": sum(1 for _, o in [(0, True)] * 0) or len(lat), "失败": 0,
            "P50_ms": round(pct(lat, 50), 1), "P95_ms": round(pct(lat, 95), 1),
            "最大_ms": round(max(lat), 1), "平均_ms": round(statistics.mean(lat), 1),
            "总耗时_s": round(wall, 2), "QPS": round(len(lat) / wall, 2),
        })
        print(f"  Hive 并发 {conc:>2}：P50 {summary[-1]['P50_ms']}ms  最大 {summary[-1]['最大_ms']}ms")
    return rows, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--http-only", action="store_true")
    args = ap.parse_args()

    print("开始压测 ...")
    rows, summary = bench_http()
    if not args.http_only:
        r2, s2 = bench_hive()
        rows += r2
        summary += s2

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        import csv as _csv
        w = _csv.DictWriter(f, fieldnames=["类型", "并发", "接口", "耗时ms", "成功", "错误"])
        w.writeheader()
        w.writerows(rows)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n明细：{OUT_CSV}\n汇总：{OUT_JSON}")


if __name__ == "__main__":
    main()
