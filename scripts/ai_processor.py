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


def filter_ai_relevant(items, context="产品"):
    """用 AI 过滤，只保留与 AI/ML 相关的条目，并翻译/扩写摘要"""
    client = get_client()
    if not client:
        return items

    if not items:
        return []

    is_github = context == "GitHub仓库"

    if is_github:
        lines = [
            f"{i}. {item.get('title','')} | {item.get('summary','')[:80]} | 语言:{item.get('language','')} | {item.get('time','')}"
            for i, item in enumerate(items)
        ]
        extra = """- 对保留的每个仓库，用2-3句话写清楚：这是什么工具/框架、解决什么问题、为什么值得关注（结合今日star数和语言背景）
- 摘要要有实质内容，不能只重复原始描述"""
    else:
        lines = [f"{i}. [{item.get('source','')}] {item.get('title','')} | {item.get('summary','')[:80]}"
                 for i, item in enumerate(items)]
        extra = "- 将标题和摘要翻译为中文（若已是中文则保留）"

    prompt = f"""以下是今日{context}列表，请判断每条是否与 AI/ML/LLM/生成式AI 相关。

{chr(10).join(lines)}

规则：
- 只保留明确与 AI、机器学习、大语言模型、生成式AI相关的条目
{extra}
- 没有相关条目则返回空数组

JSON格式（严格）：
[{{"idx": 0, "title": "中文标题或原名", "summary": "中文说明"}}]"""

    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=800,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        results = _json.loads(text)

        filtered = []
        for r in results:
            idx = r.get("idx")
            if idx is not None and 0 <= idx < len(items):
                item = dict(items[idx])
                item["title"] = r.get("title", item["title"])
                item["summary"] = r.get("summary", item["summary"])
                filtered.append(item)
        print(f"  AI过滤：{len(items)} → {len(filtered)} 条")
        return filtered
    except Exception as e:
        print(f"  [WARN] AI过滤失败: {e}")
        return items


def detect_pain_points(raw_items):
    """从非AI社区帖子中提炼痛点信号"""
    client = get_client()
    if not client or not raw_items:
        return []

    lines = [f"{i}. [{item.get('source','')}] {item.get('title','')} | {item.get('summary','')[:100]}"
             for i, item in enumerate(raw_items[:60])]

    prompt = f"""以下是来自小企业主、法律、财务、HR、教育等非AI领域社区的帖子。

{chr(10).join(lines)}

请找出其中3-5个"用户正在手动做、但明显可以被AI自动化"的具体任务场景。

要求：
- 必须是具体的操作性任务，不是泛泛的抱怨
- 信号越具体越好（如"每周手动核对银行流水"比"工作很累"好）
- 每条附上来源帖子的序号

JSON格式（严格）：
[{{
  "title": "场景名称（10字以内）",
  "summary": "具体描述这个手动任务的痛苦程度，以及AI可以如何解决（80-120字）",
  "source_idx": 0,
  "opportunity": "潜在AI产品方向（一句话）"
}}]"""

    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        results = _json.loads(text)

        items = []
        for r in results:
            idx = r.get("source_idx", 0)
            source_item = raw_items[idx] if 0 <= idx < len(raw_items) else {}
            summary = r.get("summary", "")
            opportunity = r.get("opportunity", "")
            if opportunity:
                summary = summary + f"\n\n💡 机会方向：{opportunity}"
            items.append({
                "title": r.get("title", ""),
                "summary": summary,
                "source": source_item.get("source", ""),
                "url": source_item.get("url", ""),
                "time": "",
                "eventId": None,
                "relatedDate": None,
            })
        print(f"  提炼痛点：{len(items)} 条")
        return items
    except Exception as e:
        print(f"  [WARN] 痛点提炼失败: {e}")
        return []


def generate_opportunities(sections):
    """基于当天所有内容，生成今日AI机会"""
    client = get_client()
    if not client:
        return []

    # 压缩各板块内容
    lines = []
    skip_ids = {"opportunities", "hot_topics"}
    for sec in sections:
        if sec["id"] in skip_ids:
            continue
        for item in sec.get("items", [])[:5]:
            lines.append(f"[{sec['name']}] {item.get('title','')}：{item.get('summary','')[:60]}")

    if len(lines) < 3:
        return []

    content = chr(10).join(lines[:40])

    prompt = f"""你是一个 AI 创业导师。以下是今日 AI 日报的核心内容摘要：

{content}

基于以上信息，推导3个独立开发者可以在1-2周内完成MVP的AI产品机会。

要求：
- 必须有明确的用户群体和解决的具体问题
- MVP 功能必须极度精简（一句话能说清楚）
- 信号来源必须对应上面的真实内容

JSON格式（严格）：
[{{
  "title": "产品名（假设）",
  "problem": "解决什么人的什么问题（一句话）",
  "mvp": "MVP核心功能（一句话）",
  "signal": "信号来源（来自哪个板块的什么内容）"
}}]"""

    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=600,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        results = _json.loads(text)

        items = []
        for r in results:
            summary = (
                f"问题：{r.get('problem','')}\n"
                f"MVP：{r.get('mvp','')}\n"
                f"信号来源：{r.get('signal','')}"
            )
            items.append({
                "title": r.get("title", ""),
                "summary": summary,
                "source": "AI 机会分析",
                "url": "",
                "time": "",
                "eventId": None,
                "relatedDate": None,
            })
        print(f"  生成机会：{len(items)} 条")
        return items
    except Exception as e:
        print(f"  [WARN] 机会生成失败: {e}")
        return []


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
