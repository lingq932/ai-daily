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

TWITTER_ACCOUNTS = [
    # AI 公司官方账号
    "OpenAI", "GoogleDeepMind", "AnthropicAI", "AIatMeta",
    "midjourney", "runwayml", "deepseek_ai", "Alibaba_Qwen",
    "Kimi_Moonshot", "MiniMax_AI",
    # AI 领域意见领袖
    "sama", "karpathy", "demishassabis", "geoffreyhinton",
    "ylecun", "yoshua_bengio", "lexfridman",
]
