# Transformer Pipeline

This pipeline uses a transformer for:
- intent classification (`action`)
- slot tagging (BIO tagging for category/priority/date/id/title)

## Dataset Format (JSONL)
Each line is a JSON object:
```json
{
  "text": "新增 任务 12 明天 工作 高",
  "action": "add",
  "slots": [
    {"start": 3, "end": 5, "label": "ID"},
    {"start": 6, "end": 8, "label": "DATE"},
    {"start": 9, "end": 11, "label": "CATEGORY"},
    {"start": 12, "end": 13, "label": "PRIORITY"},
    {"start": 0, "end": 2, "label": "TITLE"}
  ]
}
```

Slot labels:
`ID`, `DATE`, `CATEGORY`, `PRIORITY`, `TITLE`

Offsets are **character indices** in the original text.

## Train Intent
```bash
python -m backend.ai.transformer.train_intent \
  --data backend/ai/data/transformer/train_bilingual.jsonl \
  --model bert-base-multilingual-cased \
  --output-dir backend/ai/models/intent
```

## Train Slots
```bash
python -m backend.ai.transformer.train_slots \
  --data backend/ai/data/transformer/train_bilingual.jsonl \
  --model bert-base-multilingual-cased \
  --output-dir backend/ai/models/slots
```

## Inference
```bash
python -m backend.ai.transformer.infer --text "添加 任务 12 明天 工作 高"
```

## Generate Bilingual Dataset
```bash
python backend/ai/transformer/gen_bilingual.py \
  --output backend/ai/data/transformer/train_bilingual.jsonl \
  --count 2000
```
