import feedparser
import requests
from datetime import datetime, timezone, timedelta
import time
import re

HEADERS = {
    "User-Agent": "AI-Daily-Bot/1.0 (RSS Reader; +https://github.com)"
}

def fetch_rss_section(section_id, section_config, max_per_feed=5):
    items = []
    for feed_cfg in section_config["feeds"]:
        try:
            fetched = fetch_single_feed(feed_cfg, max_per_feed)
            items.extend(fetched)
            print(f"  [OK] {feed_cfg['source']}: {len(fetched)} items")
        except Exception as e:
            print(f"  [FAIL] {feed_cfg['source']}: {e}")
    return {
        "id": section_id,
        "name": section_config["name"],
        "items": items,
    }


def fetch_single_feed(feed_cfg, max_items=5):
    try:
        resp = requests.get(feed_cfg["url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
    except requests.RequestException:
        feed = feedparser.parse(feed_cfg["url"])

    items = []
    for entry in feed.entries[:max_items]:
        title = clean_html(entry.get("title", ""))
        summary = clean_html(entry.get("summary", entry.get("description", "")))
        if len(summary) > 500:
            summary = summary[:500] + "..."

        link = entry.get("link", "")
        published = parse_feed_time(entry)
        source = feed_cfg.get("label", feed_cfg["source"])

        items.append({
            "source": source,
            "title": title,
            "summary": summary,
            "url": link,
            "time": published,
            "eventId": None,
            "relatedDate": None,
        })

    return items


def clean_html(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_feed_time(entry):
    for field in ["published_parsed", "updated_parsed"]:
        t = entry.get(field)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc)
                cst = dt + timedelta(hours=8)
                return cst.strftime("%H:%M")
            except Exception:
                pass
    return ""
