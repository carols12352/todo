import argparse
import json
import os
import sys
from typing import Dict, List

if __package__ in (None, ""):
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(repo_root)

from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments

from backend.ai.transformer.data import load_jsonl, validate_record
from backend.ai.transformer.labels import ACTION_LABELS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train intent classifier.")
    p.add_argument("--data", required=True, help="Path to JSONL dataset.")
    p.add_argument("--model", default="bert-base-chinese", help="Base model name.")
    p.add_argument("--output-dir", default="backend/ai/models/intent", help="Output dir.")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--max-length", type=int, default=128)
    return p


def main(argv: List[str]) -> int:
    args = build_parser().parse_args(argv)
    records = load_jsonl(args.data)
    for r in records:
        ok, msg = validate_record(r)
        if not ok:
            raise ValueError(f"invalid record: {msg} -> {r}")

    label2id = {l: i for i, l in enumerate(ACTION_LABELS)}
    id2label = {i: l for i, l in enumerate(ACTION_LABELS)}

    tokenizer = AutoTokenizer.from_pretrained(args.model)

    texts = [r["text"] for r in records]
    labels = [label2id[r["action"]] for r in records]

    enc = tokenizer(texts, truncation=True, padding=True, max_length=args.max_length)
    dataset = IntentDataset(enc, labels)

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, num_labels=len(ACTION_LABELS), id2label=id2label, label2id=label2id
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


class IntentDataset:
    def __init__(self, encodings: Dict, labels: List[int]):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
