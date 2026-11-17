# 第 4 周：Superset 定制镜像
# 官方镜像默认没有 MySQL 驱动，这里补装 pymysql + cryptography，
# 使其既能用 MySQL 存元数据，也能连接 MySQL BI 集市。
FROM apache/superset:3.1.3

USER root
# 使用国内镜像源，避免构建时访问 PyPI 超时
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
        pymysql \
        cryptography
USER superset