from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any
import yaml

from .enums import OHLCOrder, SpreadPolicy
from .errors import ConfigError


@dataclass
class Config:
    """設定情報を保持するデータクラス。"""

    symbol: str
    timezone: str
    dst: bool
    spread_policy: SpreadPolicy
    fixed_spread_point: int
    commission_per_lot_round: float
    swap_long_per_lot_day: float
    swap_short_per_lot_day: float
    ohlc_order: OHLCOrder
    point: float
    tick_size: float
    tick_value: float
    min_lot: float
    lot_step: float
    max_lot: float
    enable_trailing_stop: bool
    trailing_start_ratio: float
    trailing_width_points: int
    stoploss_points: int
    rr: float
    rsi_period: int
    reset_level: float
    overbought: float
    oversold: float
    loss_streak_max: int
    ft6_mode: bool
    save_chart_flags: bool
    batch_size: int
    chunk_years: int
    gpu_debug_mode: bool
    gpu_debug_runs: int
    gpu_debug_seed: str

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        """YAML ファイルから Config を生成する。

        Args:
            path: 設定ファイルのパス。

        Raises:
            ConfigError: 必須項目が欠落または型が不正な場合。

        Returns:
            Config: 生成された設定インスタンス。
        """
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        except FileNotFoundError as exc:
            raise ConfigError(str(exc)) from exc

        values: dict[str, Any] = {}
        for f in fields(cls):
            if f.name not in data:
                raise ConfigError(f"missing field: {f.name}")
            val = data[f.name]
            if f.type is SpreadPolicy:
                try:
                    values[f.name] = SpreadPolicy[val]
                except KeyError as exc:
                    raise ConfigError(f"invalid spread_policy: {val}") from exc
            elif f.type is OHLCOrder:
                try:
                    values[f.name] = OHLCOrder[val]
                except KeyError as exc:
                    raise ConfigError(f"invalid ohlc_order: {val}") from exc
            else:
                values[f.name] = val
        return cls(**values)
