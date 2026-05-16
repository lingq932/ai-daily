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

    import json
    result = json.loads(text)
    item["title"] = result.get("title", title)
    item["summary"] = result.get("summary", summary)
    return item
