# -*- coding: utf-8 -*-
"""第 4 周 · 子任务 3：Streamlit 对话式问答应用

把第 3 周的 NL2SQL 接进来，形成「提问 → 生成 SQL → 执行 → 表格/图表」闭环。

启动：
    streamlit run app/streamlit_app.py
访问：
    http://localhost:8501
"""
import os
import sys
import time

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from nl2sql import engine, main as cli, prompts  # noqa: E402

st.set_page_config(page_title="云购生活 · 智能经营问答", page_icon="💬", layout="wide")

# ---------------- 侧边栏 ----------------
with st.sidebar:
    st.markdown("### 关于")
    st.caption("基于第 3 周 NL2SQL 能力：自然语言 → Hive SQL → 执行 → 结果")
    st.markdown("### 推荐问题")
    samples = [
        "2024 年 6 月的 GMV 是多少",
        "销量最高的前 5 个品类",
        "各渠道的客单价对比",
        "各会员等级的客单价是多少",
        "哪个门店的 GMV 最高",
    ]
    clicked = None
    for s in samples:
        if st.button(s, use_container_width=True):
            clicked = s
    st.divider()
    if st.button("清空对话", use_container_width=True):
        st.session_state.history = []
        st.rerun()

st.title("云购生活 · 智能经营问答")
st.caption("用中文提问，系统自动生成 Hive SQL 并返回结果")

if "history" not in st.session_state:
    st.session_state.history = []

# ---------------- 输入 ----------------
with st.form("ask", clear_on_submit=True):
    question = st.text_input("请输入问题", placeholder="例如：2024 年 6 月 GMV 最高的前 3 家门店")
    submitted = st.form_submit_button("提问", type="primary")

if clicked:
    question = clicked
    submitted = True


@st.cache_resource(show_spinner=False)
def system_prompt():
    """Schema 只需加载一次。"""
    from nl2sql import schema_loader
    schema = schema_loader.load()
    return prompts.SYSTEM.replace("{schema}", schema_loader.as_prompt_text(schema))


def ask(q):
    t0 = time.time()
    sp = system_prompt()
    with st.spinner("正在生成 SQL ..."):
        text, usage = engine.llm_call(sp, prompts.USER_TEMPLATE.format(question=q))
    sql, reason = engine.extract_sql(text)
    if not sql:
        return {"question": q, "error": "模型未返回可解析的 SQL", "raw": text[:400]}

    ok, why = engine.guard(sql)
    if not ok:
        return {"question": q, "sql": sql, "error": f"SQL 被拦截：{why}"}

    with st.spinner("正在执行查询 ..."):
        header, rows, out = engine.execute(sql)
    err = engine.check_error(out)
    if err:
        return {"question": q, "sql": sql, "error": f"执行失败：{err}"}

    df = pd.DataFrame(rows, columns=header)
    # 数值列转换，便于画图
    for c in df.columns:
        try:
            df[c] = pd.to_numeric(df[c])
        except (ValueError, TypeError):
            pass
    return {"question": q, "sql": sql, "reason": reason, "df": df,
            "elapsed": round(time.time() - t0, 2), "tokens": usage.get("total_tokens")}


# ---------------- 处理提问 ----------------
# 支持链接直达：?q=问题内容（便于分享与截图演示）
_qp = st.query_params.get("q")
if isinstance(_qp, list):
    _qp = _qp[0] if _qp else None
if _qp and submitted is False:
    question = _qp
    submitted = True
    st.query_params.clear()

if submitted and question:
    result = ask(question)
    st.session_state.history.insert(0, result)

# ---------------- 历史对话 ----------------
for i, item in enumerate(st.session_state.history):
    with st.chat_message("user"):
        st.write(item["question"])

    with st.chat_message("assistant"):
        if item.get("error"):
            st.error(item["error"])
            if item.get("sql"):
                st.code(item["sql"], language="sql")
            continue

        if item.get("reason"):
            st.caption(f"思路：{item['reason']}")
        st.code(item["sql"], language="sql")

        df = item["df"]
        st.dataframe(df, use_container_width=True, height=min(360, 38 * (len(df) + 1)))

        # 单指标 → 指标卡；两列（名称 + 数值）→ 柱状图
        num_cols = df.select_dtypes("number").columns.tolist()
        if len(df) == 1 and len(num_cols) == 1:
            v = df[num_cols[0]].iloc[0]
            st.metric(num_cols[0], f"{v:,.2f}")
        elif 1 < len(df) <= 20 and num_cols:
            label_col = df.columns[0]
            try:
                st.bar_chart(df.set_index(label_col)[num_cols[0]])
            except Exception:
                pass

        st.caption(f"耗时 {item.get('elapsed', '-')} 秒　token {item.get('tokens', '-')}")

if not st.session_state.history:
    st.info("在左侧点推荐问题，或直接输入你的问题开始。")
