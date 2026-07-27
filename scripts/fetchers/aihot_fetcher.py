"""AI HOT 只读聚合 API 抓取。

匿名、无需 API Key，仅需设置 User-Agent 标识请求身份。
⚠️ 只走公开 REST 接口 /api/public/items，不安装其第三方 skill。
返回结构与 rss_fetcher 的 item 对齐，便于统一进入工程解码候选池。
"""
import requests


def fetch_aihot_items(base, endpoint="/items", take=60, user_agent="ai-daily/1.0"):
    url = base.rstrip("/") + endpoint
    try:
        resp = requests.get(
            url,
            params={"take": take},
            headers={"User-Agent": user_agent},
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [AI HOT] 抓取失败: {e}")
        return []

    # 兼容 list 或 {items:[...]} / {data:[...]} 两种返回
    arr = data if isinstance(data, list) else (data.get("items") or data.get("data") or [])

    items = []
    for it in arr:
        items.append({
            "source": "AI HOT",
            "title": it.get("title", ""),
            "summary": it.get("summary", ""),
            "url": it.get("url") or it.get("permalink", ""),
            "time": it.get("publishedAt", ""),
            "eventId": None,
            "relatedDate": None,
            "raw_category": it.get("category", ""),  # 保留原始分类，供 AI 筛选参考
        })
    print(f"  [AI HOT] 抓取 {len(items)} 条")
    return items
