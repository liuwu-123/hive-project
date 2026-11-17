# 第 4 周：ECharts 大屏（Flask 数据接口 + 静态页面）
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    TZ=Asia/Shanghai

WORKDIR /app
RUN pip install --no-cache-dir flask pymysql

COPY . /app

EXPOSE 5000
CMD ["python", "api.py"]
