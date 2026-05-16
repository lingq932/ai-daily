import feedparser
import requests
from datetime import datetime, timedelta, timezone

NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
    "https://nitter.net",
    "https://nitter.cz",
    "https://nitter.woodland.cafe",
]


def _fetch_handle_rss(handle, hours_back=24):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"}

    for instance in NITTER_INSTANCES:
        url = f"{instance}/{handle}/rss"
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            feed = feedparser.parse(resp.text)
            if not feed.entries:
                continue

            items = []
            for entry in feed.entries:
                # 解析发布时间
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if published and published < cutoff:
                    continue

                content = entry.get("summary", "") or entry.get("title", "")
                if not content:
                    continue

                items.append({
                    "title": f"@{handle}",
                    "url": entry.get("link", f"https://twitter.com/{handle}"),
                    "content": content,
                    "source": f"Twitter @{handle}",
                    "published": published.isoformat() if published else "",
                })

            print(f"  @{handle}: {len(items)} 条（via {instance}）")
            return items

        except Exception as e:
            continue

    print(f"  @{handle}: 所有 Nitter 实例均不可用")
    return []


def fetch_twitter_section(accounts):
    print(f"  爬取账号: {', '.join('@' + a for a in accounts)}")
    items = []
    for handle in accounts:
        items.extend(_fetch_handle_rss(handle))

    print(f"  合计 {len(items)} 条")
    return {
        "id": "twitter",
        "name": "Twitter/X 动态",
        "items": items,
    }
