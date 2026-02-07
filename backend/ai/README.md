# AI Module

Transformer-based intent + slot parser for task commands (Chinese + English).

## Structure
- `backend/ai/transformer/`: intent + slot models, training, inference, dataset generation
- `backend/ai/transformer_parser.py`: main `parse_nl_transformer()` entry (thin wrapper around transformer inference)

## Transformer Pipeline

### 1. Generate Bilingual Dataset (Recommended)

```bash
python backend/ai/transformer/gen_bilingual.py \
  --output backend/ai/data/transformer/train_bilingual.jsonl \
  --count 20000
```

### 2. Train Intent Model

```bash
python -m backend.ai.transformer.train_intent \
  --data backend/ai/data/transformer/train_bilingual.jsonl \
  --model bert-base-multilingual-cased \
  --output-dir backend/ai/models/intent
```

### 3. Train Slot Model

```bash
python -m backend.ai.transformer.train_slots \
  --data backend/ai/data/transformer/train_bilingual.jsonl \
  --model bert-base-multilingual-cased \
  --output-dir backend/ai/models/slots
```

### 4. Inference CLI

```bash
python -m backend.ai.transformer.infer --text "添加 任务 12 明天 下午三点 玩游戏 工作 优先级高"
python -m backend.ai.transformer.infer --text "go eat dinner tomorrow at 8:30 with a high priority"
```

To avoid re-loading model weights between requests, keep a single Python process alive:

```bash
python -m backend.ai.transformer.infer --interactive
```

### 5. Programmatic Usage

```python
from backend.ai import parse_nl_transformer

result = parse_nl_transformer("添加 任务 12 明天 下午三点 玩游戏 工作 优先级高")
print(result)
```

## Output Schema Notes

Inference returns a dict containing `action`, `task_patch`, and `confidence`.

`task_patch` date/time fields:
- `task_patch.due_date`: parsed date (YYYY-MM-DD) when `DATE` is present.
- `task_patch.due_time`: parsed time (HH:MM) when `TIME` is present.
- `task_patch.all_day`: `true` when `ALLDAY` is present, `false` when `TIME` is present, otherwise `null`.

## Dataset Format (JSONL)

Each line is a JSON object:

```json
{
  "text": "添加 任务 12 明天 下午三点 玩游戏 工作 优先级高",
  "action": "add",
  "slots": [
    {"start": 6, "end": 8, "label": "ID"},
    {"start": 9, "end": 11, "label": "DATE"},
    {"start": 12, "end": 16, "label": "TIME"},
    {"start": 17, "end": 20, "label": "TITLE"},
    {"start": 21, "end": 23, "label": "CATEGORY"},
    {"start": 24, "end": 28, "label": "PRIORITY"}
  ]
}
```

Slot labels:
- `ID`
- `DATE`
- `TIME`
- `ALLDAY`
- `CATEGORY`
- `PRIORITY`
- `TITLE`

Offsets are character indices in the original `text` (0-based, `end` is exclusive).

## Notes
- If you view `.jsonl` in PowerShell and see garbled Chinese, try: `Get-Content -Encoding utf8 path/to/file.jsonl`.
- You may see Hugging Face warnings about `UNEXPECTED/MISSING` params; this can happen when initializing new heads.
