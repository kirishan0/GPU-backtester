from __future__ import annotations

from typing import List, Dict

from ..engine.context import ReadOnlyCtx
from ..engine.execution import compute_lot_with_mode


def emit_actions(i_minute: int, ctx: ReadOnlyCtx) -> List[Dict]:
    """RSIを利用したシンプルなEA例。"""
    rsi = ctx.rsi[-1]
    actions: List[Dict] = []
    lot = compute_lot_with_mode(ctx.state.balance, ctx.state.risk_pct, ctx.cfg.stoploss_points, ctx.cfg)
    if rsi <= ctx.cfg.oversold and not ctx.state.buy_locked:
        actions.append({"type": "OPEN", "side": "BUY", "lot": lot})
    elif rsi >= ctx.cfg.overbought and not ctx.state.sell_locked:
        actions.append({"type": "OPEN", "side": "SELL", "lot": lot})
    else:
        actions.append({"type": "NOP"})
    return actions
