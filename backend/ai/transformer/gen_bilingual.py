import argparse
import json
import os
import random
from typing import List, Dict


def make_record(text: str, action: str, slots: List[Dict]) -> Dict:
    return {"text": text, "action": action, "slots": slots}


def span(text: str, phrase: str):
    idx = text.find(phrase)
    if idx == -1:
        return None
    return {"start": idx, "end": idx + len(phrase)}


def gen_zh() -> Dict:
    actions = {
        "add": ["新增", "创建", "添加", "新建", "记一下", "帮我记"],
        "update": ["修改", "更新", "改为", "改成", "调整"],
        "done": ["完成", "做完", "标记完成", "设为完成"],
        "reopen": ["重新打开", "撤销完成", "设为未完成", "改回未完成"],
        "remove": ["删除", "移除", "删掉", "去掉"],
    }
    titles = ["整理会议纪要", "准备周报", "提交代码", "完成作业", "复习数据结构", "阅读论文", "买菜", "打扫房间", "健身"]
    cats = {"work": ["工作", "上班", "公司"], "study": ["学习", "复习", "看书"], "personal": ["个人", "生活", "私事"]}
    pris = {"high": ["高", "优先级高", "紧急"], "medium": ["中", "优先级中", "一般"], "low": ["低", "优先级低", "不急"]}
    dates = ["今天", "明天", "后天", "2026-08-12", "2026年8月12日", "8月12日"]

    action = random.choice(list(actions.keys()))
    verb = random.choice(actions[action])
    title = random.choice(titles)
    cat = random.choice(list(cats.keys()))
    pri = random.choice(list(pris.keys()))
    date = random.choice(dates)
    task_id = str(random.randint(1, 500))

    parts = [verb, f"任务 {task_id}", title, random.choice(cats[cat]), random.choice(pris[pri]), date]
    sep = random.choice(["，", " ", "、"])
    text = sep.join(parts)

    slots = []
    s = span(text, task_id)
    if s:
        slots.append({**s, "label": "ID"})
    s = span(text, date)
    if s:
        slots.append({**s, "label": "DATE"})
    s = span(text, title)
    if s:
        slots.append({**s, "label": "TITLE"})
    s = span(text, random.choice(cats[cat]))
    if s:
        slots.append({**s, "label": "CATEGORY"})
    s = span(text, random.choice(pris[pri]))
    if s:
        slots.append({**s, "label": "PRIORITY"})

    return make_record(text, action, slots)


def gen_en() -> Dict:
    actions = {
        "add": ["add", "create", "make", "note"],
        "update": ["update", "change", "edit", "modify"],
        "done": ["finish", "complete", "mark done"],
        "reopen": ["reopen", "undo done", "mark not done"],
        "remove": ["delete", "remove", "drop"],
    }
    titles = ["submit report", "write weekly summary", "fix bug", "study algorithms", "buy groceries", "go to gym"]
    cats = {"work": ["work"], "study": ["study", "learning"], "personal": ["personal", "life"]}
    pris = {"high": ["high", "urgent"], "medium": ["medium", "normal"], "low": ["low", "not urgent"]}
    dates = ["today", "tomorrow", "the day after tomorrow", "2026-08-12", "Aug 12 2026"]

    action = random.choice(list(actions.keys()))
    verb = random.choice(actions[action])
    title = random.choice(titles)
    cat = random.choice(list(cats.keys()))
    pri = random.choice(list(pris.keys()))
    date = random.choice(dates)
    task_id = str(random.randint(1, 500))

    text = f"{verb} task {task_id} {title} {random.choice(cats[cat])} {random.choice(pris[pri])} {date}"

    slots = []
    s = span(text, task_id)
    if s:
        slots.append({**s, "label": "ID"})
    s = span(text, date)
    if s:
        slots.append({**s, "label": "DATE"})
    s = span(text, title)
    if s:
        slots.append({**s, "label": "TITLE"})
    s = span(text, random.choice(cats[cat]))
    if s:
        slots.append({**s, "label": "CATEGORY"})
    s = span(text, random.choice(pris[pri]))
    if s:
        slots.append({**s, "label": "PRIORITY"})

    return make_record(text, action, slots)


def main():
    ap = argparse.ArgumentParser(description="Generate bilingual JSONL dataset.")
    ap.add_argument("--output", required=True, help="Output JSONL path.")
    ap.add_argument("--count", type=int, default=2000, help="Total records.")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    rows = []
    for _ in range(args.count):
        rows.append(gen_zh() if random.random() < 0.5 else gen_en())

    with open(args.output, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
