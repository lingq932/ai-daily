import asyncio
import os
from datetime import datetime, timedelta, timezone


async def _fetch(accounts, hours_back=24):
    try:
        from twscrape import API
    except ImportError:
        print("  [SKIP] twscrape 未安装")
        return []

    auth_token = os.environ.get("TWITTER_AUTH_TOKEN", "")
    ct0 = os.environ.get("TWITTER_CT0", "")

    if not auth_token or not ct0:
        print("  [SKIP] 未配置 TWITTER_AUTH_TOKEN / TWITTER_CT0")
        return []

    cookies = f"auth_token={auth_token}; ct0={ct0}"

    api = API()
    try:
        await api.pool.add_account(
            username="cookie_user",
            password="cookie_pass",
            email="cookie@placeholder.com",
            email_password="cookie_pass",
            cookies=cookies,
        )
    except Exception as e:
        print(f"  [WARN] 添加账号失败: {e}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    items = []

    for handle in accounts:
        try:
            user = await api.user_by_login(handle)
            if not user:
                continue
            async for tweet in api.user_tweets(user.id, limit=30):
                if tweet.date < cutoff:
                    break
                if tweet.rawContent:
                    items.append({
                        "title": f"@{handle}",
                        "url": f"https://twitter.com/{handle}/status/{tweet.id}",
                        "content": tweet.rawContent,
                        "source": f"Twitter @{handle}",
                        "published": tweet.date.isoformat(),
                    })
        except Exception as e:
            print(f"  [WARN] @{handle}: {e}")

    return items


def fetch_twitter_section(accounts):
    print(f"  爬取账号: {', '.join('@' + a for a in accounts)}")
    try:
        items = asyncio.run(_fetch(accounts))
    except Exception as e:
        print(f"  [WARN] {e}")
        items = []
    print(f"  获取 {len(items)} 条")
    return {
        "id": "twitter",
        "name": "Twitter/X 动态",
        "items": items,
    }
