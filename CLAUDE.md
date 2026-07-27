# AI 日报 — CLAUDE.md

## 项目简介
网页版 AI 日报：聚合 AI 领域信息源的每日资讯，纯静态前端，GitHub Pages 托管，GitHub Actions 每天自动更新。当前在第三版基础上新增独立学习页「工程解码」。

## 当前阶段
**第四版已完成：工程解码模块**（独立累积学习页，帮非技术 PM 建立技术边界判断力 + vibe coding 企业闭环认知）。
本地五块验证通过，待上线让 Actions 用线上 key 首跑核对 DeepSeek 筛选质量。规格见 `_harness/spec.md` 第四版，验收场景见 `_harness/eval-scenarios.md`。

## 关键约束（必读）
- **走 harness 流程**：一次只做一块，checkpoint → 执行 → 验收，没批准不跳到下一块
- 不允许自行添加 spec 之外的功能
- 破坏性操作（删文件、推代码、发外部请求）执行前必须先确认
- **不改动现有 11 板块与 `data/YYYY-MM-DD.json` 每日数据的逻辑**——工程解码隔离在 `data/learning.json`
- **不安装 AI HOT 第三方 skill**，只走其 REST 只读接口
- 全中文输出；内容只增不减（改交付物先做完整性核对，不静默删除）
- 大改前先做版本快照到 `_versions/`

## 技术栈
纯 HTML/CSS/JS 前端 · Python 采集（`scripts/`）· DeepSeek API 处理 · GitHub Actions 定时 · GitHub Pages 部署

## 重要文件
- `_harness/spec.md` — 需求规格（含第四版：工程解码）
- `_harness/handoff.md` — 项目状态与交接
- `data/learning.json` — 工程解码累积数据（第四版新增）
- `scripts/config.py` — 信息源配置
- `scripts/ai_processor.py` — DeepSeek 处理（将新增 `curate_tech_learning()`）
- `_versions/v3.0-baseline/` — 第四版开工前的可回滚快照

## 禁止行为
- 不在没有 checkpoint 的情况下跨任务块执行
- 不修改 spec 里标注"暂不处理（v2）"的功能（已读/收藏/月度精粹）
- **不把 token / 密钥等凭证写进任何会进 git 的文件**（注：handoff.md 历史遗留了明文 GitHub token，待清理并吊销）
