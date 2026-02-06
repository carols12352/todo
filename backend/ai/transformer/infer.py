import argparse
import json
import os
import sys
from typing import Dict, List

if __package__ in (None, ""):
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(repo_root)

import torch
from transformers import AutoModelForSequenceClassification, AutoModelForTokenClassification, AutoTokenizer

from backend.ai.transformer.utils import extract_due_date, extract_id
from backend.ai.transformer.data import id_to_slot_label
from backend.ai.transformer.labels import ACTION_LABELS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Infer ai_result using transformer models.")
    p.add_argument("--text", required=True, help="Input text.")
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


def spans_to_ai_result(text: str, action: str, slots: List[Dict], confidence: float) -> Dict:
    result = {
        "action": action,
        "target": {"id": None},
        "task_patch": {
            "description": None,
            "details": None,
            "completed": None,
            "due_date": None,
            "category": None,
            "priority": None,
            "color": None,
        },
        "confidence": float(confidence),
    }

    # Fill from slots
    for s in slots:
        if s["label"] == "ID":
            try:
                result["target"]["id"] = int("".join(ch for ch in s["text"] if ch.isdigit()))
            except ValueError:
                pass
        elif s["label"] == "DATE":
            d = extract_due_date(s["text"]) or extract_due_date(text)
            result["task_patch"]["due_date"] = d
        elif s["label"] == "CATEGORY":
            if any(k in s["text"] for k in ["工作", "上班", "公司", "work"]):
                result["task_patch"]["category"] = "work"
            elif any(k in s["text"] for k in ["学习", "复习", "看书", "study", "learning"]):
                result["task_patch"]["category"] = "study"
            elif any(k in s["text"] for k in ["个人", "生活", "私事", "personal", "life"]):
                result["task_patch"]["category"] = "personal"
        elif s["label"] == "PRIORITY":
            if any(k in s["text"] for k in ["优先级高", "紧急", "很急", "高", "high", "urgent"]):
                result["task_patch"]["priority"] = "high"
            elif any(k in s["text"] for k in ["优先级中", "一般", "中", "medium", "normal"]):
                result["task_patch"]["priority"] = "medium"
            elif any(k in s["text"] for k in ["优先级低", "不急", "低", "low", "not urgent"]):
                result["task_patch"]["priority"] = "low"
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
    intent_tokenizer = AutoTokenizer.from_pretrained(intent_dir)
    intent_model = AutoModelForSequenceClassification.from_pretrained(intent_dir)
    intent_inputs = intent_tokenizer(text, return_tensors="pt")
    intent_logits = intent_model(**intent_inputs).logits[0]
    intent_probs = softmax(intent_logits)
    intent_id = int(intent_probs.argmax().item())
    action = ACTION_LABELS[intent_id]
    confidence = float(intent_probs[intent_id].item())

    slot_tokenizer = AutoTokenizer.from_pretrained(slots_dir, use_fast=True)
    slot_model = AutoModelForTokenClassification.from_pretrained(slots_dir)
    slot_inputs = slot_tokenizer(text, return_tensors="pt", return_offsets_mapping=True)
    offsets = slot_inputs.pop("offset_mapping")[0].tolist()
    slot_logits = slot_model(**slot_inputs).logits[0]
    slot_preds = slot_logits.argmax(dim=-1).tolist()
    id2label = id_to_slot_label()
    slots = decode_slots(text, offsets, slot_preds, id2label)

    return spans_to_ai_result(text, action, slots, confidence)


def main(argv: List[str]) -> int:
    args = build_parser().parse_args(argv)
    result = infer(args.text, args.intent_dir, args.slots_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
