#!/usr/bin/env python3
"""Scrape GitHub Trending, score with DeepSeek, generate Chinese summaries."""

import json
import os
import re
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

try:
    from openai import OpenAI
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "openai"])
    from openai import OpenAI


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_trending_html(language: str = "") -> str:
    url = "https://github.com/trending"
    if language:
        url += f"/{urllib.parse.quote(language)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


import urllib.parse


def parse_trending(html: str) -> list[dict]:
    repos = []
    articles = re.findall(r"<article[^>]*>(.*?)</article>", html, re.DOTALL)

    for article in articles:
        # repo path: first /owner/repo href
        href_match = re.search(
            r'href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', article
        )
        if not href_match:
            continue
        repo_path = href_match.group(1)
        if "/" not in repo_path:
            continue
        owner, name = repo_path.split("/", 1)

        # description: first <p> text
        desc = ""
        desc_match = re.search(r"<p[^>]*>(.*?)</p>", article, re.DOTALL)
        if desc_match:
            desc = re.sub(r"<[^>]+>", "", desc_match.group(1)).strip()

        # language
        language = ""
        lang_match = re.search(
            r'itemprop="programmingLanguage"[^>]*>\s*([^<]+)\s*<', article
        )
        if lang_match:
            language = lang_match.group(1).strip()

        # stars today
        stars_today = 0
        today_match = re.search(r"([\d,]+)\s+stars?\s+today", article)
        if today_match:
            stars_today = int(today_match.group(1).replace(",", ""))

        # total stars
        total_stars = 0
        stars_match = re.search(
            r'/stargazers.*?>\s*([\d,]+)\s*<', article, re.DOTALL
        )
        if stars_match:
            total_stars = int(stars_match.group(1).replace(",", ""))

        repos.append({
            "id": repo_path.replace("/", "_"),
            "full_name": repo_path,
            "owner": owner,
            "name": name,
            "url": f"https://github.com/{repo_path}",
            "description": desc,
            "language": language,
            "stars": total_stars,
            "stars_today": stars_today,
        })

    return repos


RANK_PROMPT = """你是一个内容推荐助手，帮助用户从 GitHub Trending 中发现感兴趣的项目。

请基于以下用户兴趣画像，判断这个 GitHub 项目是否值得推荐：

{profile}

打分标准（0-100 分）：
- 80-100：与用户兴趣高度相关，强烈推荐
- 40-79：有一定相关性，可以关注
- 0-39：与用户兴趣无关，不推荐

项目名称: {full_name}
编程语言: {language}
今日 Star: {stars_today}
项目描述: {description}

请只输出一个 JSON 对象，不要输出任何解释：
{{"score": 0-100}}"""


SUMMARY_PROMPT = """请用1-2句中文简要介绍以下 GitHub 项目是做什么的，以及为什么值得关注。

项目: {full_name}
语言: {language}
描述: {description}

只输出中文介绍，不要任何额外说明。"""


def score_repo(client: OpenAI, repo: dict, config: dict) -> int | None:
    profile = config.get("github_trending", {}).get("preference", {}).get("profile", "")
    prompt = RANK_PROMPT.format(
        profile=profile,
        full_name=repo["full_name"],
        language=repo.get("language", "未知"),
        stars_today=repo.get("stars_today", 0),
        description=repo.get("description", ""),
    )
    ds_cfg = config.get("llm", config.get("deepseek", {}))
    try:
        resp = client.chat.completions.create(
            model=ds_cfg.get("model", "deepseek-chat"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=64,
            temperature=0.0,
        )
        content = resp.choices[0].message.content.strip()
        start, end = content.find("{"), content.rfind("}")
        if start != -1 and end != -1:
            data = json.loads(content[start: end + 1])
            return max(0, min(100, int(data.get("score", 0))))
    except Exception as e:
        print(f"[trending] scoring failed for {repo['full_name']}: {e}")
    return None


def summarize_repo(client: OpenAI, repo: dict, config: dict) -> str | None:
    prompt = SUMMARY_PROMPT.format(
        full_name=repo["full_name"],
        language=repo.get("language", ""),
        description=repo.get("description", ""),
    )
    ds_cfg = config.get("llm", config.get("deepseek", {}))
    try:
        resp = client.chat.completions.create(
            model=ds_cfg.get("model", "deepseek-chat"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[trending] summarize failed for {repo['full_name']}: {e}")
    return None


def load_trending_scores() -> dict[str, int]:
    path = Path(__file__).parent.parent / "data" / "trending_scores.json"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {str(k): int(v) for k, v in json.load(f).items()}
    except Exception:
        return {}


def save_trending_scores(scores: dict[str, int]) -> None:
    path = Path(__file__).parent.parent / "data" / "trending_scores.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)


def save_trending(repos: list[dict], date_str: str) -> None:
    path = Path(__file__).parent.parent / "data" / "trending" / f"{date_str}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    print(f"[trending] saved {len(repos)} repos to {path}")


def main():
    config = load_config()
    gt_cfg = config.get("github_trending", {})
    max_per_day = gt_cfg.get("max_repos_per_day", 8)

    print("[trending] fetching GitHub Trending...")
    html = fetch_trending_html()
    repos = parse_trending(html)
    print(f"[trending] parsed {len(repos)} repos")

    if not repos:
        print("[trending] no repos found, check HTML parsing")
        return

    scores = load_trending_scores()
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    client = None
    if api_key:
        client = OpenAI(
            api_key=api_key,
            base_url=config.get("llm", config.get("deepseek", {})).get("base_url", "https://api.deepseek.com"),
        )

    if client:
        new_scored = 0
        for repo in repos:
            rid = repo["id"]
            if rid in scores:
                continue
            s = score_repo(client, repo, config)
            if s is not None:
                scores[rid] = s
                new_scored += 1
            time.sleep(0.2)
        if new_scored:
            print(f"[trending] scored {new_scored} repos")
            save_trending_scores(scores)
        else:
            print("[trending] no new repos to score")
    else:
        print("[trending] LLM_API_KEY not set, ranking by stars_today only")

    for repo in repos:
        repo["relevance_score"] = scores.get(repo["id"], 0)

    ranked = sorted(repos, key=lambda x: x.get("relevance_score", 0), reverse=True)
    selected = ranked[:max_per_day]

    # summarize selected repos
    if client:
        for repo in selected:
            if repo.get("summary"):
                continue
            summary = summarize_repo(client, repo, config)
            if summary:
                repo["summary"] = summary
            time.sleep(0.2)

    today = datetime.now().strftime("%Y-%m-%d")
    save_trending(selected, today)


if __name__ == "__main__":
    main()
