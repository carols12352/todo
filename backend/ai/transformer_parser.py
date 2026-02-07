from typing import Dict

from .transformer.infer import infer, clear_model_cache, _load_intent, _load_slots


def parse_nl_transformer(
    text: str,
    intent_dir: str = "backend/ai/models/intent",
    slots_dir: str = "backend/ai/models/slots",
) -> Dict:
    return infer(text, intent_dir, slots_dir)


def warmup_models(
    intent_dir: str = "backend/ai/models/intent",
    slots_dir: str = "backend/ai/models/slots",
) -> None:
    _load_intent(intent_dir)
    _load_slots(slots_dir)


def unload_models() -> None:
    clear_model_cache()
