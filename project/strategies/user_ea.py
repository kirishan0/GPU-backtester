from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from ..engine.context import ReadOnlyCtx
from ..engine.execution import compute_lot_with_mode, apply_spread_policy


@dataclass
class EAInternalState:
    """EA内部で利用する状態管理クラス。"""
    buy_locked: bool = False
    sell_locked: bool = False
    loss_streak: int = 0


ea_state = EAInternalState()


def emit_actions(i_minute: int, ctx: ReadOnlyCtx) -> List[Dict]:
    """H1 と M15 の RSI を用いたエントリー判定と損切/利確ロジック。"""
    # エンジン側の連敗数を同期
    ea_state.loss_streak = ctx.state.loss_streak

    actions: List[Dict] = []

    # リセットフラグでロック解除
    if ctx.flags.get("reset"):
        ea_state.buy_locked = False
        ea_state.sell_locked = False

    lot = compute_lot_with_mode(
        ctx.state.balance,
        ctx.state.risk_pct,
        ctx.cfg.stoploss_points,
        ctx.cfg,
        loss_streak=ea_state.loss_streak,
    )

    rsi_m15 = ctx.rsi_m15[-1]
    rsi_h1 = ctx.rsi_h1[-1]

    price_buy = apply_spread_policy(ctx.bid, "BUY", ctx.cfg)
    price_sell = apply_spread_policy(ctx.ask, "SELL", ctx.cfg)

    sl_points = ctx.cfg.stoploss_points * ctx.point
    tp_points = ctx.cfg.stoploss_points * ctx.cfg.rr * ctx.point

    if (
        rsi_m15 <= ctx.cfg.oversold
        and rsi_h1 <= ctx.cfg.oversold
        and not ea_state.buy_locked
    ):
        sl = price_buy - sl_points
        action: Dict = {"type": "OPEN", "side": "BUY", "lot": lot, "sl": sl}
        if not ctx.cfg.enable_trailing_stop:
            action["tp"] = price_buy + tp_points
        actions.append(action)
        ea_state.buy_locked = True
    elif (
        rsi_m15 >= ctx.cfg.overbought
        and rsi_h1 >= ctx.cfg.overbought
        and not ea_state.sell_locked
    ):
        sl = price_sell + sl_points
        action = {"type": "OPEN", "side": "SELL", "lot": lot, "sl": sl}
        if not ctx.cfg.enable_trailing_stop:
            action["tp"] = price_sell - tp_points
        actions.append(action)
        ea_state.sell_locked = True
    else:
        actions.append({"type": "NOP"})

    return actions
