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


def _fetch_handle_tweets(handle, hours_back=24):
    """抓取单个账号的推文列表，返回原始文本列表"""
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

            tweets = []
            for entry in feed.entries:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if published and published < cutoff:
                    continue
                content = entry.get("summary", "") or entry.get("title", "")
                if content:
                    tweets.append(content)

            print(f"  @{handle}: {len(tweets)} 条（via {instance}）")
            return tweets

        except Exception:
            continue

    print(f"  @{handle}: 所有 Nitter 实例均不可用")
    return []


def fetch_twitter_section(accounts):
    print(f"  爬取 {len(accounts)} 个账号...")
    items = []

    for handle in accounts:
        tweets = _fetch_handle_tweets(handle)
        if not tweets:
            continue

        # 多条推文合并为一个条目
        if len(tweets) == 1:
            summary = tweets[0]
        else:
            summary = "\n\n".join(f"· {t}" for t in tweets)

        items.append({
            "title": f"@{handle}",
            "url": f"https://twitter.com/{handle}",
            "summary": summary,
            "source": f"Twitter @{handle}",
        })

    print(f"  合计 {len(items)} 个账号有更新")
    return {
        "id": "twitter",
        "name": "Twitter/X 动态",
        "items": items,
    }
