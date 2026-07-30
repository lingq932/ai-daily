import json as _json
import hashlib
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
        extra = """- 对保留的每个仓库，用中文2-3句话写清楚：这是什么工具/框架、解决什么问题、为什么值得关注（结合今日star数和语言背景）
- summary 必须用中文撰写，不能使用英文！title 可保留仓库原名
- 摘要要有实质内容，不能只重复原始描述
- 额外分析商业缺口：这个仓库周围缺什么付费产品？（不是"托管这个repo"，而是它周围缺什么治理/审计/成本/采用证据层，一句话）"""
    else:
        lines = [f"{i}. [{item.get('source','')}] {item.get('title','')} | {item.get('summary','')[:80]}"
                 for i, item in enumerate(items)]
        extra = ""

    if is_github:
        json_format = '[{"idx": 0, "title": "中文标题（必须翻译为中文）", "summary": "中文说明（必须是中文）", "gap": "商业缺口一句话"}]'
    else:
        json_format = '[{"idx": 0, "title": "中文标题（必须翻译为中文）", "summary": "中文摘要（必须是中文）"}]'

    prompt = f"""以下是今日{context}列表，请完成两个任务：1）判断是否与AI相关；2）将保留条目翻译为中文。

{chr(10).join(lines)}

规则：
- 只保留明确与 AI、机器学习、大语言模型、生成式AI相关的条目
- ⚠️ 重要：所有保留条目的 title 和 summary 必须翻译为中文！英文标题必须翻译，英文摘要必须翻译。已是中文则保留。
{extra}
- 没有相关条目则返回空数组

JSON格式（严格，title和summary必须是中文）：
{json_format}"""

    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000,
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
                summary = r.get("summary", item["summary"])
                gap = r.get("gap", "")
                if gap:
                    summary = summary + f"\n\n💼 商业缺口：{gap}"
                item["summary"] = summary
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

    content = chr(10).join(lines[:60])

    prompt = f"""你是一个 AI 创业顾问，专门帮 solo founder 找今日最值得行动的产品机会。以下是今日 AI 日报的核心内容摘要，每条标注了来源板块：

{content}

基于以上信息，推导3个独立开发者可以在1-2周内完成MVP的AI产品机会。

要求：
- 优先推导有多个不同板块同时佐证的机会——同一个痛点在【GitHub热榜】【痛点信号】【新产品发布】等多个板块都有体现，说明信号更强
- 买家必须具体（不是"用户"，而是"每天手动核对账单的财务负责人"这种粒度）
- 必须说清楚为什么是今天——列出哪几个板块的哪些内容作为需求证据
- MVP 功能极度精简（一句话说清楚能交付什么产物，要有具体输入和输出）
- 验证路径必须是今天就能做的第一步（找谁、问什么、发什么）
- 不要推导泛泛的"AI助手"类产品，要有具体交付物

JSON格式（严格）：
[{{
  "title": "产品名（假设）",
  "buyer": "具体买家是谁（职位/场景，一句话）",
  "problem": "他们现在手动在做什么、痛在哪里（一句话）",
  "mvp": "MVP交付什么产物（一句话，说清楚输入和输出）",
  "signal": "今日触发信号（列出支撑这个机会的所有板块和内容）",
  "source_count": 2,
  "validation": "最快验证路径（今天就能做的第一步）"
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
            source_count = r.get('source_count', 1)
            source_label = f"（{source_count}个板块佐证）" if source_count > 1 else ""
            summary = (
                f"买家：{r.get('buyer','')}\n"
                f"痛点：{r.get('problem','')}\n"
                f"MVP：{r.get('mvp','')}\n"
                f"今日触发信号{source_label}：{r.get('signal','')}\n"
                f"最快验证：{r.get('validation','')}"
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


def curate_tech_learning(candidates, max_keep=8):
    """第四版·工程解码：从候选池严筛 + 归主题 + 重写三段式。

    candidates: [{source, title, summary, url, ...}]
    返回: [{category, title, whatIsIt, boundary, whyLearn, source, url}]
    宁缺毋滥——没有合格的返回空数组。
    """
    client = get_client()
    if not client or not candidates:
        return []

    lines = [
        f"{i}. [{c.get('source','')}] {c.get('title','')} | {c.get('summary','')[:120]}"
        for i, c in enumerate(candidates)
    ]

    prompt = f"""你是一位专门帮【非技术出身的 AI 产品经理】挑技术选题的导师。她的目标是建立技术边界判断力——搞懂某类技术能做到什么、做不到什么、代价多大，以及企业怎么把 vibe coding 落成闭环。

以下是今日候选内容（来源 + 标题 + 摘要）：
{chr(10).join(lines)}

第一步 严筛（宁缺毋滥）：只保留真正能帮她长技术判断力的，满足其一：
- 讲某个 AI 技术/能力怎么实现、原理或架构
- 讲某技术的边界、局限、失败案例、代价
- 讲 AI coding / agent 在真实团队或企业里怎么落地、怎么跑成闭环
明确丢弃：纯融资/人事/发布会八卦、泛泛"AI 很厉害"、纯产品导购、和技术认知无关的行业新闻。没有合格的就返回空数组，不要凑数。

第二步 归主题：每条归入 技术实现 / 技术边界 / vibe coding 企业闭环 之一。

第三步 重写三段式（中文，PM 水位，不堆术语）：
- whatIsIt：一句话讲清这是什么
- boundary：技术边界（重点）——能做到 X，做不到 Y，前提/代价是 Z
- whyLearn：为什么值得她学，能用在哪

严格按 JSON 返回，最多 {max_keep} 条，不要输出其他内容：
[{{"category":"技术边界","title":"中文标题","whatIsIt":"...","boundary":"...","whyLearn":"...","idx":原候选序号}}]"""

    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=3000,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        results = _json.loads(text)

        items = []
        for r in results:
            idx = r.get("idx")
            src = candidates[idx] if (idx is not None and 0 <= idx < len(candidates)) else {}
            items.append({
                "category": r.get("category", "技术实现"),
                "title": r.get("title", src.get("title", "")),
                "whatIsIt": r.get("whatIsIt", ""),
                "boundary": r.get("boundary", ""),
                "whyLearn": r.get("whyLearn", ""),
                "source": src.get("source", ""),
                "url": src.get("url", ""),
            })
        print(f"  工程解码严筛：{len(candidates)} → {len(items)} 条")
        return items[:max_keep]
    except Exception as e:
        print(f"  [WARN] 工程解码筛选失败: {e}")
        return []


def generate_best_practices(candidates, max_keep=3):
    """工程解码·最佳实践：从最近 7 天真实案例提炼"某场景/某技术怎么落地"的方法论。

    candidates: [{source, title, summary, url, ...}]
    返回: [{id, date, viewType, label, title, whatIsIt, howTo, pitfalls, cases}]
    宁缺毋滥——没有够格（尤其"怎么做"讲不清架构）的返回空数组。
    """
    from datetime import datetime as _dt
    client = get_client()
    if not client or not candidates:
        return []

    lines = [
        f"{i}. [{c.get('source','')}] {c.get('title','')} | {c.get('summary','')[:120]}"
        for i, c in enumerate(candidates)
    ]

    prompt = f"""你在为一位非技术出身的 AI 产品经理提炼「最佳实践」。她想从真实案例里看懂：某个业务场景 / 某个新技术，在实际中是怎么落地的、架构怎么搭、有哪些坑。她尤其关注 2C（面向消费者/个人用户）的实践。

以下是最近 7 天采集的真实案例（来源 + 标题 + 摘要）：
{chr(10).join(lines)}

任务：从中提炼 1-3 条「最佳实践」。宁缺毋滥——没有够格的就返回空数组 []。

【硬门槛：任何一条不满足就丢弃】
1. 必须基于上面列表里的真实案例，不许编造；每条必须附来源链接（用列表里给出的来源）。
2. 「怎么做」必须能讲清架构链路——案例本身没披露技术怎么搭的，直接丢弃，不许脑补通用流程。
3. 优先 2C（面向消费者/个人用户）场景；2B 企业内部工程实践只在特别典型时才收。

【每条归类】
- viewType：这条是讲某个「场景」还是某个「技术」，二选一填 "场景" 或 "技术"。
- label：具体场景名（常见有 客服/办公/销售/数据分析/营销，也可自行归纳其他）或技术名（如 harness/loop/agent 等，自行归纳）。

【四段内容，中文，PM 水位，不堆术语】
- whatIsIt：{{scenario 什么场景, users 用户群是谁, painpoint 痛在哪}}
- howTo：{{architecture 架构链路——用"输入→环节→环节→输出"一条链说清、点明 AI 在哪一环及其边界; keyMoves 架构之外的关键做法与取舍 2-4 条，每条是具体可执行动作、不是"加强管理"这种空话}}
- pitfalls：别人踩过的坑
- cases：支撑这条的真实来源 [{{source, url}}]

严格按 JSON 返回，最多 {max_keep} 条，不要输出其他内容（idx 填对应候选序号）：
[{{"viewType":"场景","label":"客服","title":"...","whatIsIt":{{"scenario":"...","users":"...","painpoint":"..."}},"howTo":{{"architecture":"...","keyMoves":["...","..."]}},"pitfalls":"...","cases":[{{"source":"...","url":"..."}}],"idx":0}}]"""

    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=3000,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        results = _json.loads(text)

        today = _dt.now().strftime("%Y-%m-%d")
        items = []
        for r in results:
            cases = r.get("cases") or []
            # 兜底：来源缺失时用候选原始来源/链接补上
            if not cases:
                idx = r.get("idx")
                src = candidates[idx] if (idx is not None and 0 <= idx < len(candidates)) else {}
                if src.get("url"):
                    cases = [{"source": src.get("source", ""), "url": src.get("url", "")}]
            first_url = cases[0].get("url", "") if cases else ""
            iid = hashlib.md5((first_url or r.get("title", "")).encode("utf-8")).hexdigest()[:12]
            items.append({
                "id": iid,
                "date": today,
                "viewType": r.get("viewType", "场景"),
                "label": r.get("label", ""),
                "title": r.get("title", ""),
                "whatIsIt": r.get("whatIsIt", {}),
                "howTo": r.get("howTo", {}),
                "pitfalls": r.get("pitfalls", ""),
                "cases": cases,
            })
        print(f"  最佳实践归纳：{len(candidates)} → {len(items)} 条")
        return items[:max_keep]
    except Exception as e:
        print(f"  [WARN] 最佳实践归纳失败: {e}")
        return []
