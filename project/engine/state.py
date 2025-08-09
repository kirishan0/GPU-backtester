from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class RunState:
    """取引状態を保持するクラス。"""

    position_side: str | None = None
    open_price: float | None = None
    sl: float | None = None
    tp: float | None = None
    loss_streak: int = 0
    buy_locked: bool = False
    sell_locked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """辞書へ変換する。"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunState":
        """辞書から RunState を復元する。"""
        return cls(**data)


def init_states() -> RunState:
    """初期状態を生成する。"""
    return RunState()
