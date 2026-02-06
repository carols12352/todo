# AI Module

Transformer-based intent + slot parser for task commands. This module is internal-only
and not connected to `backend/cores` yet.

## Structure
- `transformer/`: intent + slot models, training, inference
- `transformer_parser.py`: main `parse_nl_transformer()` entry

## Transformer Pipeline (All Usage)

### 1. Generate Bilingual Dataset (Recommended)
```bash
python backend/ai/transformer/gen_bilingual.py \
  --output backend/ai/data/transformer/train_bilingual.jsonl \
  --count 2000
```

### 2. Convert Existing JSON to JSONL with Slots (Optional)
If you already have a JSON list dataset (e.g. legacy `train_2000.json`), convert it:
```bash
python backend/ai/transformer/build_dataset.py \
  --input backend/ai/data/train_2000.json \
  --output backend/ai/data/transformer/train_bilingual.jsonl
```

### 3. Train Intent Model
```bash
python -m backend.ai.transformer.train_intent \
  --data backend/ai/data/transformer/train_bilingual.jsonl \
  --model bert-base-multilingual-cased \
  --output-dir backend/ai/models/intent
```

### 4. Train Slot Model
```bash
python -m backend.ai.transformer.train_slots \
  --data backend/ai/data/transformer/train_bilingual.jsonl \
  --model bert-base-multilingual-cased \
  --output-dir backend/ai/models/slots
```

### 5. Inference CLI
```bash
python -m backend.ai.transformer.infer --text "添加 任务 12 明天 工作 高"
python -m backend.ai.transformer.infer --text "go eat dinner tomorrow at 8:30 high"
```

### 6. Programmatic Usage
```python
from backend.ai import parse_nl_transformer

result = parse_nl_transformer("添加 任务 12 明天 工作 高")
print(result)
```

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

Offsets are character indices in the original text.

## Notes
- You may see Hugging Face warnings about `UNEXPECTED/MISSING` params — this is normal when initializing new heads.
- For faster model downloads, set `HF_TOKEN`.
