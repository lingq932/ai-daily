import os
import sys
import json
import argparse
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    RSS_SOURCES, WEB_SCRAPE_SOURCES,
    PRODUCT_LAUNCH_SOURCES, PAIN_POINT_SOURCES,
    TWITTER_ACCOUNTS, DATA_DIR, MAX_DAYS,
    TECH_DECODE_RSS, AIHOT_API, LEARNING_FILE,
    BEST_PRACTICE_FILE, BEST_PRACTICE_WEEKDAY,
)
from fetchers.rss_fetcher import fetch_rss_section
from fetchers.twitter_fetcher import fetch_twitter_section
from fetchers.web_scraper import fetch_web_scrape_section, fetch_github_trending
from fetchers.aihot_fetcher import fetch_aihot_items
from learning_store import merge_learning
from best_practices_store import merge_bp
from ai_processor import (
    translate_and_summarize,
    filter_ai_relevant,
    detect_pain_points,
    generate_opportunities,
    detect_hot_topics,
    curate_tech_learning,
    generate_best_practices,
)


def get_time_range(target_date_str):
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
    print(f"日期: {target_date} | 时段: {time_range}")
    print()

    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, f"{target_date}.json")
    if os.path.exists(output_path):
        print(f"[SKIP] {target_date}.json 已存在")
        return

    sections = []

    # ── 市场信号层 ──────────────────────────────────────────
    print("[新产品发布] 抓取 Product Hunt + HN Show...")
    products_raw = fetch_rss_section("products", PRODUCT_LAUNCH_SOURCES,
                                     time_from=time_from, time_to=time_to, max_per_feed=20)
    sections.append(products_raw)

    print("[GitHub热榜] 爬取 Trending...")
    github_raw_items = fetch_github_trending()
    sections.append({
        "id": "github_trending",
        "name": "GitHub 热榜",
        "items": github_raw_items,
    })

    print("[痛点信号] 抓取非AI社区...")
    pain_raw = fetch_rss_section("pain_points_raw", PAIN_POINT_SOURCES,
                                 time_from=time_from, time_to=time_to, max_per_feed=15)

    # ── 舆论与观点层 ────────────────────────────────────────
    print("[Twitter/X] 爬取意见领袖...")
    twitter = fetch_twitter_section(TWITTER_ACCOUNTS, time_from=time_from, time_to=time_to)
    sections.append(twitter)

    print("[Newsletter] 抓取...")
    newsletter = fetch_rss_section("newsletter", RSS_SOURCES["newsletter"],
                                   time_from=time_from, time_to=time_to)
    sections.append(newsletter)

    print("[科技媒体] 抓取...")
    media = fetch_rss_section("media", RSS_SOURCES["media"],
                               time_from=time_from, time_to=time_to)
    sections.append(media)

    # ── 专业层 ──────────────────────────────────────────────
    print("[投资视角] 抓取...")
    investment_rss = fetch_rss_section(
        "investment",
        RSS_SOURCES.get("investment", {"name": "投资视角", "feeds": []}),
        time_from=time_from, time_to=time_to,
    )
    investment_web = fetch_web_scrape_section(
        "investment",
        WEB_SCRAPE_SOURCES.get("investment", {"name": "投资视角", "sites": []}),
    )
    sections.append({
        "id": "investment",
        "name": "投资视角",
        "items": investment_rss["items"] + investment_web["items"],
    })

    print("[社区论坛] 抓取...")
    community_rss = fetch_rss_section("community", RSS_SOURCES["community"],
                                       time_from=time_from, time_to=time_to)
    community_web = fetch_web_scrape_section(
        "community",
        WEB_SCRAPE_SOURCES.get("community_extra", {"name": "社区论坛（补充）", "sites": []}),
    )
    sections.append({
        "id": "community",
        "name": "社区论坛",
        "items": community_rss["items"] + community_web["items"],
    })

    print("[学术论文] 抓取...")
    arxiv = fetch_rss_section("arxiv", RSS_SOURCES["arxiv"],
                               time_from=time_from, time_to=time_to)
    arxiv["id"] = "papers"
    sections.append(arxiv)

    # ── AI 处理 ─────────────────────────────────────────────
    print("\n--- AI 处理 ---")

    # 新产品发布：翻译 + 过滤 AI 相关
    for sec in sections:
        if sec["id"] == "products" and sec["items"]:
            print(f"过滤 AI 相关产品（{len(sec['items'])} 条）...")
            sec["items"] = filter_ai_relevant(sec["items"], context="新产品")

    # GitHub热榜：过滤 AI 相关
    for sec in sections:
        if sec["id"] == "github_trending" and sec["items"]:
            print(f"过滤 AI 相关仓库（{len(sec['items'])} 条）...")
            sec["items"] = filter_ai_relevant(sec["items"], context="GitHub仓库")

    # 其余板块：普通翻译摘要
    skip_ai_filter = {"products", "github_trending"}
    for section in sections:
        if section["id"] in skip_ai_filter:
            continue
        if section["items"]:
            print(f"翻译: {section['name']} ({len(section['items'])} 条)")
            section["items"] = translate_and_summarize(section["items"], section["name"])

    # 痛点提炼（用原始帖子，不走普通翻译）
    print("提炼痛点信号...")
    pain_items = detect_pain_points(pain_raw["items"]) if pain_raw["items"] else []
    if pain_items:
        sections.append({
            "id": "pain_points",
            "name": "痛点信号",
            "items": pain_items,
        })

    # 去除空板块
    sections = [s for s in sections if s["items"]]

    # 热点检测
    print("\n--- 热点检测 ---")
    hot_topics = detect_hot_topics(sections)
    if hot_topics:
        print(f"发现 {len(hot_topics)} 个热点")
        sections.insert(0, {"id": "hot_topics", "name": "热点头条", "items": hot_topics})
    else:
        print("无跨媒体热点")

    # 今日 AI 机会（最后生成，基于所有内容）
    print("\n--- 生成今日 AI 机会 ---")
    opp_items = generate_opportunities(sections)
    if opp_items:
        # 插入到 hot_topics 之后（总览层第二位）
        insert_pos = 1 if sections and sections[0]["id"] == "hot_topics" else 0
        sections.insert(insert_pos, {
            "id": "opportunities",
            "name": "今日 AI 机会",
            "items": opp_items,
        })

    if not sections:
        print(f"[SKIP] {target_date} 无任何内容")
        return

    # 生成 JSON
    data = {
        "date": target_date,
        "timeRange": time_range,
        "sections": sections,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(len(s["items"]) for s in sections)
    print(f"\n=== 完成 {target_date} === {len(sections)} 板块 / {total} 条")


def run_tech_decode(target_date=None):
    """第四版·工程解码：采集专属源 + AI 严筛 + 累积进 learning.json。

    独立于每日 json：不写进 data/YYYY-MM-DD.json，而是追加到 data/learning.json，
    长期留存、不受 90 天清理。某个源失败不影响主日报。
    """
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
    time_from, time_to, _ = get_time_range(target_date)

    print("\n=== 工程解码（技术边界 / vibe coding 闭环）===")
    try:
        rss = fetch_rss_section("tech_decode", TECH_DECODE_RSS,
                                time_from=time_from, time_to=time_to, max_per_feed=15)
        aihot = fetch_aihot_items(AIHOT_API["base"], AIHOT_API["items_endpoint"],
                                  take=AIHOT_API["take"], user_agent=AIHOT_API["user_agent"])
        candidates = rss["items"] + aihot
        print(f"候选 {len(candidates)} 条")
        if not candidates:
            return
        picks = curate_tech_learning(candidates)
        if picks:
            added, total = merge_learning(LEARNING_FILE, picks, today=target_date)
            print(f"工程解码：新增 {added} / 累计 {total}")
        else:
            print("工程解码：今日无合格内容（宁缺毋滥）")
    except Exception as e:
        print(f"[WARN] 工程解码失败（不影响主日报）: {e}")


def run_tech_decode(target_date):
    """第四版·工程解码：采集专属源 + DeepSeek 严筛 + 累积进 learning.json。
    独立于每日 json，自带去重，不受 90 天清理。"""
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
    time_from, time_to, _ = get_time_range(target_date)

    print("\n=== 工程解码（技术边界 / vibe coding 闭环）===")
    rss = fetch_rss_section("tech_decode", TECH_DECODE_RSS,
                            time_from=time_from, time_to=time_to, max_per_feed=15)
    aihot = fetch_aihot_items(AIHOT_API["base"], AIHOT_API["items_endpoint"],
                              take=AIHOT_API["take"], user_agent=AIHOT_API["user_agent"])
    candidates = rss["items"] + aihot
    print(f"候选 {len(candidates)} 条")
    if not candidates:
        return
    picks = curate_tech_learning(candidates)
    if picks:
        added, total = merge_learning(LEARNING_FILE, picks, today=target_date)
        print(f"工程解码：新增 {added} / 累计 {total}")
    else:
        print("工程解码：今日无合格内容")


def run_best_practices(target_date=None):
    """工程解码·最佳实践：每周日归纳一次。

    抓最近 7 天候选 → DeepSeek 提炼"某场景/某技术怎么落地" → 累积进 best_practices.json。
    非周日直接跳过。独立于每日 json 与工程解码卡片流，失败不影响主日报。
    """
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    if datetime.strptime(target_date, "%Y-%m-%d").weekday() != BEST_PRACTICE_WEEKDAY:
        print("\n=== 最佳实践：非生成日（每周日跑），跳过 ===")
        return

    print("\n=== 最佳实践（每周归纳·某场景/某技术怎么落地）===")
    try:
        tz_cst = timezone(timedelta(hours=8))
        target = datetime.strptime(target_date, "%Y-%m-%d")
        time_to = target.replace(hour=9, minute=0, second=0, tzinfo=tz_cst)
        time_from = (target - timedelta(days=7)).replace(hour=9, minute=0, second=0, tzinfo=tz_cst)

        rss = fetch_rss_section("best_practice", TECH_DECODE_RSS,
                                time_from=time_from, time_to=time_to, max_per_feed=30)
        aihot = fetch_aihot_items(AIHOT_API["base"], AIHOT_API["items_endpoint"],
                                  take=AIHOT_API["take"], user_agent=AIHOT_API["user_agent"])
        candidates = rss["items"] + aihot
        print(f"最近 7 天候选 {len(candidates)} 条")
        if not candidates:
            return
        picks = generate_best_practices(candidates)
        if picks:
            added, total = merge_bp(BEST_PRACTICE_FILE, picks, today=target_date)
            print(f"最佳实践：新增 {added} / 累计 {total}")
        else:
            print("最佳实践：本周无合格内容（宁缺毋滥）")
    except Exception as e:
        print(f"[WARN] 最佳实践失败（不影响主日报）: {e}")


def cleanup_old_data():
    cutoff = datetime.now() - timedelta(days=MAX_DAYS)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    removed = 0
    if not os.path.exists(DATA_DIR):
        return
    for fname in os.listdir(DATA_DIR):
        if fname.endswith(".json") and fname.replace(".json", "") < cutoff_str:
            os.remove(os.path.join(DATA_DIR, fname))
            removed += 1
    if removed:
        print(f"[清理] 已删除 {removed} 个过期文件")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="目标日期 YYYY-MM-DD，默认今天")
    args = parser.parse_args()
    main(args.date)
    run_tech_decode(args.date)
    run_best_practices(args.date)
    cleanup_old_data()
