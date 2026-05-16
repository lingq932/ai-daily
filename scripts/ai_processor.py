import json as _json
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

def get_client():
    if not DEEPSEEK_API_KEY:
        return None
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def translate_and_summarize(items, section_name):
    client = get_client()
    if not client:
        print(f"  [SKIP] DeepSeek API key 未设置，跳过 AI 处理")
        return items

    processed = []
    for item in items:
        try:
            result = process_single_item(client, item)
            processed.append(result)
        except Exception as e:
            print(f"  [AI FAIL] {item.get('source', '?')}: {e}")
            processed.append(item)

    return processed


def process_single_item(client, item):
    title = item.get("title", "")
    summary = item.get("summary", "")

    is_chinese = any('一' <= c <= '鿿' for c in title)
    if is_chinese and len(summary) <= 200:
        return item

    prompt = f"""你是一个 AI 新闻编辑。请完成以下任务：

1. 如果标题是英文，翻译成简洁的中文标题
2. 如果摘要是英文，翻译成中文
3. 将摘要精简到 2-3 句话（80-150 字），保留核心信息

术语表（必须严格遵守）：
- Sam Altman → 山姆·奥特曼
- Yann LeCun → 杨立昆
- Andrej Karpathy → 安德烈·卡帕西
- Geoffrey Hinton → 杰弗里·辛顿
- Yoshua Bengio → 约书亚·本吉奥
- Demis Hassabis → 德米斯·哈萨比斯
- Lex Fridman → 列克斯·弗里德曼

原始标题：{title}
原始摘要：{summary}

请严格按以下 JSON 格式返回，不要添加其他内容：
{{"title": "中文标题", "summary": "中文摘要"}}"""

    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )

    text = resp.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    result = _json.loads(text)
    item["title"] = result.get("title", title)
    item["summary"] = result.get("summary", summary)
    return item


def detect_hot_topics(sections):
    """跨板块检测多媒体共同报道的热点事件"""
    client = get_client()
    if not client:
        return []

    # 收集所有非 Twitter 条目
    all_items = []
    for sec in sections:
        if sec["id"] in ("twitter", "hot_topics"):
            continue
        for item in sec.get("items", []):
            all_items.append({
                "idx": len(all_items),
                "source": item.get("source", ""),
                "title": item.get("title", ""),
                "summary": item.get("summary", "")[:80],
                "url": item.get("url", ""),
            })

    if len(all_items) < 4:
        return []

    lines = [f"{i['idx']}. [{i['source']}] {i['title']}" for i in all_items]
    prompt = f"""以下是今日 AI 新闻标题，找出被 2 个或以上不同媒体报道的相同事件。

{chr(10).join(lines)}

规则：
- 必须是真正相同的事件（同一公司/产品/事件），不是同类话题
- 每个热点至少 2 个不同来源
- 标题简洁（15字以内）
- 最多 4 个热点，没有则返回空数组

JSON格式（严格）：
[{{"headline": "热点标题", "indices": [0, 3]}}]"""

    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        clusters = _json.loads(text)

        hot_items = []
        for cluster in clusters:
            headline = cluster.get("headline", "")
            indices = cluster.get("indices", [])
            coverage = []
            seen_sources = set()
            for idx in indices:
                if 0 <= idx < len(all_items):
                    item = all_items[idx]
                    if item["source"] not in seen_sources:
                        seen_sources.add(item["source"])
                        coverage.append({
                            "source": item["source"],
                            "summary": item["summary"],
                            "url": item["url"],
                        })
            if len(coverage) >= 2:
                hot_items.append({"headline": headline, "coverage": coverage})

        return hot_items
    except Exception as e:
        print(f"  [WARN] 热点检测失败: {e}")
        return []
