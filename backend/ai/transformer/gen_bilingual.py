import argparse
import json
import os
import random
from typing import Dict, List, Optional, Tuple


def make_record(text: str, action: str, slots: List[Dict]) -> Dict:
    return {"text": text, "action": action, "slots": slots}


def span(text: str, phrase: str) -> Optional[Dict]:
    idx = text.find(phrase)
    if idx == -1:
        return None
    return {"start": idx, "end": idx + len(phrase)}


def _choose_sep() -> str:
    return random.choice([" ", "，", "。", "；", " | ", " - ", ""])


def _join_parts(parts: List[str]) -> str:
    parts = [p for p in parts if p]
    if not parts:
        return ""

    sep = _choose_sep()
    if sep == "":
        sep = " "

    if sep in (" | ", " - "):
        return sep.join(parts)

    if sep in ("，", "。", "；"):
        return sep.join(parts)

    return sep.join(parts)


def _maybe(prob: float) -> bool:
    return random.random() < prob


def _build_slots(text: str, items: List[Tuple[str, str]]) -> List[Dict]:
    slots: List[Dict] = []
    for label, token in items:
        if not token:
            continue
        s = span(text, token)
        if s:
            slots.append({**s, "label": label})
    return slots


def gen_zh() -> Dict:
    verbs = {
        "add": ["新增", "创建", "添加", "新建", "记一下", "帮我记", "麻烦帮我记", "请帮我加一个", "安排一下", "记个"],
        "update": ["修改", "更新", "改为", "改成", "调整", "帮我改", "把它改成"],
        "done": ["完成", "做完", "标记完成", "设为完成", "搞定", "完成一下"],
        "reopen": ["重新打开", "撤销完成", "设为未完成", "改回未完成", "取消完成"],
        "remove": ["删除", "移除", "删掉", "去掉", "干掉"],
    }

    titles = [
        "整理会议纪要",
        "准备周报",
        "提交代码",
        "完成作业",
        "复习数据结构",
        "阅读论文",
        "买菜",
        "打扫房间",
        "健身",
        "玩游戏",
        "吃晚饭",
        "看电影",
    ]

    cats = {
        "work": ["工作", "上班", "公司"],
        "study": ["学习", "复习", "看书"],
        "personal": ["个人", "生活", "私事"],
    }

    pris = {
        "high": ["优先级高", "紧急", "很急", "高优先级"],
        "medium": ["优先级中", "一般", "普通", "中优先级"],
        "low": ["优先级低", "不急", "低优先级"],
    }

    dates = ["今天", "明天", "后天", "大后天", "2026-08-12", "2026年8月12日", "8月12日"]
    times = ["下午三点", "下午3点", "上午十点半", "晚上8点15分", "8:30", "20:05"]
    allday_tokens = ["全天", "整天", "一整天"]

    action = random.choice(["add", "add", "add", "update", "done", "reopen", "remove"])
    title = random.choice(titles)

    cat_key = random.choice(list(cats.keys()))
    pri_key = random.choice(list(pris.keys()))

    include_date = _maybe(0.65)
    include_time = _maybe(0.45)
    include_allday = include_date and _maybe(0.20)

    date = random.choice(dates) if include_date else ""

    # If ALLDAY is present, don't include a specific time.
    if include_allday:
        allday = random.choice(allday_tokens)
        time = ""
    else:
        allday = ""
        time = random.choice(times) if include_time else ""

    cat_word = random.choice(cats[cat_key]) if _maybe(0.40) else ""
    pri_word = random.choice(pris[pri_key]) if _maybe(0.40) else ""

    task_id = str(random.randint(1, 500))
    id_phrase_variants = [f"任务 {task_id}", f"任务{task_id}", f"ID {task_id}", f"#{task_id}"]
    id_phrase = random.choice(id_phrase_variants)

    style = random.choice(["formal", "casual", "telegraph", "list"])

    parts: List[str] = []
    slot_items: List[Tuple[str, str]] = []

    if action == "add" and _maybe(0.55):
        parts.append("" if style != "formal" else "请帮我记录")
    else:
        parts.append(random.choice(verbs[action]))

    include_id = action != "add" or _maybe(0.20)
    if include_id:
        parts.append(id_phrase)
        slot_items.append(("ID", task_id))

    core = [title, cat_word, pri_word, date, allday, time]
    core = [c for c in core if c]

    if style == "formal":
        parts.append(title)
        if cat_word:
            parts.append(f"分类{cat_word}")
        if pri_word:
            parts.append(pri_word)
        if date:
            parts.append(date)
        if allday:
            parts.append(allday)
        if time:
            parts.append(time)

        slot_items.append(("TITLE", title))
        if cat_word:
            slot_items.append(("CATEGORY", cat_word))
        if pri_word:
            slot_items.append(("PRIORITY", pri_word))
        if date:
            slot_items.append(("DATE", date))
        if allday:
            slot_items.append(("ALLDAY", allday))
        if time:
            slot_items.append(("TIME", time))

    elif style == "telegraph":
        front = []
        if date:
            front.append(date)
            slot_items.append(("DATE", date))
        if allday:
            front.append(allday)
            slot_items.append(("ALLDAY", allday))
        if time:
            front.append(time)
            slot_items.append(("TIME", time))
        parts.extend(front)

        parts.append(title)
        slot_items.append(("TITLE", title))

        if cat_word:
            parts.append(cat_word)
            slot_items.append(("CATEGORY", cat_word))
        if pri_word:
            parts.append(pri_word)
            slot_items.append(("PRIORITY", pri_word))

    elif style == "list":
        random.shuffle(core)
        parts.extend(core)
        slot_items.append(("TITLE", title))
        if cat_word:
            slot_items.append(("CATEGORY", cat_word))
        if pri_word:
            slot_items.append(("PRIORITY", pri_word))
        if date:
            slot_items.append(("DATE", date))
        if allday:
            slot_items.append(("ALLDAY", allday))
        if time:
            slot_items.append(("TIME", time))

    else:
        parts.append(title)
        slot_items.append(("TITLE", title))
        rest = [cat_word, pri_word, date, allday, time]
        rest = [r for r in rest if r]
        random.shuffle(rest)
        parts.extend(rest)
        if cat_word:
            slot_items.append(("CATEGORY", cat_word))
        if pri_word:
            slot_items.append(("PRIORITY", pri_word))
        if date:
            slot_items.append(("DATE", date))
        if allday:
            slot_items.append(("ALLDAY", allday))
        if time:
            slot_items.append(("TIME", time))

    text = _join_parts(parts)
    slots = _build_slots(text, slot_items)

    return make_record(text, action, slots)


def gen_en() -> Dict:
    verbs = {
        "add": ["add", "create", "make", "note", "remind me to", "please add"],
        "update": ["update", "change", "edit", "modify", "please update"],
        "done": ["finish", "complete", "mark done"],
        "reopen": ["reopen", "undo done", "mark not done"],
        "remove": ["delete", "remove", "drop"],
    }

    titles = [
        "submit report",
        "write weekly summary",
        "fix bug",
        "study algorithms",
        "buy groceries",
        "go to gym",
        "play games",
        "eat dinner",
    ]

    cats = {"work": ["work", "office"], "study": ["study", "learning"], "personal": ["personal", "life"]}
    pris = {
        "high": ["high priority", "urgent"],
        "medium": ["medium priority", "normal"],
        "low": ["low priority", "not urgent"],
    }

    dates = ["today", "tomorrow", "day after tomorrow", "2026-08-12", "Aug 12 2026"]
    times = ["8:30", "20:05", "3:00 pm", "15:00"]
    allday_tokens = ["all day"]

    action = random.choice(["add", "add", "add", "update", "done", "reopen", "remove"])
    title = random.choice(titles)
    cat_key = random.choice(list(cats.keys()))
    pri_key = random.choice(list(pris.keys()))

    include_date = _maybe(0.65)
    include_time = _maybe(0.45)
    include_allday = include_date and _maybe(0.20)
    include_cat = _maybe(0.40)
    include_pri = _maybe(0.40)

    date = random.choice(dates) if include_date else ""

    if include_allday:
        allday = random.choice(allday_tokens)
        time = ""
    else:
        allday = ""
        time = random.choice(times) if include_time else ""

    cat_word = random.choice(cats[cat_key]) if include_cat else ""
    pri_word = random.choice(pris[pri_key]) if include_pri else ""

    task_id = str(random.randint(1, 500))
    id_phrase_variants = [f"task {task_id}", f"id {task_id}", f"#{task_id}"]
    id_phrase = random.choice(id_phrase_variants)

    parts: List[str] = []
    slot_items: List[Tuple[str, str]] = []

    if action == "add" and _maybe(0.55):
        parts.append(title)
    else:
        parts.append(random.choice(verbs[action]))
        parts.append(title)

    include_id = action != "add" or _maybe(0.20)
    if include_id:
        parts.append(id_phrase)
        slot_items.append(("ID", task_id))

    extras = []
    if cat_word:
        extras.append(cat_word)
        slot_items.append(("CATEGORY", cat_word))
    if pri_word:
        extras.append(pri_word)
        slot_items.append(("PRIORITY", pri_word))
    if date:
        extras.append(date)
        slot_items.append(("DATE", date))
    if allday:
        extras.append(allday)
        slot_items.append(("ALLDAY", allday))
    if time:
        if _maybe(0.5):
            extras.append(f"at {time}")
            slot_items.append(("TIME", time))
        else:
            extras.append(time)
            slot_items.append(("TIME", time))

    random.shuffle(extras)
    parts.extend(extras)

    text = " ".join([p for p in parts if p])

    slot_items.append(("TITLE", title))
    slots = _build_slots(text, slot_items)

    return make_record(text, action, slots)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate bilingual JSONL dataset.")
    ap.add_argument("--output", required=True, help="Output JSONL path.")
    ap.add_argument("--count", type=int, default=2000, help="Total records.")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        for _ in range(args.count):
            r = gen_zh() if random.random() < 0.5 else gen_en()
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
