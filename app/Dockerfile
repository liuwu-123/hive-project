# 第 4 周：Streamlit 问答应用镜像
# nl2sql 通过 `docker exec beeline` 查询 Hive：
#   - 镜像内放置 docker CLI 静态二进制（Debian 的 docker.io 包不含 CLI）
#   - 运行时挂载宿主 /var/run/docker.sock（见 docker-compose.yml）
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive

# 静态 docker CLI（从清华镜像下载的 docker-27.3.1 中提取）
COPY bin/docker /usr/local/bin/docker
RUN chmod +x /usr/local/bin/docker && docker --version

WORKDIR /repo
RUN pip install --no-cache-dir streamlit pandas pymysql

EXPOSE 8501
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]