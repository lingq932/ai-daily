import os
import sys
import json
import argparse
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    RSS_SOURCES, WEB_SCRAPE_SOURCES, TWITTER_ACCOUNTS,
    DATA_DIR, MAX_DAYS,
)
from fetchers.rss_fetcher import fetch_rss_section
from fetchers.twitter_fetcher import fetch_twitter_section
from fetchers.web_scraper import fetch_web_scrape_section
from ai_processor import translate_and_summarize, detect_hot_topics


def get_time_range(target_date_str):
    """返回目标日期的时间范围：前一天9点 ~ 当天9点（UTC+8）"""
    target = datetime.strptime(target_date_str, "%Y-%m-%d")
    tz_cst = timezone(timedelta(hours=8))

    time_to = target.replace(hour=9, minute=0, second=0, tzinfo=tz_cst)
    time_from = (target - timedelta(days=1)).replace(hour=9, minute=0, second=0, tzinfo=tz_cst)

    range_str = f"{time_from.strftime('%Y-%m-%d %H:%M')} ~ {time_to.strftime('%Y-%m-%d %H:%M')}"
    return time_from, time_to, range_str


def main(target_date=None):
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    time_from, time_to, time_range = get_time_range(target_date)

    print(f"=== AI 日报数据生成 ===")
    print(f"日期: {target_date}")
    print(f"时段: {time_range}")
    print()

    # 检查文件是否已存在
    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, f"{target_date}.json")
    if os.path.exists(output_path):
        print(f"[SKIP] {target_date}.json 已存在，跳过")
        return

    sections = []

    # 1. Twitter/X
    print("[1/6] Twitter/X 动态")
    twitter_section = fetch_twitter_section(TWITTER_ACCOUNTS, time_from=time_from, time_to=time_to)
    sections.append(twitter_section)

    # 2. Newsletter
    print("[2/6] Newsletter 精选")
    newsletter = fetch_rss_section("newsletter", RSS_SOURCES["newsletter"], time_from=time_from, time_to=time_to)
    sections.append(newsletter)

    # 3. 科技媒体
    print("[3/6] 科技媒体")
    media = fetch_rss_section("media", RSS_SOURCES["media"], time_from=time_from, time_to=time_to)
    sections.append(media)

    # 4. 投资视角
    print("[4/6] 投资视角")
    investment_rss = fetch_rss_section("investment", RSS_SOURCES.get("investment", {"name": "投资视角", "feeds": []}), time_from=time_from, time_to=time_to)
    investment_web = fetch_web_scrape_section("investment", WEB_SCRAPE_SOURCES.get("investment", {"name": "投资视角", "sites": []}))
    investment = {
        "id": "investment",
        "name": "投资视角",
        "items": investment_rss["items"] + investment_web["items"],
    }
    sections.append(investment)

    # 5. 社区论坛
    print("[5/6] 社区论坛")
    community_rss = fetch_rss_section("community", RSS_SOURCES["community"], time_from=time_from, time_to=time_to)
    community_web = fetch_web_scrape_section("community", WEB_SCRAPE_SOURCES.get("community_extra", {"name": "社区论坛（补充）", "sites": []}))
    community = {
        "id": "community",
        "name": "社区论坛",
        "items": community_rss["items"] + community_web["items"],
    }
    sections.append(community)

    # 6. 学术论文
    print("[6/6] 学术论文")
    arxiv = fetch_rss_section("arxiv", RSS_SOURCES["arxiv"], time_from=time_from, time_to=time_to)
    arxiv["id"] = "papers"
    sections.append(arxiv)

    # AI 翻译和摘要
    print("\n--- AI 处理 ---")
    for section in sections:
        if section["items"]:
            print(f"处理: {section['name']} ({len(section['items'])} 条)")
            section["items"] = translate_and_summarize(section["items"], section["name"])

    # 去除空板块
    sections = [s for s in sections if s["items"]]

    if not sections:
        print(f"[SKIP] {target_date} 无任何内容，不生成文件")
        return

    # 热点检测
    print("\n--- 热点检测 ---")
    hot_topics = detect_hot_topics(sections)
    if hot_topics:
        print(f"发现 {len(hot_topics)} 个热点")
        sections.insert(0, {
            "id": "hot_topics",
            "name": "热点头条",
            "items": hot_topics,
        })
    else:
        print("无跨媒体热点")

    # 生成 JSON
    data = {
        "date": target_date,
        "timeRange": time_range,
        "sections": sections,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total_items = sum(len(s['items']) for s in sections)
    print(f"\n=== 完成 {target_date} === {len(sections)} 板块 / {total_items} 条")


def cleanup_old_data():
    cutoff = datetime.now() - timedelta(days=MAX_DAYS)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    removed = 0
    if not os.path.exists(DATA_DIR):
        return
    for fname in os.listdir(DATA_DIR):
        if not fname.endswith(".json"):
            continue
        if fname.replace(".json", "") < cutoff_str:
            os.remove(os.path.join(DATA_DIR, fname))
            removed += 1
    if removed:
        print(f"[清理] 已删除 {removed} 个过期文件")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="目标日期 YYYY-MM-DD，默认今天")
    args = parser.parse_args()
    main(args.date)
    cleanup_old_data()
