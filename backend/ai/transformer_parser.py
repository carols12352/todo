from typing import Dict

from .transformer.infer import infer


def parse_nl_transformer(
    text: str,
    intent_dir: str = "backend/ai/models/intent",
    slots_dir: str = "backend/ai/models/slots",
) -> Dict:
    return infer(text, intent_dir, slots_dir)
