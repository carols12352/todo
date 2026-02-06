import argparse
import json
import os
import sys
from typing import Dict, List

if __package__ in (None, ""):
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(repo_root)

from transformers import AutoModelForTokenClassification, AutoTokenizer, Trainer, TrainingArguments

from backend.ai.transformer.data import (
    build_char_labels,
    load_jsonl,
    slot_label_to_id,
    validate_record,
)
from backend.ai.transformer.labels import SLOT_LABELS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train slot tagger.")
    p.add_argument("--data", required=True, help="Path to JSONL dataset.")
    p.add_argument("--model", default="bert-base-chinese", help="Base model name.")
    p.add_argument("--output-dir", default="backend/ai/models/slots", help="Output dir.")
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--max-length", type=int, default=128)
    return p


def align_labels(text: str, offsets, char_labels: List[str], label2id: Dict[str, int]):
    labels = []
    for start, end in offsets:
        if start == end:
            labels.append(-100)
            continue
        # Use the label of the first char in the token span.
        tag = char_labels[start] if start < len(char_labels) else "O"
        labels.append(label2id.get(tag, label2id["O"]))
    return labels


def main(argv: List[str]) -> int:
    args = build_parser().parse_args(argv)
    records = load_jsonl(args.data)
    for r in records:
        ok, msg = validate_record(r)
        if not ok:
            raise ValueError(f"invalid record: {msg} -> {r}")

    label2id = slot_label_to_id()
    id2label = {i: l for l, i in label2id.items()}

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)

    texts = [r["text"] for r in records]
    slots = [r.get("slots", []) for r in records]
    enc = tokenizer(texts, truncation=True, padding=True, max_length=args.max_length, return_offsets_mapping=True)

    all_labels = []
    for i, text in enumerate(texts):
        char_labels = build_char_labels(text, slots[i])
        offsets = enc["offset_mapping"][i]
        all_labels.append(align_labels(text, offsets, char_labels, label2id))

    dataset = SlotDataset(enc, all_labels)

    model = AutoModelForTokenClassification.from_pretrained(
        args.model, num_labels=len(SLOT_LABELS), id2label=id2label, label2id=label2id
    )

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.lr,
        logging_steps=50,
        save_steps=500,
    )

    trainer = Trainer(model=model, args=training_args, train_dataset=dataset)
    trainer.train()

    os.makedirs(args.output_dir, exist_ok=True)
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    with open(os.path.join(args.output_dir, "label_map.json"), "w", encoding="utf-8") as f:
        json.dump({"label2id": label2id, "id2label": id2label}, f, ensure_ascii=False, indent=2)
    return 0


class SlotDataset:
    def __init__(self, encodings: Dict, labels: List[List[int]]):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = self.labels[idx]
        item.pop("offset_mapping", None)
        return item


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
