# -*- coding: utf-8 -*-
"""打包第 5 周源代码提交包（排除虚拟环境、缓存、密钥、原始数据）。"""
import os
import zipfile

ROOT = r"E:\hive-project"
OUT = r"E:\hive-project\第5周_源代码.zip"

INCLUDE_DIRS = ["web", "superset", "app", "nl2sql", "sync", "analysis", "insight", "bench", "scripts", "sql", "tools"]
INCLUDE_FILES = ["docker-compose.yml", "README.md", "README.zh-CN.md", ".gitignore"]

EXCLUDE_DIRS = {"__pycache__", ".venv", ".git", "node_modules", "screenshots", "bin"}
EXCLUDE_EXT = {".pyc", ".pyo", ".log", ".zip"}
EXCLUDE_FILES = {".env"}

count = 0
total = 0
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in INCLUDE_FILES:
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            z.write(p, f)
            count += 1
            total += os.path.getsize(p)

    for d in INCLUDE_DIRS:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            print(f"  [跳过] {d} 不存在")
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames if x not in EXCLUDE_DIRS]
            for fn in filenames:
                if fn in EXCLUDE_FILES:
                    continue
                ext = os.path.splitext(fn)[1].lower()
                if ext in EXCLUDE_EXT:
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, ROOT)
                z.write(full, rel.replace("\\", "/"))
                count += 1
                total += os.path.getsize(full)

print(f"已生成 {OUT}")
print(f"  文件数：{count}")
print(f"  原始大小：{total/1024/1024:.2f} MB")
print(f"  压缩后：{os.path.getsize(OUT)/1024/1024:.2f} MB")
