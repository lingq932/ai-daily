"""工程解码·最佳实践累积数据的读写。

best_practices.json 长期留存、不受 90 天清理。
核心是「追加 + 去重 + 排序」：每周把新归纳的条目并进来，
按 id（url/title 哈希）去重，按生成日期倒序（新在前）。
参照 learning_store.py 的写法保持一致。
"""
import os
import json
import hashlib
from datetime import datetime


def item_id(url, title=""):
    """去重键：优先用 url，退化到 title。"""
    key = (url or title or "").strip()
    return hashlib.md5(key.encode("utf-8")).hexdigest()[:12]


def load_bp(path):
    if not os.path.exists(path):
        return {"updatedAt": "", "items": []}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "items" not in data:
            return {"updatedAt": "", "items": []}
        return data
    except Exception as e:
        print(f"  [best_practices] 读取失败，按空处理: {e}")
        return {"updatedAt": "", "items": []}


def merge_bp(path, new_items, today=None):
    """把新条目并入 best_practices.json。

    - 按 id 去重（已存在则跳过，保留旧的生成日期）
    - 按 date 倒序排列
    返回 (实际新增数, 合并后总数)。
    """
    today = today or datetime.now().strftime("%Y-%m-%d")
    data = load_bp(path)
    existing = {it.get("id") for it in data["items"] if it.get("id")}

    added = 0
    for it in new_items:
        first_url = ""
        cases = it.get("cases") or []
        if cases:
            first_url = cases[0].get("url", "")
        iid = it.get("id") or item_id(first_url, it.get("title", ""))
        if iid in existing:
            continue
        it["id"] = iid
        it.setdefault("date", today)
        data["items"].append(it)
        existing.add(iid)
        added += 1

    data["items"].sort(key=lambda x: x.get("date", ""), reverse=True)
    data["updatedAt"] = today

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return added, len(data["items"])
