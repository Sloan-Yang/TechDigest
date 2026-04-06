#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime
import yaml
import shutil


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CATEGORY_NAMES = {
    "cs.CV": "计算机视觉",
    "cs.CL": "自然语言处理",
    "cs.LG": "机器学习",
    "cs.AI": "人工智能",
    "cs.GR": "图形学",
    "cs.HC": "人机交互",
    "cs.MM": "多媒体",
    "cs.RO": "机器人",
    "cs.NE": "神经与进化计算",
    "stat.ML": "统计机器学习"
}


def generate_paper_html(paper: dict) -> str:
    summary = paper.get("summary", {})
    title_zh = summary.get("title_zh", "")

    authors_str = ", ".join(paper["authors"][:5])
    if len(paper["authors"]) > 5:
        authors_str += f" 等 ({len(paper['authors'])} 位作者)"

    cat_name = CATEGORY_NAMES.get(paper.get("primary_category", ""), paper.get("primary_category", ""))
    score = paper.get("score")

    score_html = f'<span class="score-badge">相关性 {int(score)}/100</span>' if isinstance(score, (int, float)) else ""

    return f'''
    <article class="paper-card">
      <div class="paper-header">
        <div class="left-header">
          <span class="category-badge">{cat_name}</span>
          <span class="paper-id">{paper["id"]}</span>
        </div>
        {score_html}
      </div>
      <h3 class="paper-title">
        <a href="{paper["abs_url"]}" target="_blank">{paper["title"]}</a>
      </h3>
      {f'<p class="paper-title-zh">{title_zh}</p>' if title_zh else ''}
      <p class="paper-authors">{authors_str}</p>
      
      <div class="paper-summary">
        {f'<div class="summary-section"><strong>核心贡献:</strong> {summary.get("core_contribution", "")}</div>' if summary.get("core_contribution") else ''}
        {f'<div class="summary-section"><strong>方法:</strong> {summary.get("method", "")}</div>' if summary.get("method") else ''}
        {f'<div class="summary-section"><strong>关键发现:</strong> {summary.get("findings", "")}</div>' if summary.get("findings") else ''}
      </div>
      
      <details class="paper-abstract">
        <summary>查看原文摘要</summary>
        <p>{paper["abstract"]}</p>
      </details>
      
      <div class="paper-links">
        <a href="{paper["abs_url"]}" target="_blank" class="link-btn">📄 arXiv</a>
        <a href="{paper["pdf_url"]}" target="_blank" class="link-btn">📥 PDF</a>
      </div>
    </article>
    '''


def generate_hn_story_html(story: dict) -> str:
    score = story.get("relevance_score")
    score_html = (
        f'<span class="score-badge">推荐度 {int(score)}/100</span>'
        if isinstance(score, (int, float)) else ""
    )
    title = story.get("title", "")
    hn_url = story.get("hn_url", "#")
    url = story.get("url", "")
    by = story.get("by", "")
    hn_score = story.get("score", 0)
    comments = story.get("comments", 0)

    external_link = (
        f'<a href="{url}" target="_blank" class="link-btn">🔗 原文</a>'
        if url else ""
    )

    return f'''
    <article class="paper-card hn-card" style="border-left: 3px solid var(--hn-color);">
      <div class="paper-header">
        <div class="left-header">
          <span class="category-badge hn-badge">HN</span>
          <span class="paper-id">▲ {hn_score} &nbsp;💬 {comments}</span>
        </div>
        {score_html}
      </div>
      <h3 class="paper-title">
        <a href="{hn_url}" target="_blank">{title}</a>
      </h3>
      <p class="paper-authors">by {by}</p>
      {f'<div class="paper-summary"><div class="summary-section">{story.get("summary")}</div></div>' if story.get("summary") else ''}
      <div class="paper-links">
        <a href="{hn_url}" target="_blank" class="link-btn">💬 HN 讨论</a>
        {external_link}
      </div>
    </article>
    '''


def generate_trending_repo_html(repo: dict) -> str:
    score = repo.get("relevance_score")
    score_html = (
        f'<span class="score-badge">推荐度 {int(score)}/100</span>'
        if isinstance(score, (int, float)) else ""
    )
    lang = repo.get("language", "")
    lang_html = f'<span class="category-badge gh-badge">{lang}</span>' if lang else ""
    stars_today = repo.get("stars_today", 0)
    stars = repo.get("stars", 0)

    return f'''
    <article class="paper-card gh-card" style="border-left: 3px solid var(--gh-color);">
      <div class="paper-header">
        <div class="left-header">
          {lang_html}
          <span class="paper-id">⭐ {stars:,} &nbsp;+{stars_today} today</span>
        </div>
        {score_html}
      </div>
      <h3 class="paper-title">
        <a href="{repo['url']}" target="_blank">{repo['full_name']}</a>
      </h3>
      {f'<p class="paper-authors">{repo["description"]}</p>' if repo.get("description") else ''}
      {f'<div class="paper-summary"><div class="summary-section">{repo["summary"]}</div></div>' if repo.get("summary") else ''}
      <div class="paper-links">
        <a href="{repo['url']}" target="_blank" class="link-btn">⭐ GitHub</a>
      </div>
    </article>
    '''


def generate_index_html(papers: list[dict], date_str: str, config: dict,
                        hn_stories: list[dict] | None = None,
                        trending_repos: list[dict] | None = None) -> str:
    site_config = config.get("site", {})
    
    papers_html = "\n".join([generate_paper_html(p) for p in papers])
    
    cat_counts = {}
    for p in papers:
        cat = p.get("primary_category", "other")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    
    stats_html = " | ".join([f"{CATEGORY_NAMES.get(k, k)}: {v}" for k, v in sorted(cat_counts.items())])
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_config.get("title", "TechDigest")}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Noto+Sans+SC:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #fdf9ed;
            --card-bg: #ffffff;
            --card-border: #e8ecf0;
            --card-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
            --text: #1e2128;
            --text-muted: #6b7385;
            --accent: #4f6ef7;
            --accent-light: #eef1fe;
            --hn-color: #e8600a;
            --hn-light: #fff4ed;
            --gh-color: #1a7f37;
            --gh-light: #edfbf0;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: 'Lato', 'Noto Sans SC', -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
            min-height: 100vh;
        }}

        .site-header {{
            background: #fff;
            border-bottom: 1px solid var(--card-border);
            padding: 1.2rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        .site-name {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text);
            text-decoration: none;
            letter-spacing: -0.3px;
        }}

        .site-name span {{
            color: var(--accent);
        }}

        .header-nav a {{
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.9rem;
            margin-left: 1.5rem;
            transition: color 0.2s;
        }}

        .header-nav a:hover {{ color: var(--accent); }}

        .page-hero {{
            background: #fff;
            border-bottom: 1px solid var(--card-border);
            padding: 2.5rem 2rem;
            text-align: center;
        }}

        .page-date {{
            display: inline-block;
            background: var(--accent-light);
            color: var(--accent);
            font-size: 0.85rem;
            font-weight: 700;
            padding: 0.25rem 0.9rem;
            border-radius: 20px;
            margin-bottom: 0.75rem;
            letter-spacing: 0.5px;
        }}

        .page-hero h2 {{
            font-size: 1.6rem;
            font-weight: 300;
            color: var(--text-muted);
            margin-bottom: 0.4rem;
        }}

        .page-stats {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
        }}

        .page-stats a {{
            color: var(--accent);
            text-decoration: none;
            margin-left: 1rem;
        }}

        .content {{
            max-width: 780px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }}

        .section-heading {{
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin: 2.5rem 0 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .section-heading::after {{
            content: '';
            flex: 1;
            height: 1px;
            background: var(--card-border);
        }}

        .paper-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 1.4rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: var(--card-shadow);
            transition: box-shadow 0.2s, border-color 0.2s;
        }}

        .paper-card:hover {{
            box-shadow: 0 4px 20px rgba(79,110,247,0.1);
            border-color: #c5cef7;
        }}

        .paper-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.7rem;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}

        .left-header {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            flex-wrap: wrap;
        }}

        .category-badge {{
            background: var(--accent-light);
            color: var(--accent);
            padding: 0.2rem 0.65rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
        }}

        .hn-badge {{
            background: var(--hn-light) !important;
            color: var(--hn-color) !important;
        }}

        .gh-badge {{
            background: var(--gh-light) !important;
            color: var(--gh-color) !important;
        }}

        .paper-id {{
            color: var(--text-muted);
            font-size: 0.78rem;
            font-family: monospace;
        }}

        .score-badge {{
            font-size: 0.75rem;
            color: var(--text-muted);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 0.15rem 0.6rem;
        }}

        .paper-title {{
            font-size: 1.05rem;
            font-weight: 700;
            line-height: 1.45;
            margin-bottom: 0.3rem;
        }}

        .paper-title a {{
            color: var(--text);
            text-decoration: none;
        }}

        .paper-title a:hover {{ color: var(--accent); }}

        .paper-title-zh {{
            font-size: 0.92rem;
            color: var(--text-muted);
            margin-bottom: 0.4rem;
            font-weight: 300;
        }}

        .paper-authors {{
            font-size: 0.83rem;
            color: var(--text-muted);
            margin-bottom: 0.9rem;
        }}

        .paper-summary {{
            background: var(--accent-light);
            border-left: 3px solid var(--accent);
            border-radius: 0 6px 6px 0;
            padding: 0.75rem 1rem;
            margin-bottom: 0.9rem;
            font-size: 0.88rem;
        }}

        .hn-card .paper-summary {{
            background: var(--hn-light);
            border-left-color: var(--hn-color);
        }}

        .gh-card .paper-summary {{
            background: var(--gh-light);
            border-left-color: var(--gh-color);
        }}

        .summary-section {{ margin-bottom: 0.35rem; }}
        .summary-section:last-child {{ margin-bottom: 0; }}
        .summary-section strong {{ color: var(--accent); }}

        .paper-abstract {{
            margin-bottom: 0.9rem;
            font-size: 0.85rem;
        }}

        .paper-abstract summary {{
            cursor: pointer;
            color: var(--text-muted);
            user-select: none;
        }}

        .paper-abstract p {{
            margin-top: 0.6rem;
            color: var(--text-muted);
            line-height: 1.6;
        }}

        .paper-links {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}

        .link-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.2rem;
            padding: 0.35rem 0.85rem;
            background: var(--bg);
            color: var(--text-muted);
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.8rem;
            border: 1px solid var(--card-border);
            transition: all 0.15s;
        }}

        .link-btn:hover {{
            background: var(--accent);
            color: #fff;
            border-color: var(--accent);
        }}

        footer {{
            text-align: center;
            padding: 2.5rem 1rem;
            color: var(--text-muted);
            font-size: 0.83rem;
            border-top: 1px solid var(--card-border);
            margin-top: 2rem;
        }}

        footer a {{ color: var(--accent); text-decoration: none; }}

        @media (max-width: 600px) {{
            .site-header {{ padding: 1rem; }}
            .content {{ padding: 1rem; }}
            .paper-card {{ padding: 1rem; }}
        }}
    </style>
</head>
<body>
    <header class="site-header">
        <a class="site-name" href="index.html">Tech<span>Digest</span></a>
        <nav class="header-nav">
            <a href="archive.html">归档</a>
        </nav>
    </header>

    <div class="page-hero">
        <div class="page-date">📅 {date_str}</div>
        <h2>{site_config.get("description", "每日精选")}</h2>
        <p class="page-stats">
            {stats_html}
            <a href="archive.html">归档 →</a>
        </p>
    </div>

    <div class="content">
        <div class="section-heading">📄 arXiv 论文</div>
        {papers_html}
        {('<div class="section-heading">🔥 Hacker News</div>' + "".join(generate_hn_story_html(s) for s in hn_stories)) if hn_stories else ''}
        {('<div class="section-heading">🐙 GitHub Trending</div>' + "".join(generate_trending_repo_html(r) for r in trending_repos)) if trending_repos else ''}
    </div>

    <footer>
        <p>由 <a href="https://github.com/Sloan-Yang/TechDigest">TechDigest</a> 自动生成</p>
        <p>数据来源: <a href="https://arxiv.org">arXiv.org</a> · <a href="https://news.ycombinator.com">Hacker News</a> · <a href="https://github.com/trending">GitHub Trending</a></p>
    </footer>
</body>
</html>'''


def generate_archive_html(all_dates: list[str], config: dict) -> str:
    site_config = config.get("site", {})
    
    dates_html = "\n".join([
        f'<a href="{d}.html" class="archive-link">{d}</a>'
        for d in sorted(all_dates, reverse=True)
    ])
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>归档 · {site_config.get("title", "TechDigest")}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Lato', -apple-system, sans-serif;
            background: #fdf9ed;
            color: #1e2128;
            min-height: 100vh;
        }}
        .site-header {{
            background: #fff;
            border-bottom: 1px solid #e8ecf0;
            padding: 1.2rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .site-name {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #1e2128;
            text-decoration: none;
        }}
        .site-name span {{ color: #4f6ef7; }}
        .content {{
            max-width: 600px;
            margin: 0 auto;
            padding: 2.5rem 1.5rem;
        }}
        h1 {{
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: #1e2128;
        }}
        .archive-link {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.9rem 1.1rem;
            background: #fff;
            border: 1px solid #e8ecf0;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            color: #1e2128;
            text-decoration: none;
            font-size: 0.95rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            transition: border-color 0.15s, box-shadow 0.15s;
        }}
        .archive-link:hover {{
            border-color: #4f6ef7;
            box-shadow: 0 2px 8px rgba(79,110,247,0.1);
        }}
        .archive-link::after {{
            content: '→';
            color: #a0aab8;
            font-size: 0.85rem;
        }}
        .back {{ margin-bottom: 1.5rem; }}
        .back a {{ color: #4f6ef7; text-decoration: none; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <header class="site-header">
        <a class="site-name" href="index.html">Tech<span>Digest</span></a>
    </header>
    <div class="content">
        <p class="back"><a href="index.html">← 返回今日</a></p>
        <h1>历史归档</h1>
        {dates_html}
    </div>
</body>
</html>'''


def load_hn_stories(date_str: str, project_root: Path) -> list[dict]:
    path = project_root / "data" / "hn" / f"{date_str}.json"
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def load_trending_repos(date_str: str, project_root: Path) -> list[dict]:
    path = project_root / "data" / "trending" / f"{date_str}.json"
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def main():
    config = load_config()
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "papers"
    output_dir = project_root / "public"

    output_dir.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    today_file = data_dir / f"{today}.json"

    if today_file.exists():
        with open(today_file, "r", encoding="utf-8") as f:
            papers = json.load(f)

        hn_stories = load_hn_stories(today, project_root)
        trending_repos = load_trending_repos(today, project_root)
        index_html = generate_index_html(papers, today, config, hn_stories, trending_repos)
        (output_dir / "index.html").write_text(index_html, encoding="utf-8")
        (output_dir / f"{today}.html").write_text(index_html, encoding="utf-8")
        print(f"Generated index.html with {len(papers)} papers, {len(hn_stories)} HN, {len(trending_repos)} trending")

    all_dates = [f.stem for f in data_dir.glob("*.json")]
    archive_html = generate_archive_html(all_dates, config)
    (output_dir / "archive.html").write_text(archive_html, encoding="utf-8")
    print(f"Generated archive.html with {len(all_dates)} dates")


if __name__ == "__main__":
    main()
