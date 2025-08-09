from __future__ import annotations

import importlib
from typing import Any, Callable

from .errors import EAValidationError
from .logger import get_logger


def load_user_ea(module_path: str = "project.strategies.user_ea") -> Any:
    """ユーザーEAをロードする。"""
    logger = get_logger(__name__)
    try:
        mod = importlib.import_module(module_path)
    except Exception as exc:  # pragma: no cover - import error
        raise EAValidationError(str(exc)) from exc

    if hasattr(mod, "emit_actions"):
        func = getattr(mod, "emit_actions")
        if not callable(func):
            raise EAValidationError("emit_actions is not callable")
        logger.info("EA emit_actions loaded")
        return mod

    if hasattr(mod, "entry_signal"):

        def emit_actions(i_minute: int, ctx: Any) -> list[dict]:
            side = mod.entry_signal(i_minute, ctx)
            if side in {"BUY", "SELL"}:
                return [{"type": "OPEN", "side": side, "lot": ctx.cfg.min_lot}]
            return []

        mod.emit_actions = emit_actions  # type: ignore[attr-defined]
        logger.info("EA legacy API wrapped")
        return mod

    raise EAValidationError("no valid API found")
