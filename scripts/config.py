import os
from datetime import datetime, timedelta

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MAX_DAYS = 90

now = datetime.now()
TODAY = now.strftime("%Y-%m-%d")
yesterday_9am = (now - timedelta(days=1)).replace(hour=9, minute=0, second=0)
today_9am = now.replace(hour=9, minute=0, second=0)
TIME_RANGE = f"{yesterday_9am.strftime('%Y-%m-%d %H:%M')} ~ {today_9am.strftime('%Y-%m-%d %H:%M')}"

RSS_SOURCES = {
    "arxiv": {
        "name": "学术论文",
        "feeds": [
            {
                "source": "arXiv",
                "url": "https://rss.arxiv.org/rss/cs.AI",
                "label": "arXiv cs.AI",
            },
            {
                "source": "arXiv",
                "url": "https://rss.arxiv.org/rss/cs.CL",
                "label": "arXiv cs.CL",
            },
            {
                "source": "arXiv",
                "url": "https://rss.arxiv.org/rss/cs.LG",
                "label": "arXiv cs.LG",
            },
        ],
    },
    "media": {
        "name": "科技媒体",
        "feeds": [
            {
                "source": "The Verge AI",
                "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
            },
            {
                "source": "MIT Technology Review - AI",
                "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
            },
            {
                "source": "TechCrunch - AI",
                "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
            },
        ],
    },
    "community": {
        "name": "社区论坛",
        "feeds": [
            {
                "source": "Reddit",
                "url": "https://www.reddit.com/r/MachineLearning/hot/.rss",
                "label": "r/MachineLearning",
            },
            {
                "source": "Reddit",
                "url": "https://www.reddit.com/r/artificial/hot/.rss",
                "label": "r/artificial",
            },
            {
                "source": "Hugging Face",
                "url": "https://huggingface.co/blog/feed.xml",
            },
        ],
    },
    "newsletter": {
        "name": "Newsletter 精选",
        "feeds": [
            {
                "source": "The Rundown AI",
                "url": "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml",
            },
            {
                "source": "Towards AI",
                "url": "https://towardsai.net/feed",
            },
            {
                "source": "AI News",
                "url": "https://buttondown.com/ainews/rss",
            },
        ],
    },
    "investment": {
        "name": "投资视角",
        "feeds": [
            # a16z 和 CB Insights 均已关闭 RSS，需要网页爬取
            # 暂用占位，后续实现 web scraper
        ],
    },
}

# 需要网页爬取的源（无 RSS）
WEB_SCRAPE_SOURCES = {
    "investment": {
        "name": "投资视角",
        "sites": [
            {
                "source": "a16z",
                "url": "https://a16z.com/ai",
            },
            {
                "source": "CB Insights - AI",
                "url": "https://www.cbinsights.com/research/artificial-intelligence/",
            },
        ],
    },
    "community_extra": {
        "name": "社区论坛（补充）",
        "sites": [
            {
                "source": "Way to AGI",
                "url": "https://www.waytoagi.com",
            },
        ],
    },
}

# 新产品发布（Product Hunt + HN Show）
PRODUCT_LAUNCH_SOURCES = {
    "name": "新产品发布",
    "feeds": [
        {"source": "Product Hunt", "url": "https://www.producthunt.com/feed"},
        {"source": "HN Show", "url": "https://hnrss.org/show"},
    ],
}

# 痛点挖掘（非AI领域社区）
PAIN_POINT_SOURCES = {
    "name": "痛点信号",
    "feeds": [
        {"source": "r/smallbusiness", "url": "https://www.reddit.com/r/smallbusiness/hot/.rss"},
        {"source": "r/legaladvice",   "url": "https://www.reddit.com/r/legaladvice/hot/.rss"},
        {"source": "r/accounting",    "url": "https://www.reddit.com/r/accounting/hot/.rss"},
        {"source": "r/humanresources","url": "https://www.reddit.com/r/humanresources/hot/.rss"},
        {"source": "r/Teachers",      "url": "https://www.reddit.com/r/Teachers/hot/.rss"},
        {"source": "HN Ask",          "url": "https://hnrss.org/ask"},
    ],
}

# 新产品发布（Product Hunt + HN Show）
PRODUCT_LAUNCH_SOURCES = {
    "name": "新产品发布",
    "feeds": [
        {"source": "Product Hunt", "url": "https://www.producthunt.com/feed"},
        {"source": "HN Show",      "url": "https://hnrss.org/show"},
    ],
}

# 痛点挖掘（非AI领域社区）
PAIN_POINT_SOURCES = {
    "name": "痛点信号",
    "feeds": [
        {"source": "r/smallbusiness",  "url": "https://www.reddit.com/r/smallbusiness/hot/.rss"},
        {"source": "r/legaladvice",    "url": "https://www.reddit.com/r/legaladvice/hot/.rss"},
        {"source": "r/accounting",     "url": "https://www.reddit.com/r/accounting/hot/.rss"},
        {"source": "r/humanresources", "url": "https://www.reddit.com/r/humanresources/hot/.rss"},
        {"source": "r/Teachers",       "url": "https://www.reddit.com/r/Teachers/hot/.rss"},
        {"source": "HN Ask",           "url": "https://hnrss.org/ask"},
    ],
}

TWITTER_ACCOUNTS = [
    # AI 公司官方账号
    "OpenAI", "GoogleDeepMind", "AnthropicAI", "AIatMeta",
    "midjourney", "runwayml", "deepseek_ai", "Alibaba_Qwen",
    "Kimi_Moonshot", "MiniMax_AI",
    # AI 领域意见领袖
    "sama", "karpathy", "demishassabis", "geoffreyhinton",
    "ylecun", "yoshua_bengio", "lexfridman",
]

# ══════════════════════════════════════════════════════════════
# 第四版：工程解码（独立学习页）
# 面向非技术 PM，累积精选技术深度内容，建立技术边界判断力 + vibe coding 企业闭环认知
# ══════════════════════════════════════════════════════════════

# RSS 源：讲技术实现 / 技术边界 / 工程落地闭环
TECH_DECODE_RSS = {
    "name": "工程解码",
    "feeds": [
        {"source": "Simon Willison", "url": "https://simonwillison.net/atom/everything/"},
        {"source": "Latent Space", "url": "https://www.latent.space/feed"},
        {"source": "GitHub Blog", "url": "https://github.blog/ai-and-ml/feed/"},
    ],
}

# AI HOT 只读聚合 API（匿名，无需 API Key，仅需 User-Agent）
# ⚠️ 只走公开 REST 接口，不安装其第三方 skill
AIHOT_API = {
    "base": "https://aihot.virxact.com/api/public",
    "items_endpoint": "/items",
    "user_agent": "ai-daily-tech-decode/1.0 (+https://github.com/lingq932/ai-daily)",
    "take": 60,
}

# 工程解码累积数据文件（长期留存，不受 90 天清理）
LEARNING_FILE = os.path.join(DATA_DIR, "learning.json")

# 工程解码三大主题
TECH_DECODE_CATEGORIES = ["技术实现", "技术边界", "vibe coding 企业闭环"]

# ══════════════════════════════════════════════════════════════
# 工程解码·最佳实践子区
# 从真实案例提炼"某场景 / 某技术怎么落地"的方法论，每周归纳一次
# ══════════════════════════════════════════════════════════════

# 保底关注的业务场景（其余由 AI 从案例自动归纳）
BEST_PRACTICE_SCENARIOS = ["客服", "办公", "销售", "数据分析", "营销"]
# 偏好：优先 2C（面向消费者/个人用户）实践
BEST_PRACTICE_PREFER_2C = True
# 累积数据文件（长期留存，不受 90 天清理）
BEST_PRACTICE_FILE = os.path.join(DATA_DIR, "best_practices.json")
# 每周生成日：6 = 周日（Python weekday，周一=0）
BEST_PRACTICE_WEEKDAY = 6
