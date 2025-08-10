from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, get_type_hints

import yaml

from .enums import OHLCOrder, SpreadPolicy
from .errors import ConfigError


@dataclass
class Config:
    """設定情報を保持するデータクラス。"""

    symbol: str
    timezone: str
    dst: bool
    data_path: str
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

        hints = get_type_hints(cls)
        values: dict[str, Any] = {}
        for f in fields(cls):
            if f.name not in data:
                raise ConfigError(f"missing field: {f.name}")
            val = data[f.name]
            typ = hints[f.name]

            if typ is SpreadPolicy:
                try:
                    values[f.name] = SpreadPolicy[val]
                except KeyError as exc:
                    raise ConfigError(f"invalid spread_policy: {val}") from exc
                continue

            if typ is OHLCOrder:
                try:
                    values[f.name] = OHLCOrder[val]
                except KeyError as exc:
                    raise ConfigError(f"invalid ohlc_order: {val}") from exc
                continue

            if typ in (int, float):
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    raise ConfigError(f"invalid type for {f.name}: {type(val).__name__}")

                if f.name in {
                    "point",
                    "tick_size",
                    "tick_value",
                    "min_lot",
                    "lot_step",
                    "max_lot",
                    "rr",
                    "rsi_period",
                    "batch_size",
                    "chunk_years",
                    "gpu_debug_runs",
                } and val <= 0:
                    raise ConfigError(f"{f.name} must be > 0")
                if f.name in {
                    "fixed_spread_point",
                    "commission_per_lot_round",
                    "trailing_start_ratio",
                    "trailing_width_points",
                    "stoploss_points",
                    "loss_streak_max",
                } and val < 0:
                    raise ConfigError(f"{f.name} must be >= 0")
                if f.name == "reset_level" and not 0 <= val <= 100:
                    raise ConfigError("reset_level must be between 0 and 100")
                if f.name in {"overbought", "oversold"} and not 0 <= val <= 100:
                    raise ConfigError(f"{f.name} must be between 0 and 100")

                values[f.name] = float(val) if typ is float else int(val)
                continue

            if typ is bool:
                if not isinstance(val, bool):
                    raise ConfigError(f"invalid type for {f.name}: {type(val).__name__}")
                values[f.name] = val
                continue

            if typ is str:
                if not isinstance(val, str):
                    raise ConfigError(f"invalid type for {f.name}: {type(val).__name__}")
                if f.name == "data_path" and not Path(val).exists():
                    raise ConfigError(f"data_path does not exist: {val}")
                values[f.name] = val
                continue

            values[f.name] = val

        if values["max_lot"] < values["min_lot"]:
            raise ConfigError("max_lot must be >= min_lot")
        if values["overbought"] <= values["oversold"]:
            raise ConfigError("overbought must be greater than oversold")

        return cls(**values)
