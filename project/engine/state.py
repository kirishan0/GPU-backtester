from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict

from .config import Config


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
    lot: float | None = None
    balance: float = 0.0
    risk_pct: float = 0.0
    cycle_profit: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """辞書へ変換する。"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunState":
        """辞書から RunState を復元する。"""
        return cls(**data)

    def update_after_trade(self, profit: float, cfg: Config) -> None:
        """取引終了後にリスク関連の状態を更新する。"""
        self.balance += profit
        if profit < 0:
            self.loss_streak += 1
            self.risk_pct = cfg.initial_risk_pct
            self.cycle_profit = 0.0
        else:
            self.loss_streak = 0
            self.cycle_profit += profit
            threshold = cfg.base_balance * cfg.step_percent
            if threshold > 0 and self.cycle_profit >= threshold:
                self.risk_pct += cfg.step_percent
                self.cycle_profit -= threshold


def init_states(cfg: Config | None = None) -> RunState:
    """初期状態を生成する。"""
    if cfg:
        return RunState(balance=cfg.base_balance, risk_pct=cfg.initial_risk_pct)
    return RunState()
