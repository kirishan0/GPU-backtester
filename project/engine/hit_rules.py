from __future__ import annotations

from typing import List


def hit_order_for_segment(side: str, going_up: bool) -> List[str]:
    """価格の進行方向に応じたヒット順序を返す。"""
    if side == "BUY":
        return ["TP", "SL"] if going_up else ["SL", "TP"]
    return ["SL", "TP"] if going_up else ["TP", "SL"]


def resolve_hit(side: str, high: float, low: float, sl: float, tp: float, going_up: bool) -> str:
    """ヒット結果を判定する。"""
    order = hit_order_for_segment(side, going_up)
    for event in order:
        if event == "TP":
            if (side == "BUY" and high >= tp) or (side == "SELL" and low <= tp):
                return "TP"
        else:  # SL
            if (side == "BUY" and low <= sl) or (side == "SELL" and high >= sl):
                return "SL"
    return ""
