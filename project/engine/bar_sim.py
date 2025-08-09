from __future__ import annotations

from typing import Tuple

from .config import Config
from .hit_rules import resolve_hit
from .state import RunState


def simulate_bar(
    state: RunState,
    side: str,
    bid_ticks: Tuple[float, float, float, float],
    ask_ticks: Tuple[float, float, float, float],
    cfg: Config,
    rr: float,
    trailing_enabled: bool,
    trailing_start_ratio: float,
    trailing_width_points: int,
    sl_points_eff: float,
) -> Tuple[RunState, bool, str]:
    """1バー内のシンプルなシミュレーションを行う。"""
    if state.position_side is None:
        open_price = bid_ticks[0] if side == "BUY" else ask_ticks[0]
        sl = open_price - sl_points_eff * cfg.point if side == "BUY" else open_price + sl_points_eff * cfg.point
        tp = open_price + rr * sl_points_eff * cfg.point if side == "BUY" else open_price - rr * sl_points_eff * cfg.point
        state.position_side = side
        state.open_price = open_price
        state.sl = sl
        state.tp = tp
        return state, False, ""

    # 既にポジションが存在する場合
    high = max(bid_ticks) if state.position_side == "BUY" else max(ask_ticks)
    low = min(bid_ticks) if state.position_side == "BUY" else min(ask_ticks)
    going_up = bid_ticks[0] < bid_ticks[-1] if state.position_side == "BUY" else ask_ticks[0] < ask_ticks[-1]
    result = resolve_hit(state.position_side, high, low, state.sl, state.tp, going_up)

    closed = False
    if result in {"TP", "SL"}:
        state.position_side = None
        state.open_price = None
        state.sl = None
        state.tp = None
        closed = True
    return state, closed, result
