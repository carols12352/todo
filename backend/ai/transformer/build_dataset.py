import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

if __package__ in (None, ""):
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    sys.path.append(repo_root)


ACTION_VERBS = [
    "新增",
    "创建",
    "添加",
    "新建",
    "记下",
    "记一下",
    "帮我记",
    "加一条",
    "加个",
    "添一条",
    "修改",
    "更新",
    "改成",
    "改为",
    "调整",
    "改一下",
    "改下",
    "改改",
    "变更",
    "完成",
    "做完",
    "标记完成",
    "设为完成",
    "搞定",
    "完成一下",
    "重新打开",
    "撤销完成",
    "设为未完成",
    "改回未完成",
    "取消完成",
    "删除",
    "移除",
    "删掉",
    "去掉",
    "删除掉",
    "删了",
]

CATEGORY_WORDS = {
    "work": ["工作", "上班", "公司"],
    "study": ["学习", "复习", "看书"],
    "personal": ["个人", "生活", "私事"],
}

PRIORITY_WORDS = {
    "high": ["优先级高", "紧急", "很急", "高"],
    "medium": ["优先级中", "一般", "中"],
    "low": ["优先级低", "不急", "低"],
}

DATE_PATTERNS = [
    r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
    r"\b\d{4}年\d{1,2}月\d{1,2}日\b",
    r"\b\d{1,2}月\d{1,2}日\b",
    r"\b今天\b",
    r"\b明天\b",
    r"\b后天\b",
]


def load_json(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_first(text: str, keywords: List[str]) -> Optional[Tuple[int, int]]:
    for k in sorted(keywords, key=len, reverse=True):
        idx = text.find(k)
        if idx != -1:
            return idx, idx + len(k)
    return None


def find_all_dates(text: str) -> Optional[Tuple[int, int]]:
    for p in DATE_PATTERNS:
        m = re.search(p, text)
        if m:
            return m.start(), m.end()
    return None


def find_id(text: str) -> Optional[Tuple[int, int]]:
    m = re.search(r"(?:ID|id|任务)\\s*(\\d+)|#(\\d+)", text)
    if not m:
        return None
    if m.group(1):
        start = m.start(1)
        end = m.end(1)
    else:
        start = m.start(2)
        end = m.end(2)
    return start, end


def guess_title_span(text: str) -> Optional[Tuple[int, int]]:
    # Split by common separators and remove action prefix to find the core task phrase.
    parts = re.split(r"[，、,\\s]+", text.strip())
    parts = [p for p in parts if p]
    if not parts:
        return None
    # Remove action verb from first part if it starts with it.
    first = parts[0]
    for v in sorted(ACTION_VERBS, key=len, reverse=True):
        if first.startswith(v):
            first = first[len(v) :].strip()
            break
    if first:
        cand = first
    else:
        cand = parts[1] if len(parts) > 1 else None
    if not cand:
        return None
    idx = text.find(cand)
    if idx == -1:
        return None
    return idx, idx + len(cand)


def build_slots(text: str) -> List[Dict]:
    slots = []

    def add_slot(span, label):
        if not span:
            return
        start, end = span
        if start < 0 or end <= start:
            return
        slots.append({"start": start, "end": end, "label": label})

    add_slot(find_id(text), "ID")
    add_slot(find_all_dates(text), "DATE")

    for cat, words in CATEGORY_WORDS.items():
        span = find_first(text, words)
        if span:
            add_slot(span, "CATEGORY")
            break

    for pri, words in PRIORITY_WORDS.items():
        span = find_first(text, words)
        if span:
            add_slot(span, "PRIORITY")
            break

    add_slot(guess_title_span(text), "TITLE")

    # Deduplicate overlaps by keeping earliest and longest
    slots = sorted(slots, key=lambda s: (s["start"], -(s["end"] - s["start"])))
    dedup = []
    used = set()
    for s in slots:
        key = (s["start"], s["end"], s["label"])
        if key in used:
            continue
        used.add(key)
        dedup.append(s)
    return dedup


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Convert JSON dataset to transformer JSONL with slots.")
    ap.add_argument("--input", required=True, help="Path to JSON dataset (list).")
    ap.add_argument("--output", required=True, help="Path to output JSONL.")
    args = ap.parse_args(argv)

    rows = load_json(args.input)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for r in rows:
            text = r.get("text", "")
            action = r.get("action")
            if not text or not action:
                continue
            slots = build_slots(text)
            record = {"text": text, "action": action, "slots": slots}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
