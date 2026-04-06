#!/usr/bin/env python3
"""Send today's ArXiv digest as an HTML email via SMTP."""

import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import yaml


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_today_papers() -> list[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    path = Path(__file__).parent.parent / "data" / "papers" / f"{today}.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_today_hn() -> list[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    path = Path(__file__).parent.parent / "data" / "hn" / f"{today}.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_today_trending() -> list[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    path = Path(__file__).parent.parent / "data" / "trending" / f"{today}.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


CATEGORY_NAMES = {
    "cs.CV": "计算机视觉",
    "cs.CL": "自然语言处理",
    "cs.LG": "机器学习",
    "cs.AI": "人工智能",
    "cs.GR": "图形学",
    "cs.HC": "人机交互",
    "cs.MM": "多媒体",
}


def render_paper(paper: dict) -> str:
    summary = paper.get("summary", {})
    title_zh = summary.get("title_zh", "")
    authors_str = ", ".join(paper["authors"][:5])
    if len(paper["authors"]) > 5:
        authors_str += f" 等 ({len(paper['authors'])} 位作者)"
    cat = CATEGORY_NAMES.get(paper.get("primary_category", ""), paper.get("primary_category", ""))
    score = paper.get("score")
    score_html = (
        f'<span style="border:1px solid #6366f1;border-radius:999px;padding:2px 10px;'
        f'font-size:12px;color:#6366f1;">相关性 {int(score)}/100</span>'
        if isinstance(score, (int, float)) else ""
    )

    sections = ""
    for label, key in [("核心贡献", "core_contribution"), ("方法", "method"), ("关键发现", "findings")]:
        val = summary.get(key, "")
        if val:
            sections += (
                f'<p style="margin:4px 0;font-size:14px;">'
                f'<strong style="color:#6366f1;">{label}:</strong> {val}</p>'
            )

    return f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
            padding:20px;margin-bottom:20px;">
  <div style="display:flex;justify-content:space-between;align-items:center;
              margin-bottom:10px;">
    <span style="background:#6366f1;color:#fff;border-radius:20px;
                 padding:3px 12px;font-size:12px;">{cat}</span>
    {score_html}
  </div>
  <h3 style="margin:0 0 4px;font-size:16px;">
    <a href="{paper['abs_url']}" style="color:#111827;text-decoration:none;">
      {paper['title']}
    </a>
  </h3>
  {f'<p style="margin:0 0 6px;font-size:14px;color:#6b7280;">{title_zh}</p>' if title_zh else ''}
  <p style="margin:0 0 12px;font-size:13px;color:#9ca3af;">{authors_str}</p>
  <div style="background:#f5f3ff;border-radius:8px;padding:12px;">
    {sections}
  </div>
  <div style="margin-top:12px;">
    <a href="{paper['abs_url']}"
       style="display:inline-block;padding:6px 14px;background:#f3f4f6;
              color:#374151;border-radius:6px;font-size:13px;
              text-decoration:none;margin-right:8px;">📄 arXiv</a>
    <a href="{paper['pdf_url']}"
       style="display:inline-block;padding:6px 14px;background:#f3f4f6;
              color:#374151;border-radius:6px;font-size:13px;
              text-decoration:none;">📥 PDF</a>
  </div>
</div>"""


def render_hn_story(story: dict) -> str:
    title = story.get("title", "")
    hn_url = story.get("hn_url", "#")
    url = story.get("url", "")
    by = story.get("by", "")
    hn_score = story.get("score", 0)
    comments = story.get("comments", 0)
    relevance = story.get("relevance_score")
    score_html = (
        f'<span style="border:1px solid #f59e0b;border-radius:999px;padding:2px 8px;'
        f'font-size:11px;color:#f59e0b;">推荐度 {int(relevance)}/100</span>'
        if isinstance(relevance, (int, float)) else ""
    )
    external_link = (
        f'&nbsp;<a href="{url}" style="display:inline-block;padding:5px 12px;'
        f'background:#f3f4f6;color:#374151;border-radius:6px;font-size:12px;'
        f'text-decoration:none;">🔗 原文</a>'
        if url else ""
    )
    return f"""
<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
            padding:16px;margin-bottom:14px;">
  <div style="display:flex;justify-content:space-between;align-items:center;
              margin-bottom:8px;">
    <span style="background:#f59e0b;color:#fff;border-radius:20px;
                 padding:2px 10px;font-size:11px;">HN</span>
    {score_html}
  </div>
  <h3 style="margin:0 0 4px;font-size:15px;">
    <a href="{hn_url}" style="color:#111827;text-decoration:none;">{title}</a>
  </h3>
  <p style="margin:0 0 10px;font-size:12px;color:#9ca3af;">
    by {by} &nbsp;▲ {hn_score} &nbsp;💬 {comments}
  </p>
  {f'<p style="margin:0 0 10px;font-size:13px;color:#374151;background:#fefce8;border-radius:6px;padding:8px 10px;">{story.get("summary")}</p>' if story.get("summary") else ''}
  <a href="{hn_url}" style="display:inline-block;padding:5px 12px;background:#f3f4f6;
     color:#374151;border-radius:6px;font-size:12px;text-decoration:none;">💬 HN 讨论</a>
  {external_link}
</div>"""


def render_trending_repo(repo: dict) -> str:
    full_name = repo.get("full_name", "")
    url = repo.get("url", "#")
    description = repo.get("description", "")
    language = repo.get("language", "")
    stars = repo.get("stars", 0)
    stars_today = repo.get("stars_today", 0)
    relevance = repo.get("relevance_score")
    score_html = (
        f'<span style="border:1px solid #10b981;border-radius:999px;padding:2px 8px;'
        f'font-size:11px;color:#10b981;">推荐度 {int(relevance)}/100</span>'
        if isinstance(relevance, (int, float)) else ""
    )
    lang_html = (
        f'<span style="background:#10b981;color:#fff;border-radius:20px;'
        f'padding:2px 10px;font-size:11px;">{language}</span>'
        if language else ""
    )
    return f"""
<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
            padding:16px;margin-bottom:14px;">
  <div style="display:flex;justify-content:space-between;align-items:center;
              margin-bottom:8px;">
    {lang_html}
    {score_html}
  </div>
  <h3 style="margin:0 0 4px;font-size:15px;">
    <a href="{url}" style="color:#111827;text-decoration:none;">{full_name}</a>
  </h3>
  <p style="margin:0 0 6px;font-size:13px;color:#6b7280;">{description}</p>
  {f'<p style="margin:0 0 10px;font-size:13px;color:#374151;background:#f0fdf4;border-radius:6px;padding:8px 10px;">{repo["summary"]}</p>' if repo.get("summary") else ''}
  <p style="margin:0 0 10px;font-size:12px;color:#9ca3af;">
    ⭐ {stars:,} &nbsp;+{stars_today} today
  </p>
  <a href="{url}" style="display:inline-block;padding:5px 12px;background:#f3f4f6;
     color:#374151;border-radius:6px;font-size:12px;text-decoration:none;">⭐ GitHub</a>
</div>"""


def build_html(papers: list[dict], date_str: str, config: dict, site_url: str,
               hn_stories: list[dict] | None = None,
               trending_repos: list[dict] | None = None) -> str:
    site = config.get("site", {})
    papers_html = "".join(render_paper(p) for p in papers)
    site_link = (
        f'<p style="text-align:center;margin-top:8px;">'
        f'<a href="{site_url}" style="color:#6366f1;">在线查看完整页面 →</a></p>'
        if site_url else ""
    )
    hn_section = ""
    if hn_stories:
        hn_html = "".join(render_hn_story(s) for s in hn_stories)
        hn_section = f"""
  <h2 style="font-size:18px;margin:32px 0 16px;padding-bottom:10px;
             border-bottom:1px solid #e5e7eb;color:#374151;">
    🔥 Hacker News 推荐
  </h2>
  {hn_html}"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
             background:#f9fafb;color:#111827;padding:32px;max-width:700px;margin:0 auto;">
  <div style="text-align:center;margin-bottom:32px;padding-bottom:24px;
              border-bottom:1px solid #e5e7eb;">
    <h1 style="margin:0 0 8px;font-size:28px;">
      {site.get('title', '📚 TechDigest')}
    </h1>
    <p style="color:#6b7280;margin:0 0 6px;">{site.get('description', '每日论文精选')}</p>
    <p style="color:#6366f1;font-size:18px;margin:0;">📅 {date_str}</p>
    <p style="color:#9ca3af;font-size:14px;margin:6px 0 0;">
      {len(papers)} 篇论文
      {f"| {len(hn_stories)} 条 HN 推荐" if hn_stories else ""}
      {f"| {len(trending_repos)} 个 GitHub 项目" if trending_repos else ""}
    </p>
    {site_link}
  </div>
  <h2 style="font-size:18px;margin:0 0 16px;padding-bottom:10px;
             border-bottom:1px solid #e5e7eb;color:#374151;">
    📄 arXiv 论文
  </h2>
  {papers_html}
  {hn_section}
  {('<h2 style="font-size:18px;margin:32px 0 16px;padding-bottom:10px;border-bottom:1px solid #e5e7eb;color:#374151;">🐙 GitHub Trending</h2>' + "".join(render_trending_repo(r) for r in trending_repos)) if trending_repos else ""}
  <div style="text-align:center;padding-top:24px;border-top:1px solid #e5e7eb;
              color:#9ca3af;font-size:13px;">
    <p>由 TechDigest 自动生成 | 数据来源:
      <a href="https://arxiv.org" style="color:#6366f1;">arXiv.org</a>
    </p>
  </div>
</body>
</html>"""


def resolve_site_url(config: dict) -> str:
    base = config.get("site", {}).get("base_url", "")
    if base:
        return base.rstrip("/") + "/"
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return f"https://{owner}.github.io/{name}/"
    return ""


def send_email(sender: str, password: str, recipient: str,
               subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(sender, password)
        smtp.sendmail(sender, recipient, msg.as_string())


def main() -> None:
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    recipient = os.environ.get("EMAIL_RECIPIENT")

    if not all([sender, password, recipient]):
        missing = [k for k, v in {
            "EMAIL_SENDER": sender,
            "EMAIL_PASSWORD": password,
            "EMAIL_RECIPIENT": recipient,
        }.items() if not v]
        print(f"[notify_email] skipped — missing env vars: {', '.join(missing)}")
        return

    config = load_config()
    papers = load_today_papers()
    hn_stories = load_today_hn()
    trending_repos = load_today_trending()
    today = datetime.now().strftime("%Y-%m-%d")
    site_url = resolve_site_url(config)

    parts = []
    if papers:
        parts.append(f"{len(papers)} 篇新论文")
    if hn_stories:
        parts.append(f"{len(hn_stories)} 条 HN 推荐")
    if trending_repos:
        parts.append(f"{len(trending_repos)} 个 GitHub 项目")
    subject = (
        f"Daily Digest {today} — {' | '.join(parts)}"
        if parts else f"Daily Digest {today} — 今日暂无内容"
    )

    html_body = build_html(papers, today, config, site_url, hn_stories, trending_repos)

    try:
        send_email(sender, password, recipient, subject, html_body)
        print(f"[notify_email] sent to {recipient} ({len(papers)} papers, {len(hn_stories)} HN)")
    except Exception as e:
        print(f"[notify_email] failed: {e}")
        raise


if __name__ == "__main__":
    main()
