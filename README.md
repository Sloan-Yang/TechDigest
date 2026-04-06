<div align="center">

# TechDigest

**AI-powered daily digest for arXiv, Hacker News, and GitHub Trending**  
**由 AI 驱动的每日精选 — arXiv 论文 · HN 热帖 · GitHub Trending**

[![Demo](https://img.shields.io/badge/Demo-Live-4f6ef7?style=flat-square)](https://sloan-yang.github.io/TechDigest/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/Runs%20on-GitHub%20Actions-2088FF?style=flat-square&logo=github-actions)](https://github.com/features/actions)

[English](#english) · [中文](#中文)

</div>

---

## English

### What is TechDigest?

TechDigest automatically fetches content from three sources every day, scores each item against **your personal interest profile** using an AI model (DeepSeek), generates summaries in Chinese, and publishes everything as a clean static website — with optional email and WeChat push notifications.

**You describe your interests once. The AI does the filtering every day.**

### Key Features

- **Three sources in one feed**
  - 📄 **arXiv** — filter papers by category and keyword, ranked by AI relevance score
  - 🔥 **Hacker News** — top 100 stories scored against your profile, with AI summaries
  - 🐙 **GitHub Trending** — daily trending repos scored and summarized

- **Fully personalized** — write a free-form interest profile in `config.yaml`; DeepSeek scores every item 0–100 against it

- **Zero server required** — runs entirely on GitHub Actions (free), deploys to GitHub Pages (free)

- **Smart deduplication** — seen paper IDs are cached so you never get the same paper twice

- **Multi-channel delivery** — static website + HTML email + WeChat (via Server酱)

- **Pluggable AI backend** — works with the official DeepSeek API or any OpenAI-compatible third-party endpoint

### Demo

> 👉 [sloan-yang.github.io/TechDigest](https://sloan-yang.github.io/TechDigest/)

### Quick Start

#### Step 1 — Fork this repo

Click **Fork** in the top-right corner to copy it to your GitHub account.

#### Step 2 — Edit `config.yaml`

Clone your fork and open `config.yaml`. The key fields to customize:

```yaml
# arXiv categories to watch (full list: https://arxiv.org/category_taxonomy)
categories:
  - cs.CV
  - cs.GR
  - cs.MM

# Keyword filter — paper must match at least one
keywords:
  - layout generation
  - diffusion
  - image generation

# Max papers recommended per day
max_papers_per_day: 5

# Your interest profile — DeepSeek scores every paper against this
preference:
  profile: >
    I'm a grad student in design intelligence, focused on layout generation,
    text-to-image models, and diffusion transformers. Not interested in
    medical imaging or clinical applications.

# Hacker News
hackernews:
  fetch_top_n: 100
  max_stories_per_day: 8
  preference:
    profile: >
      Interested in AI/ML tools, open-source projects, UI/design tools,
      LLMs, and developer productivity. Not interested in politics or finance.

# GitHub Trending
github_trending:
  max_repos_per_day: 8
  preference:
    profile: >
      Interested in AI, creative coding, design tools, Rust, game engines,
      and developer tools. Not interested in purely commercial projects.

# Site config
site:
  title: "TechDigest"
  base_url: "https://YOUR-USERNAME.github.io/YOUR-REPO/"

# DeepSeek API — change base_url if using a third-party provider
deepseek:
  model: deepseek-chat   # or gpt-4o-mini, claude-3-haiku, etc.
  base_url: "https://api.deepseek.com/v1"   # OpenAI: https://api.openai.com/v1
```

#### Step 3 — Add GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Description | Required |
|---|---|---|
| `LLM_API_KEY` | API key for your LLM provider (DeepSeek, OpenAI, etc.) | ✅ Yes |
| `EMAIL_SENDER` | Gmail address to send from | Optional |
| `EMAIL_PASSWORD` | Gmail App Password (16 chars, not your login password) | Optional |
| `EMAIL_RECIPIENT` | Email address to deliver to | Optional |
| `SERVERCHAN_KEY` | Server酱 SendKey for WeChat push | Optional |

**Gmail App Password**: Google Account → Security → 2-Step Verification → App passwords → Create

**Server酱 Key**: Visit [sct.ftqq.com](https://sct.ftqq.com), log in with GitHub, bind WeChat, copy your SendKey

#### Step 4 — Enable GitHub Pages

Repo → **Settings → Pages → Source → GitHub Actions** → Save

#### Step 5 — Push and trigger

```bash
git add .
git commit -m "configure my TechDigest"
git push
```

Then manually trigger the first run: **Actions → Daily ArXiv Digest → Run workflow**

It will run automatically every day at **6:00 AM Beijing time** (UTC 22:00).

### Local Run

```bash
pip install -r requirements.txt

export LLM_API_KEY=sk-...
export EMAIL_SENDER=you@gmail.com
export EMAIL_PASSWORD=your-app-password
export EMAIL_RECIPIENT=you@example.com

python scripts/run_all.py
```

### Project Structure

```
├── config.yaml                  # All configuration lives here
├── scripts/
│   ├── fetch_papers.py          # Fetch arXiv + DeepSeek scoring
│   ├── fetch_hn.py              # Fetch Hacker News + scoring + summaries
│   ├── fetch_github_trending.py # Fetch GitHub Trending + scoring + summaries
│   ├── summarize.py             # Generate Chinese summaries for papers
│   ├── generate_pages.py        # Build static HTML pages
│   ├── notify_email.py          # Send HTML email
│   ├── notify_wechat.py         # WeChat push via Server酱
│   └── run_all.py               # Local one-command runner
├── data/
│   ├── papers/                  # Daily paper JSON (one file per day)
│   ├── hn/                      # Daily HN JSON
│   ├── trending/                # Daily GitHub Trending JSON
│   ├── scores.json              # arXiv score cache (avoid re-scoring)
│   ├── hn_scores.json           # HN score cache
│   └── trending_scores.json     # Trending score cache
└── public/                      # Generated static site
```

### FAQ

**DeepSeek 401 error?**  
Check that `LLM_API_KEY` is correct and that `llm.base_url` in `config.yaml` matches your API provider's endpoint.

**GitHub Pages shows "Not Found"?**  
Confirm Settings → Pages → Source is set to "GitHub Actions", and that the `deploy` job completed successfully in the Actions tab.

**Email not sending?**  
Gmail requires an App Password, not your regular login password. You must have 2-Step Verification enabled to generate one.

---

## 中文

### TechDigest 是什么？

TechDigest 每天自动从三个来源抓取内容，用 AI 模型（DeepSeek）对照**你的个人兴趣画像**为每条内容打分，生成中文摘要，并发布为静态网站 —— 同时支持邮件和微信推送。

**你只需描述一次兴趣，AI 每天替你完成筛选。**

### 核心优势

- **三个来源，一个页面**
  - 📄 **arXiv** — 按分类和关键词抓取，AI 相关性打分排序
  - 🔥 **Hacker News** — Top 100 热帖按兴趣打分，附 AI 中文简介
  - 🐙 **GitHub Trending** — 每日趋势项目打分和摘要

- **高度个性化** — 在 `config.yaml` 中用自然语言描述你的兴趣，DeepSeek 对每条内容打 0–100 分

- **无需服务器** — 完全运行在 GitHub Actions（免费），部署到 GitHub Pages（免费）

- **智能去重** — 缓存已推送的论文 ID，同一篇论文不会重复出现

- **多渠道推送** — 静态网站 + HTML 邮件 + 微信（通过 Server酱）

- **AI 后端可替换** — 支持 DeepSeek 官方 API 或任何 OpenAI 兼容的第三方接口

### 在线 Demo

> 👉 [sloan-yang.github.io/TechDigest](https://sloan-yang.github.io/TechDigest/)

### 快速开始

#### 第一步：Fork 本仓库

点击右上角 **Fork**，复制到你自己的 GitHub 账号。

#### 第二步：修改 `config.yaml`

克隆到本地后编辑 `config.yaml`，主要修改以下字段：

```yaml
# 你感兴趣的 arXiv 分类
categories:
  - cs.CV   # 计算机视觉
  - cs.GR   # 图形学
  - cs.MM   # 多媒体

# 关键词过滤（论文标题或摘要至少匹配一个）
keywords:
  - layout generation
  - diffusion
  - image generation

# 每日最多推荐论文数
max_papers_per_day: 5

# arXiv 兴趣画像（DeepSeek 据此打分）
preference:
  profile: >
    我是一名研究 design intelligence 的研究生，重点关注布局生成、
    text-to-image 模型和 diffusion transformer。对医学影像不感兴趣。

# Hacker News
hackernews:
  fetch_top_n: 100
  max_stories_per_day: 8
  preference:
    profile: >
      对 AI/ML 工具、开源项目、UI/设计工具、大模型和开发者工具感兴趣。
      对政治、财经不感兴趣。

# GitHub Trending
github_trending:
  max_repos_per_day: 8
  preference:
    profile: >
      对 AI、创意编程、设计工具、Rust、游戏引擎和开发者工具感兴趣。

# 站点配置
site:
  title: "TechDigest"
  base_url: "https://你的用户名.github.io/你的仓库名/"

# DeepSeek API（使用第三方转发时修改 base_url）
deepseek:
  model: deepseek-chat   # or gpt-4o-mini, claude-3-haiku, etc.
  base_url: "https://api.deepseek.com/v1"   # OpenAI: https://api.openai.com/v1
```

#### 第三步：配置 GitHub Secrets

进入仓库 → **Settings → Secrets and variables → Actions → New repository secret**：

| Secret 名称 | 说明 | 是否必须 |
|---|---|---|
| `LLM_API_KEY` | LLM 接口 API Key（DeepSeek、OpenAI 等均可） | ✅ 必须 |
| `EMAIL_SENDER` | 发件人 Gmail 地址 | 可选 |
| `EMAIL_PASSWORD` | Gmail App 密码（16位，非登录密码）| 可选 |
| `EMAIL_RECIPIENT` | 收件邮箱 | 可选 |
| `SERVERCHAN_KEY` | Server酱 SendKey，用于微信推送 | 可选 |

**获取 Gmail App 密码**：Google 账号 → 安全性 → 两步验证 → 应用专用密码 → 创建

**获取 Server酱 Key**：访问 [sct.ftqq.com](https://sct.ftqq.com)，GitHub 登录，绑定微信后复制 SendKey

#### 第四步：开启 GitHub Pages

仓库 → **Settings → Pages → Source → 选择 "GitHub Actions"** → 保存

#### 第五步：推送并触发运行

```bash
git add .
git commit -m "configure my TechDigest"
git push
```

手动触发第一次运行：**Actions → Daily ArXiv Digest → Run workflow**

之后每天**北京时间早上 6:00** 自动运行。

### 本地运行

```bash
pip install -r requirements.txt

export LLM_API_KEY=sk-...
export EMAIL_SENDER=you@gmail.com
export EMAIL_PASSWORD=your-app-password
export EMAIL_RECIPIENT=you@example.com

python scripts/run_all.py
```

### 项目结构

```
├── config.yaml                  # 所有配置集中在此
├── scripts/
│   ├── fetch_papers.py          # 抓取 arXiv + DeepSeek 打分
│   ├── fetch_hn.py              # 抓取 Hacker News + 打分 + 摘要
│   ├── fetch_github_trending.py # 抓取 GitHub Trending + 打分 + 摘要
│   ├── summarize.py             # 生成论文中文摘要
│   ├── generate_pages.py        # 构建静态 HTML 页面
│   ├── notify_email.py          # 发送 HTML 邮件
│   ├── notify_wechat.py         # 微信推送（Server酱）
│   └── run_all.py               # 本地一键运行
├── data/
│   ├── papers/                  # 每日论文 JSON
│   ├── hn/                      # 每日 HN JSON
│   ├── trending/                # 每日 GitHub Trending JSON
│   ├── scores.json              # arXiv 打分缓存
│   ├── hn_scores.json           # HN 打分缓存
│   └── trending_scores.json     # Trending 打分缓存
└── public/                      # 生成的静态网站
```

### 常见问题

**DeepSeek 报 401 认证错误？**  
检查 `LLM_API_KEY` 是否正确，以及 `config.yaml` 中 `llm.base_url` 是否与你的 API 服务商地址匹配。

**GitHub Pages 显示 Not Found？**  
确认 Settings → Pages → Source 已设为 "GitHub Actions"，且 Actions 中 `deploy` job 执行成功。

**邮件发送失败？**  
Gmail 需要 App 密码而非登录密码，必须先开启两步验证才能生成 App 密码。

**如何换用其他 AI 接口？**  
修改 `config.yaml` 中的 `deepseek.base_url` 为任意 OpenAI 兼容接口地址即可，无需改代码。
