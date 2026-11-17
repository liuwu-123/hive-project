"""第 4 周：Superset 配置

密钥与数据库连接全部从环境变量读取，不硬编码；
.env 中提供 SUPERSET_SECRET_KEY 与 SUPERSET_DB_URI。
"""
import os

# 会话加密密钥（必须固定，否则重启后登录失效）
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "change-me-in-env")

# Superset 自身元数据库（存用户、图表、仪表板定义）
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_DB_URI",
    "mysql+pymysql://root:root@mysql:3306/superset?charset=utf8mb4",
)

# 中文界面与本地化
BABEL_DEFAULT_LOCALE = "zh"
LANGUAGES = {"zh": {"flag": "cn", "name": "Chinese"}, "en": {"flag": "us", "name": "English"}}

# 关闭示例数据，避免启动慢
SUPERSET_LOAD_EXAMPLES = False

# 图表查询上限，防止大屏误查全表
ROW_LIMIT = 50000

# 允许嵌入（Streamlit / ECharts 如需 iframe 引用仪表板）
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}

# 时区
DEFAULT_TIMEZONE = "Asia/Shanghai"
# 本地演示环境：关闭 CSRF，便于用 REST API 批量初始化数据集与图表
# 生产环境必须开启，并通过 /api/v1/security/csrf_token/ 获取令牌
WTF_CSRF_ENABLED = False