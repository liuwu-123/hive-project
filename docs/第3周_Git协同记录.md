# 第 3 周 · Git 团队协同记录

> 团队：云仓五号　仓库：`github.com/liuwu-123/hive-project`　记录日期：2026-11-10
> 说明：本文记录一次完整的团队协作流程——Fork → Pull Request → Code Review → 冲突解决 → 合并 → 版本发布 → Issue 追踪。

---

## 一、协作流程总览

```
主仓库 liuwu-123/hive-project
        │
        ├─ ① 队友 Fork → YeHWeh1/hive-project（独立副本）
        │
        ├─ ② 在副本建分支 feature/readme-week3 → 修改 README.md
        │
        ├─ ③ 提交 Pull Request #1（源：YeHWeh1:feature/readme-week3 → 目标：liuwu-123:main）
        │
        ├─ ④ 本人 Review → Request changes（提出 3 条具体意见）
        │
        ├─ ⑤ 队友按意见修改 + merge upstream/main
        │
        ├─ ⑥ 期间主分支也修改了同一处 → 产生真实冲突 → 队友解决
        │
        ├─ ⑦ 复审 → Approve → Merge（合并提交 4a31e9d）
        │
        ├─ ⑧ 打 tag v1.0-week3 → 发布 Release
        │
        └─ ⑨ 建立 Issue #2 / #3 / #4 追踪后续任务
```

---

## 二、关键节点记录

| 时间（UTC+8） | 事件 | 详情 |
|---|---|---|
| 11-10 09:29 | 收到 PR 链接 | 队友 `YeHwH1` 提交 PR #1，改 `README.md`（+6/−1） |
| 11-10 09:34 | 第 1 轮 Review | 本人提交 **Request changes**，提出 3 条意见 |
| 11-10 09:59 | 制造冲突 | 主分支同步补写「第 3 周计划」，与 PR 修改同一区域 |
| 11-10 10:20 | 队友响应 | 按意见细化 5 条计划、补末尾换行、`merge upstream/main` 解决冲突 |
| 11-10 10:31 | 第 2 轮 Review | 本人提交 **Approve** |
| 11-10 10:32 | 合并 | Squash 合并为 `4a31e9d`，PR #1 关闭 |
| 11-10 10:37 | 版本发布 | 打 `v1.0-week3` 标签，发布 Release「第 3 周阶段交付」 |
| 11-10 10:39 | Issue 建档 | #2 增强、#3 数据核对、#4 文档 |

---

## 三、Pull Request #1 详情

| 项 | 内容 |
|---|---|
| 编号 | #1 |
| 标题 | `docs: 补充第3周计划` |
| 作者 | `YeHwH1`（Fork 自 `liuwu-123/hive-project`） |
| 源分支 | `YeHwH1:feature/readme-week3` |
| 目标分支 | `liuwu-123:main` |
| 提交数 | 3（`a1205b7` 初稿 → `c71477b` 按意见细化 → `8cdd9fd` 解决冲突） |
| 改动 | `README.md` +13 / −8 |
| 合并方式 | Merge pull request，合并提交 `4a31e9d` |

---

## 四、Code Review 记录（2 轮）

### 第 1 轮：Request changes（09:34）

评审意见原文：

> 建议把「第3周计划」写具体一些，当前两句过于笼统。理由：
> 1. 第3周任务书实际有 5 个子任务（DWS/ADS+KPI、时间序列预测、NL2SQL、AI 洞察、Git 协同），建议按这 5 项列条目，而不是笼统的「课程练习」。
> 2. 每条请补上对应产出物，便于后续追溯：DWS/ADS → `sql/dws/`、`sql/ads/`；预测 → `analysis/forecast_gmv.py`；NL2SQL → `nl2sql/`；AI 洞察 → `insight/ai_insight.py`。
> 3. README 末尾缺少换行（diff 显示 No newline at end of file），建议补上。

### 队友的修改（10:20）

- 第 3 周计划细化为 5 条，每条带产出物路径
- README 末尾补换行
- `git fetch upstream` + `git merge upstream/main` 解决冲突
- **额外修复**：主分支 README 中存在两处字符错误——`␇nalysis/`（控制字符 BEL 混入）与 `nl2sql/` 前被换行截断

### 第 2 轮：Approve（10:31）

> 冲突已解决，第3周计划已细化为 5 条并附产出物路径；顺带修复了主分支 README 中的控制字符与换行截断问题，确认无误。

---

## 五、冲突产生与解决过程

### 冲突原因

两边同时修改了 `README.md` 的同一区域（文件末尾）：

- **主分支**（本人）：新增「十、第 3 周计划（主分支）」，列 5 条
- **PR 分支**（队友）：在末尾新增「十、第3周计划」，2 条

`git merge-tree` 验证结果：

```
changed in both
+<<<<<<< .our
+>>>>>>> .their
```

### 解决方式（队友执行）

```bash
git remote add upstream https://github.com/liuwu-123/hive-project.git
git fetch upstream
git checkout feature/readme-week3
git merge upstream/main
# 手工合并 README.md：保留我方 5 条结构，补充主分支的库名与表数细节，删除冲突标记
git add README.md
git commit -m "fix: 按 review 意见细化第3周计划并解决 README 合并冲突"
git push origin feature/readme-week3
```

### 解决结果

合并后主分支的「十、第 3 周计划」为最终版本：

```markdown
1. DWS / ADS 与 KPI：建 ydsh_dws、ydsh_ads 两个库，产出 5 张汇总表 + 5 张应用表……
2. 时间序列预测：……脚本 analysis/forecast_gmv.py，报告 docs/预测建模分析报告.docx
3. NL2SQL：自然语言转 Hive SQL……代码在 nl2sql/，10 题测试全部通过
4. AI 智能洞察：……脚本 insight/ai_insight.py，报告 docs/第3周_AI经营分析摘要.docx
5. Git 协同：走通 Fork → Pull Request → Code Review → 合并冲突解决 的完整流程
```

验证：合并后 `README.md` 中 BEL(0x07) 控制字符数量为 **0**，两处字符错误已消除。

---

## 六、版本发布

| 项 | 内容 |
|---|---|
| 标签 | `v1.0-week3`（附注标签，含交付说明） |
| Release | 「第 3 周阶段交付」 |
| 发布时间 | 2026-11-10 02:37 UTC |
| 对应提交 | `4a31e9d` |

标签命令：

```bash
git tag -a v1.0-week3 -m "第3周交付：DWS/ADS+KPI、时间序列预测、NL2SQL、AI 智能洞察、Git 协同"
git push origin v1.0-week3
```

---

## 七、Issue 追踪

| 编号 | 标题 | 类型 | 来源 |
|---|---|---|---|
| #2 | [增强] NL2SQL 支持多轮上下文追问 | 功能增强 | NL2SQL 开发时发现单轮限制 |
| #3 | [数据] 核对品类销售额与订单 GMV 的 14.21 倍口径差异 | 数据问题 | 指标定义文档 3.1 节 |
| #4 | [文档] 第 4 周接入 Superset + ECharts 可视化看板 | 文档/规划 | ADS 层已就绪 |

> 说明：创建 Issue 时 GitHub 前端曾报「Unable to create issue」，刷新并改从 Issues 标签页入口后创建成功；标签（Label）未附加，后续可补。

---

## 八、协同收获与问题

### 做对了什么

1. **Review 意见必须具体**。第一轮给的是「按 5 个子任务列条目 + 补产出物路径 + 补末尾换行」，队友能直接照做；如果只写「建议写详细些」，等于没说。
2. **冲突是设计出来的**。主分支与 PR 分支同时改同一段，冲突必然发生且可控，比"碰运气"更可靠。
3. **Fork 前先确认仓库可见性**。私有仓库无法被 Fork，必须先把仓库改为 Public。

### 踩到的坑

| 问题 | 原因 | 处理 |
|---|---|---|
| 私有仓库没有 Fork 按钮 | GitHub 不允许 Fork 私有仓库 | 仓库改为 Public（确认无密钥、无数据、无简历） |
| README 混入控制字符 `␇nalysis/` | 用 PowerShell 双引号 here-string 写 Markdown 时，反引号 `` ` `` 被当作转义符，``` `a ``` 变成 BEL(0x07) | 队友 Review 时发现并修复；后续写 README 改用单引号字符串或 `git commit` 直接提交 |
| 创建 Issue 报「Unable to create issue」 | 前端临时故障/会话问题 | 强制刷新技术 + 从 Issues 标签页进入后成功 |

### 对团队协作的启示

- **PR 不需要大**。本次只改 1 个文件、13 行，Review 5 分钟看完，这才是可维护的协作粒度。
- **Review 是双向的**。队友在这次 Review 中反过来发现了主分支的字符错误——评审不是单向挑错。
- **留痕比结果重要**。任务书要的是「过程可追溯」，所以每个节点（PR 编号、Review 意见、冲突解决、tag、Issue）都要有记录。
