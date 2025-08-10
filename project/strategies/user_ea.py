from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..engine.context import ReadOnlyCtx
from ..engine.execution import compute_lot_money, apply_spread_policy


@dataclass
class EAState:
    """EA内部で管理する状態。"""

    loss_streak: int = 0
    buy_locked: bool = False
    sell_locked: bool = False


STATE = EAState()


def emit_actions(i_minute: int, ctx: ReadOnlyCtx) -> List[Dict]:
    """H1とM15のRSIを利用したエントリー判定と決済ロジック。"""

    # コンテキストから状態を同期
    STATE.loss_streak = ctx.state.loss_streak

    # リセットフラグでロック解除
    if ctx.flags.get("reset"):
        STATE.buy_locked = False
        STATE.sell_locked = False

    rsi_m15 = ctx.rsi_m15[-1]
    rsi_h1 = ctx.rsi_h1[-1]
    actions: List[Dict] = []
    side: str | None = None

    if (
        rsi_m15 <= ctx.cfg.oversold
        and rsi_h1 <= ctx.cfg.oversold
        and not STATE.buy_locked
    ):
        side = "BUY"
    elif (
        rsi_m15 >= ctx.cfg.overbought
        and rsi_h1 >= ctx.cfg.overbought
        and not STATE.sell_locked
    ):
        side = "SELL"

    if side:
        lot = compute_lot_money(STATE.loss_streak, ctx.cfg)
        price = ctx.ask if side == "BUY" else ctx.bid
        price = apply_spread_policy(price, side, ctx.cfg)
        sl_points = ctx.cfg.stoploss_points * ctx.cfg.point
        if side == "BUY":
            sl = price - sl_points
            tp = None if ctx.cfg.enable_trailing_stop else price + sl_points * ctx.cfg.rr
            STATE.buy_locked = True
        else:
            sl = price + sl_points
            tp = None if ctx.cfg.enable_trailing_stop else price - sl_points * ctx.cfg.rr
            STATE.sell_locked = True
        act = {"type": "OPEN", "side": side, "lot": lot, "sl": sl}
        if tp is not None:
            act["tp"] = tp
        actions.append(act)
    else:
        actions.append({"type": "NOP"})

    return actions
