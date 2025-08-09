from __future__ import annotations

from typing import List, Dict

from ..engine.context import ReadOnlyCtx


def emit_actions(i_minute: int, ctx: ReadOnlyCtx) -> List[Dict]:
    """RSIを利用したシンプルなEA例。"""
    rsi = ctx.rsi[-1]
    actions: List[Dict] = []
    if rsi <= ctx.cfg.oversold and not ctx.state.buy_locked:
        actions.append({"type": "OPEN", "side": "BUY", "lot": ctx.cfg.min_lot})
    elif rsi >= ctx.cfg.overbought and not ctx.state.sell_locked:
        actions.append({"type": "OPEN", "side": "SELL", "lot": ctx.cfg.min_lot})
    else:
        actions.append({"type": "NOP"})
    return actions
