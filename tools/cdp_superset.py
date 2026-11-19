# -*- coding: utf-8 -*-
"""通过 CDP 自动登录 Superset 并截取仪表板。

用法：
    python tools/cdp_superset.py <输出png> [仪表板id] [等待秒数]
"""
import base64
import json
import subprocess
import sys
import time
import urllib.request

import websocket

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE = "http://localhost:8088"


def main():
    out = sys.argv[1]
    dash_id = sys.argv[2] if len(sys.argv) > 2 else "1"
    wait = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    width, height = 1920, 1080

    port = 9334
    proc = subprocess.Popen([
        EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--remote-debugging-port={port}", f"--window-size={width},{height}",
        "--user-data-dir=" + r"E:\dssgz\shots\edge-profile-superset", "about:blank",
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
            raise SystemExit("无法连接调试端口")

        ws = websocket.create_connection(ws_url, timeout=90)
        mid = [0]

        def send(method, params=None):
            mid[0] += 1
            ws.send(json.dumps({"id": mid[0], "method": method, "params": params or {}}))
            while True:
                msg = json.loads(ws.recv())
                if msg.get("id") == mid[0]:
                    return msg.get("result", {})

        send("Page.enable")
        send("Runtime.enable")
        send("Emulation.setDeviceMetricsOverride",
             {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})

        # 1) 登录页
        send("Page.navigate", {"url": BASE + "/login/"})
        time.sleep(5)
        js = """
        (function(){
          const u = document.querySelector('#username') || document.querySelector('input[name=username]');
          const p = document.querySelector('#password') || document.querySelector('input[name=password]');
          if(!u || !p) return 'no-form';
          u.value='admin'; p.value='admin123';
          u.dispatchEvent(new Event('input',{bubbles:true}));
          p.dispatchEvent(new Event('input',{bubbles:true}));
          let btn = document.querySelector('button[type=submit]');
          if(!btn){ btn = [...document.querySelectorAll('button')].find(b => /登录|Sign in|Login/i.test(b.innerText||'')); }
          if(btn){ btn.click(); return 'clicked:' + (btn.innerText||'').trim(); }
          const f = document.querySelector('form');
          if(f){ f.submit(); return 'form-submit'; }
          return 'no-button';
        })()
        """
        r = send("Runtime.evaluate", {"expression": js, "returnByValue": True})
        print("登录动作:", r.get("result", {}).get("value"))
        time.sleep(6)

        # 2) 仪表板
        send("Page.navigate", {"url": f"{BASE}/superset/dashboard/{dash_id}/"})
        print(f"等待仪表板渲染 {wait} 秒 ...")
        time.sleep(wait)

        res = send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
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
