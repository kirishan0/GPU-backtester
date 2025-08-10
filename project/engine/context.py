from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .config import Config
from .state import RunState


@dataclass(frozen=True)
class StateView:
    """EAに提供するステートのビュー。"""

    position_side: str | None
    open_price: float | None
    sl: float | None
    tp: float | None
    loss_streak: int
    buy_locked: bool
    sell_locked: bool
    cfg: Config

    def point(self) -> float:
        """ポイントサイズを返す。"""
        return self.cfg.point


@dataclass(frozen=True)
class ReadOnlyCtx:
    """EAに渡す読み取り専用コンテキスト。"""

    bid: float
    ask: float
    point: float
    rsi_m15: Sequence[float]
    rsi_h1: Sequence[float]
    flags: dict[str, bool]
    state: StateView
    cfg: Config
