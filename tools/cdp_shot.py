# -*- coding: utf-8 -*-
"""用 Chrome DevTools Protocol 截取页面（等待渲染完成后再截图）。

用法：
    python tools/cdp_shot.py <url> <输出png> [等待秒数] [宽] [高]

为什么不用 `msedge --screenshot`：
    那个模式在页面 JS 渲染完成前就截图，Streamlit 这类靠 WebSocket 拉数据的页面
    只会截到骨架屏。CDP 可以等指定时间后再截。
"""
import base64
import json
import subprocess
import sys
import time
import urllib.request

import websocket

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_edge():
    import os
    for p in EDGE_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit("未找到 Edge")


def main():
    url = sys.argv[1]
    out = sys.argv[2]
    wait = int(sys.argv[3]) if len(sys.argv) > 3 else 15
    width = int(sys.argv[4]) if len(sys.argv) > 4 else 1600
    height = int(sys.argv[5]) if len(sys.argv) > 5 else 1200

    port = 9333
    proc = subprocess.Popen([
        find_edge(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--remote-debugging-port={port}",
        f"--window-size={width},{height}",
        "--user-data-dir=" + r"E:\dssgz\shots\edge-profile",
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        ws_url = None
        for _ in range(40):
            time.sleep(0.5)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=2) as r:
                    tabs = json.loads(r.read().decode())
                pages = [t for t in tabs if t.get("type") == "page"]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                continue
        if not ws_url:
            raise SystemExit("无法连接浏览器调试端口")

        ws = websocket.create_connection(ws_url, timeout=60)
        mid = [0]

        def send(method, params=None):
            mid[0] += 1
            ws.send(json.dumps({"id": mid[0], "method": method, "params": params or {}}))
            while True:
                msg = json.loads(ws.recv())
                if msg.get("id") == mid[0]:
                    return msg.get("result", {})

        send("Page.enable")
        send("Emulation.setDeviceMetricsOverride",
             {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
        send("Page.navigate", {"url": url})
        print(f"已打开 {url}，等待 {wait} 秒渲染 ...")
        time.sleep(wait)

        res = send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
        data = base64.b64decode(res["data"])
        with open(out, "wb") as f:
            f.write(data)
        print(f"已保存 {out}（{len(data)/1024:.0f} KB）")
        ws.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
