import argparse
import json
import os
import sys
from functools import lru_cache
from typing import Dict, List, Tuple

if __package__ in (None, ""):
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(repo_root)

import torch
from transformers import AutoModelForSequenceClassification, AutoModelForTokenClassification, AutoTokenizer

from backend.ai.transformer.utils import extract_due_date, extract_id, extract_time
from backend.ai.transformer.labels import ACTION_LABELS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Infer ai_result using transformer models.")
    p.add_argument("--text", help="Input text.")
    p.add_argument(
        "--interactive",
        action="store_true",
        help="Read lines from stdin and run inference in a single process (avoids re-loading models).",
    )
    p.add_argument("--intent-dir", default="backend/ai/models/intent", help="Intent model dir.")
    p.add_argument("--slots-dir", default="backend/ai/models/slots", help="Slots model dir.")
    return p


def softmax(x):
    e = torch.exp(x - x.max())
    return e / e.sum()


def decode_slots(text: str, offsets, preds, id2label):
    spans = []
    current = None
    for (start, end), pid in zip(offsets, preds):
        if start == end:
            continue
        label = id2label.get(int(pid), "O")
        if label == "O":
            if current:
                spans.append(current)
                current = None
            continue
        prefix, tag = label.split("-", 1)
        if prefix == "B" or (current and current["label"] != tag):
            if current:
                spans.append(current)
            current = {"label": tag, "start": start, "end": end}
        else:
            if current:
                current["end"] = end
    if current:
        spans.append(current)
    for s in spans:
        s["text"] = text[s["start"] : s["end"]]
    return spans


_CATEGORY_KEYWORDS = {
    "work": ["work", "office", "company", "工作", "上班", "公司"],
    "study": ["study", "learning", "homework", "学习", "复习", "看书", "作业"],
    "personal": ["personal", "life", "个人", "生活", "私事"],
}

_PRIORITY_KEYWORDS = {
    "high": ["high", "high priority", "urgent", "优先级高", "紧急", "很急", "高优先级"],
    "medium": ["medium", "medium priority", "normal", "优先级中", "一般", "普通", "中优先级"],
    "low": ["low", "low priority", "not urgent", "优先级低", "不急", "低优先级"],
}


def _map_by_keywords(text: str, table) -> str | None:
    if not text:
        return None
    lower = text.lower()
    for canon, keys in table.items():
        for k in keys:
            if k.lower() in lower:
                return canon
    return None


@lru_cache(maxsize=8)
def _load_intent(intent_dir: str):
    tok = AutoTokenizer.from_pretrained(intent_dir)
    model = AutoModelForSequenceClassification.from_pretrained(intent_dir)
    model.eval()
    return tok, model


@lru_cache(maxsize=8)
def _load_slots(slots_dir: str):
    tok = AutoTokenizer.from_pretrained(slots_dir, use_fast=True)
    model = AutoModelForTokenClassification.from_pretrained(slots_dir)
    model.eval()
    id2label = getattr(model.config, "id2label", None) or {}
    return tok, model, id2label


def spans_to_ai_result(text: str, action: str, slots: List[Dict], confidence: float) -> Dict:
    result = {
        "action": action,
        "target": {"id": None},
        "task_patch": {
            "description": None,
            "details": None,
            "completed": None,
            "due_date": None,
            "due_time": None,
            "all_day": None,
            "category": None,
            "priority": None,
            "color": None,
        },
        "confidence": float(confidence),
    }

    for s in slots:
        if s["label"] == "ID":
            try:
                result["target"]["id"] = int("".join(ch for ch in s["text"] if ch.isdigit()))
            except ValueError:
                pass
        elif s["label"] == "DATE":
            result["task_patch"]["due_date"] = extract_due_date(s["text"])
        elif s["label"] == "TIME":
            t = extract_time(s["text"])
            if t:
                result["task_patch"]["due_time"] = t
                result["task_patch"]["all_day"] = False
        elif s["label"] == "ALLDAY":
            result["task_patch"]["all_day"] = True
            result["task_patch"]["due_time"] = None
        elif s["label"] == "CATEGORY":
            result["task_patch"]["category"] = _map_by_keywords(s["text"], _CATEGORY_KEYWORDS)
        elif s["label"] == "PRIORITY":
            result["task_patch"]["priority"] = _map_by_keywords(s["text"], _PRIORITY_KEYWORDS)
        elif s["label"] == "TITLE":
            result["task_patch"]["description"] = s["text"]

    if action == "done":
        result["task_patch"]["completed"] = True
    elif action == "reopen":
        result["task_patch"]["completed"] = False

    if action == "add" and not result["task_patch"]["description"]:
        result["task_patch"]["description"] = text

    if result["target"]["id"] is None:
        result["target"]["id"] = extract_id(text)

    return result


def infer(text: str, intent_dir: str, slots_dir: str) -> Dict:
    intent_tokenizer, intent_model = _load_intent(intent_dir)
    with torch.inference_mode():
        intent_inputs = intent_tokenizer(text, return_tensors="pt")
        intent_logits = intent_model(**intent_inputs).logits[0]
        intent_probs = softmax(intent_logits)
        intent_id = int(intent_probs.argmax().item())
        action = ACTION_LABELS[intent_id]
        confidence = float(intent_probs[intent_id].item())

    slot_tokenizer, slot_model, id2label = _load_slots(slots_dir)
    with torch.inference_mode():
        slot_inputs = slot_tokenizer(text, return_tensors="pt", return_offsets_mapping=True)
        offsets = slot_inputs.pop("offset_mapping")[0].tolist()
        slot_logits = slot_model(**slot_inputs).logits[0]
        slot_preds = slot_logits.argmax(dim=-1).tolist()

    slots = decode_slots(text, offsets, slot_preds, id2label)
    return spans_to_ai_result(text, action, slots, confidence)


def clear_model_cache() -> None:
    _load_intent.cache_clear()
    _load_slots.cache_clear()


def main(argv: List[str]) -> int:
    args = build_parser().parse_args(argv)
    if args.interactive:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            text = line.strip()
            if not text:
                continue
            result = infer(text, args.intent_dir, args.slots_dir)
            print(json.dumps(result, ensure_ascii=False))
        return 0

    if not args.text:
        raise SystemExit("error: --text is required unless --interactive is set")

    result = infer(args.text, args.intent_dir, args.slots_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
