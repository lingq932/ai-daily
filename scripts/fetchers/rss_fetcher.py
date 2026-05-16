import feedparser
import requests
from datetime import datetime, timezone, timedelta
import re

HEADERS = {
    "User-Agent": "AI-Daily-Bot/1.0 (RSS Reader; +https://github.com)"
}


def fetch_rss_section(section_id, section_config, time_from=None, time_to=None, max_per_feed=15):
    items = []
    for feed_cfg in section_config["feeds"]:
        try:
            fetched = fetch_single_feed(feed_cfg, time_from, time_to, max_per_feed)
            items.extend(fetched)
            print(f"  [OK] {feed_cfg['source']}: {len(fetched)} items")
        except Exception as e:
            print(f"  [FAIL] {feed_cfg['source']}: {e}")
    return {
        "id": section_id,
        "name": section_config["name"],
        "items": items,
    }


def fetch_single_feed(feed_cfg, time_from=None, time_to=None, max_items=15):
    try:
        resp = requests.get(feed_cfg["url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
    except requests.RequestException:
        feed = feedparser.parse(feed_cfg["url"])

    items = []
    # 扫描更多条目以找到历史数据
    scan_limit = 200 if time_from else max_items

    for entry in feed.entries[:scan_limit]:
        title = clean_html(entry.get("title", ""))
        summary = clean_html(entry.get("summary", entry.get("description", "")))
        if len(summary) > 500:
            summary = summary[:500] + "..."

        link = entry.get("link", "")
        pub_dt = parse_entry_datetime(entry)
        source = feed_cfg.get("label", feed_cfg["source"])

        # 日期过滤
        if time_from and time_to and pub_dt:
            if not (time_from <= pub_dt < time_to):
                continue
        elif time_from and time_to and not pub_dt:
            # 无法判断日期，跳过
            continue

        time_str = pub_dt.astimezone(timezone(timedelta(hours=8))).strftime("%H:%M") if pub_dt else ""

        items.append({
            "source": source,
            "title": title,
            "summary": summary,
            "url": link,
            "time": time_str,
            "eventId": None,
            "relatedDate": None,
        })

        if len(items) >= max_items:
            break

    return items


def clean_html(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_entry_datetime(entry):
    for field in ["published_parsed", "updated_parsed"]:
        t = entry.get(field)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def parse_feed_time(entry):
    dt = parse_entry_datetime(entry)
    if dt:
        cst = dt + timedelta(hours=8)
        return cst.strftime("%H:%M")
    return ""
