# 第 4 周 · API 与密钥配置指南

> 团队：云仓五号　日期：2026-11-19
> 涉及：DeepSeek API Key、Superset SECRET_KEY、MySQL 密码

---

## 一、密钥清单

| 密钥 | 用途 | 存放位置 | 谁能看到 |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | NL2SQL、AI 洞察调用大模型 | `.env` → 容器环境变量 | app 容器、本机 |
| `SUPERSET_SECRET_KEY` | Superset 会话加密 | `.env` → 容器环境变量 | superset 容器 |
| MySQL root 密码 | 集市与元数据库 | compose 环境变量 | mysql / superset / web 容器 |
| 用户登录密码 | Superset admin | Superset 元数据库（哈希存储） | 仅使用者 |

---

## 二、配置方式

### 2.1 本机开发

项目根目录 `.env`（**已在 `.gitignore`，不会被提交**）：

```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
SUPERSET_SECRET_KEY=40位随机字符串
```

生成随机密钥：

```powershell
-join ((1..40) | ForEach-Object { 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'[(Get-Random -Maximum 62)] })
```

### 2.2 容器运行时

`docker-compose.yml` 中**只引用变量，不写明文**：

```yaml
superset:
  environment:
    SUPERSET_SECRET_KEY: ${SUPERSET_SECRET_KEY:-dev-secret-key-change-me}
    SUPERSET_DB_URI: mysql+pymysql://root:root@mysql:3306/superset?charset=utf8mb4

app:
  env_file:
    - .env            # 整份注入，代码用 os.environ 读取
```

### 2.3 代码读取

```python
import os
# 优先读环境变量，回退到 .env（本机开发时）
key = os.environ.get("DEEPSEEK_API_KEY")
```

**禁止**出现：

```python
client = OpenAI(api_key="sk-123456")   # ✗ 硬编码，绝对不行
```

---

## 三、密钥安全四条规则

| 规则 | 做法 | 本项目落地 |
|---|---|---|
| **1. 不落仓库** | `.gitignore` 排除 `.env`、`*.key` | 已验证：`git check-ignore -v .env` → `.gitignore:5:.env`；`git ls-files .env` 为空 |
| **2. 不入日志** | 打印时掩码 | 启动脚本输出 `sk-445e***413d`，只留前 6 位 + 后 4 位 |
| **3. 不写代码** | 只从环境变量读 | `nl2sql/engine.py` 的 `load_env()` 读 `.env` 或 `os.environ` |
| **4. 定期轮换** | 泄露或到期后重建 | 见第四节 |

---

## 四、密钥轮换流程

```powershell
# 1) 平台侧吊销旧 Key、创建新 Key
# 2) 更新本地 .env
(Get-Content .env) -replace '^DEEPSEEK_API_KEY=.*', 'DEEPSEEK_API_KEY=sk-新值' | Set-Content .env -Encoding ASCII

# 3) 重建使用该密钥的容器（env_file 改动不会自动生效）
docker compose up -d --force-recreate app

# 4) 验证
docker exec hive-project-app-1 python -c "import os;print('key ok' if os.environ.get('DEEPSEEK_API_KEY') else 'missing')"
```

Superset 的 `SUPERSET_SECRET_KEY` 轮换后需要**重新登录**（已有会话失效），仪表板与图表定义不受影响。

---

## 五、权限最小化建议

| 主体 | 当前权限 | 建议 |
|---|---|---|
| app 容器 | 可读 `.env`、可调 docker.sock | 生产环境改为「只读 API 网关」，不要挂 docker.sock |
| web 容器 | MySQL root | 建议建只读账号 `bi_reader`，只授予 `SELECT` on `ydsh_ads.*` |
| superset | MySQL root | 建议独立账号，仅 `superset` 库读写 + `ydsh_ads` 只读 |

只读账号示例（生产建议）：

```sql
CREATE USER 'bi_reader'@'%' IDENTIFIED BY '强密码';
GRANT SELECT ON ydsh_ads.* TO 'bi_reader'@'%';
FLUSH PRIVILEGES;
```

> 本项目为本地演示环境，为简化部署直接用了 root；上述建议已写入部署手册的「改进方向」。

---

## 六、检查清单（提交前自检）

```powershell
cd E:\hive-project

# 1) .env 是否被 Git 跟踪（必须为空）
git ls-files .env

# 2) .env 是否被忽略（应输出 .gitignore 行号）
git check-ignore -v .env

# 3) 仓库里是否残留密钥字符串
git grep -n "sk-" -- "*.py" "*.yml" "*.md"

# 4) 启动脚本是否做了掩码
Select-String -Path E:\dssgz\start3.ps1 -Pattern "sk-" 
```

四项检查全部通过，才算密钥管理合规。

---

## 七、常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| NL2SQL 报「未找到 DEEPSEEK_API_KEY」 | `.env` 未建，或容器未重建 | 建 `.env` → `docker compose up -d --force-recreate app` |
| 调用返回 401 | Key 失效或被吊销 | 重新创建 Key 并按第四节轮换 |
| 调用返回 402 | 余额不足 | 充值 |
| Superset 重启后登录失效 | `SUPERSET_SECRET_KEY` 未固定 | 在 `.env` 中固定该值，不要用默认值 |
| `git status` 出现 `.env` | 曾被 `git add -f` 强制加入 | `git rm --cached .env` 后提交 |
