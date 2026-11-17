# 第 4 周：Streamlit 问答应用镜像
# nl2sql 通过 `docker exec beeline` 查询 Hive，因此容器内需要 docker CLI，
# 并挂载宿主的 /var/run/docker.sock（见 docker-compose.yml）
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive

# 用 Debian 主源安装 docker.io（含 CLI），避免访问 download.docker.com
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true; \
    apt-get update && apt-get install -y --no-install-recommends docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /repo
RUN pip install --no-cache-dir streamlit pandas pymysql

EXPOSE 8501
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]