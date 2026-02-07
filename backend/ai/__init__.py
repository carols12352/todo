"""
AI parsing helpers.

Keep this module light-weight: importing backend.ai should not eagerly import
transformer weights/deps (important for running submodules via `python -m`).
"""

from __future__ import annotations

from typing import Dict

__all__ = ["parse_nl_transformer", "warmup_transformer", "unload_transformer"]


def parse_nl_transformer(
    text: str,
    intent_dir: str = "backend/ai/models/intent",
    slots_dir: str = "backend/ai/models/slots",
) -> Dict:
    # Lazy import to avoid importing torch/transformers as a side effect of package import.
    from .transformer_parser import parse_nl_transformer as _parse

    return _parse(text, intent_dir=intent_dir, slots_dir=slots_dir)


def warmup_transformer(
    intent_dir: str = "backend/ai/models/intent",
    slots_dir: str = "backend/ai/models/slots",
) -> None:
    from .transformer_parser import warmup_models as _warm

    _warm(intent_dir=intent_dir, slots_dir=slots_dir)


def unload_transformer() -> None:
    from .transformer_parser import unload_models as _unload

    _unload()
