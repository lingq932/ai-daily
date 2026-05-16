import os
import sys
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    RSS_SOURCES, WEB_SCRAPE_SOURCES, TWITTER_ACCOUNTS,
    DATA_DIR, TODAY, TIME_RANGE, MAX_DAYS,
)
from fetchers.rss_fetcher import fetch_rss_section
from fetchers.twitter_fetcher import fetch_twitter_section
from fetchers.web_scraper import fetch_web_scrape_section
from ai_processor import translate_and_summarize


def main():
    print(f"=== AI 日报数据生成 ===")
    print(f"日期: {TODAY}")
    print(f"时段: {TIME_RANGE}")
    print()

    sections = []

    # 1. Twitter/X（P3，占位）
    print("[1/6] Twitter/X 动态")
    twitter_section = fetch_twitter_section(TWITTER_ACCOUNTS)
    sections.append(twitter_section)

    # 2. Newsletter
    print("[2/6] Newsletter 精选")
    newsletter = fetch_rss_section("newsletter", RSS_SOURCES["newsletter"])
    sections.append(newsletter)

    # 3. 科技媒体
    print("[3/6] 科技媒体")
    media = fetch_rss_section("media", RSS_SOURCES["media"])
    sections.append(media)

    # 4. 投资视角（RSS + 网页爬取合并）
    print("[4/6] 投资视角")
    investment_rss = fetch_rss_section("investment", RSS_SOURCES.get("investment", {"name": "投资视角", "feeds": []}))
    investment_web = fetch_web_scrape_section("investment", WEB_SCRAPE_SOURCES.get("investment", {"name": "投资视角", "sites": []}))
    investment = {
        "id": "investment",
        "name": "投资视角",
        "items": investment_rss["items"] + investment_web["items"],
    }
    sections.append(investment)

    # 5. 社区论坛（RSS + 网页爬取合并）
    print("[5/6] 社区论坛")
    community_rss = fetch_rss_section("community", RSS_SOURCES["community"])
    community_web = fetch_web_scrape_section("community", WEB_SCRAPE_SOURCES.get("community_extra", {"name": "社区论坛（补充）", "sites": []}))
    community = {
        "id": "community",
        "name": "社区论坛",
        "items": community_rss["items"] + community_web["items"],
    }
    sections.append(community)

    # 6. 学术论文
    print("[6/6] 学术论文")
    arxiv = fetch_rss_section("arxiv", RSS_SOURCES["arxiv"])
    # arXiv 更名为 papers 匹配前端
    arxiv["id"] = "papers"
    sections.append(arxiv)

    # AI 翻译和摘要
    print("\n--- AI 处理 ---")
    for section in sections:
        if section["items"]:
            print(f"处理: {section['name']} ({len(section['items'])} 条)")
            section["items"] = translate_and_summarize(
                section["items"], section["name"]
            )

    # 去除空板块
    sections = [s for s in sections if s["items"]]

    # 生成 JSON
    data = {
        "date": TODAY,
        "timeRange": TIME_RANGE,
        "sections": sections,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, f"{TODAY}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完成 ===")
    print(f"文件: {output_path}")
    print(f"板块: {len(sections)}")
    total_items = sum(len(s['items']) for s in sections)
    print(f"总条数: {total_items}")

    cleanup_old_data()


def cleanup_old_data():
    cutoff = datetime.now() - timedelta(days=MAX_DAYS)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    removed = 0

    if not os.path.exists(DATA_DIR):
        return

    for fname in os.listdir(DATA_DIR):
        if not fname.endswith(".json"):
            continue
        date_str = fname.replace(".json", "")
        if date_str < cutoff_str:
            os.remove(os.path.join(DATA_DIR, fname))
            removed += 1

    if removed:
        print(f"[清理] 已删除 {removed} 个超过 {MAX_DAYS} 天的数据文件")


if __name__ == "__main__":
    main()
