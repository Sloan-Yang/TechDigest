#!/usr/bin/env python3
"""Fetch top Hacker News stories, score with DeepSeek, save daily digest."""

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


HN_API = "https://hacker-news.firebaseio.com/v0"


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_json(url: str):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "arxiv-daily-digest/0.1 (HN reader)"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_top_story_ids(limit: int = 100) -> list[int]:
    ids = fetch_json(f"{HN_API}/topstories.json")
    return ids[:limit]


def fetch_story(story_id: int) -> dict | None:
    try:
        item = fetch_json(f"{HN_API}/item/{story_id}.json")
        if not item or item.get("type") != "story":
            return None
        if item.get("dead") or item.get("deleted"):
            return None
        return {
            "id": item["id"],
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "text": item.get("text", ""),   # populated for Ask HN / Show HN
            "score": item.get("score", 0),
            "comments": item.get("descendants", 0),
            "by": item.get("by", ""),
            "time": item.get("time", 0),
            "hn_url": f"https://news.ycombinator.com/item?id={item['id']}",
        }
    except Exception as e:
        print(f"[hn] failed to fetch story {story_id}: {e}")
        return None


RANK_PROMPT = """你是一个内容推荐助手，帮助用户从 Hacker News 中筛选感兴趣的内容。

请基于以下用户兴趣画像，判断这条 HN 帖子是否值得推荐：

{profile}

打分标准（0-100 分）：
- 80-100：与用户兴趣高度相关，强烈推荐
- 40-79：有一定相关性，可以关注
- 0-39：与用户兴趣无关，不推荐

帖子标题: {title}
链接: {url}
HN 热度: {score} 点，{comments} 条评论
{text_section}

请只输出一个 JSON 对象，不要输出任何解释：
{{"score": 0-100}}"""


def score_story(client: OpenAI, story: dict, config: dict) -> int | None:
    hn_cfg = config.get("hackernews", {})
    profile = hn_cfg.get("preference", {}).get("profile", "")

    text_section = ""
    if story.get("text"):
        plain = re.sub(r"<[^>]+>", " ", story["text"])
        plain = re.sub(r"\s+", " ", plain).strip()[:600]
        text_section = f"内容摘要: {plain}"

    prompt = RANK_PROMPT.format(
        profile=profile,
        title=story["title"],
        url=story.get("url", ""),
        score=story.get("score", 0),
        comments=story.get("comments", 0),
        text_section=text_section,
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
            data = json.loads(content[start : end + 1])
            return max(0, min(100, int(data.get("score", 0))))
    except Exception as e:
        print(f"[hn] scoring failed for {story['id']}: {e}")
    return None


SUMMARY_PROMPT = """请用1-2句中文简要说明以下 Hacker News 帖子的内容和看点。

标题: {title}
链接: {url}
{text_section}

只输出中文简介，不要任何额外说明。"""


def summarize_story(client: OpenAI, story: dict, config: dict) -> str | None:
    text_section = ""
    if story.get("text"):
        plain = re.sub(r"<[^>]+>", " ", story["text"])
        plain = re.sub(r"\s+", " ", plain).strip()[:600]
        text_section = f"内容: {plain}"

    prompt = SUMMARY_PROMPT.format(
        title=story["title"],
        url=story.get("url", ""),
        text_section=text_section,
    )

    ds_cfg = config.get("llm", config.get("deepseek", {}))
    try:
        resp = client.chat.completions.create(
            model=ds_cfg.get("model", "deepseek-chat"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[hn] summarize failed for {story['id']}: {e}")
        return None


def load_hn_scores() -> dict[str, int]:
    path = Path(__file__).parent.parent / "data" / "hn_scores.json"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {str(k): int(v) for k, v in json.load(f).items()}
    except Exception:
        return {}


def save_hn_scores(scores: dict[str, int]) -> None:
    path = Path(__file__).parent.parent / "data" / "hn_scores.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)


def save_hn_stories(stories: list[dict], date_str: str) -> None:
    path = Path(__file__).parent.parent / "data" / "hn" / f"{date_str}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)
    print(f"[hn] saved {len(stories)} stories to {path}")


def main():
    config = load_config()
    hn_cfg = config.get("hackernews", {})
    fetch_n = hn_cfg.get("fetch_top_n", 100)
    max_per_day = hn_cfg.get("max_stories_per_day", 8)

    print(f"[hn] fetching top {fetch_n} story IDs...")
    story_ids = fetch_top_story_ids(fetch_n)

    print("[hn] fetching story details...")
    stories = []
    for sid in story_ids:
        s = fetch_story(sid)
        if s:
            stories.append(s)
        time.sleep(0.05)
    print(f"[hn] got {len(stories)} valid stories")

    scores = load_hn_scores()
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    client = None
    if api_key:
        client = OpenAI(api_key=api_key, base_url=config.get("llm", config.get("deepseek", {})).get("base_url", "https://api.deepseek.com"))

    if client:
        new_scored = 0
        for story in stories:
            sid = str(story["id"])
            if sid in scores:
                continue
            s = score_story(client, story, config)
            if s is not None:
                scores[sid] = s
                new_scored += 1
            time.sleep(0.2)
        if new_scored:
            print(f"[hn] scored {new_scored} new stories")
            save_hn_scores(scores)
        else:
            print("[hn] no new stories to score")
    else:
        print("[hn] LLM_API_KEY not set, ranking by HN score only")

    # attach relevance scores and sort
    for story in stories:
        sid = str(story["id"])
        story["relevance_score"] = scores.get(sid, 0)

    ranked = sorted(stories, key=lambda x: x.get("relevance_score", 0), reverse=True)
    selected = ranked[:max_per_day]

    # summarize selected stories
    if client:
        for story in selected:
            if story.get("summary"):
                continue
            summary = summarize_story(client, story, config)
            if summary:
                story["summary"] = summary
            time.sleep(0.2)

    today = datetime.now().strftime("%Y-%m-%d")
    save_hn_stories(selected, today)


if __name__ == "__main__":
    main()
