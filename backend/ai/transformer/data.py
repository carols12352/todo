import json
from typing import Dict, Iterable, List, Tuple

from .labels import ACTION_LABELS, SLOT_ENTITY_LABELS, SLOT_LABELS


def load_jsonl(path: str) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def validate_record(rec: Dict) -> Tuple[bool, str]:
    if "text" not in rec:
        return False, "missing text"
    if "action" not in rec:
        return False, "missing action"
    if rec["action"] not in ACTION_LABELS:
        return False, f"invalid action: {rec['action']}"
    if "slots" in rec:
        slots = rec["slots"]
        if not isinstance(slots, list):
            return False, "slots must be list"
        for s in slots:
            if not all(k in s for k in ("start", "end", "label")):
                return False, "slot missing start/end/label"
            if s["label"] not in SLOT_ENTITY_LABELS:
                return False, f"invalid slot label: {s['label']}"
    return True, ""


def build_char_labels(text: str, slots: Iterable[Dict]) -> List[str]:
    labels = ["O"] * len(text)
    for s in slots:
        start, end, label = int(s["start"]), int(s["end"]), s["label"]
        if start < 0 or end > len(text) or start >= end:
            continue
        labels[start] = f"B-{label.split('-')[-1]}"
        for i in range(start + 1, end):
            labels[i] = f"I-{label.split('-')[-1]}"
    return labels


def slot_label_to_id() -> Dict[str, int]:
    return {l: i for i, l in enumerate(SLOT_LABELS)}


def id_to_slot_label() -> Dict[int, str]:
    return {i: l for i, l in enumerate(SLOT_LABELS)}
