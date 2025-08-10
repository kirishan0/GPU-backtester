from __future__ import annotations

from .config import Config
from .enums import SpreadPolicy, MoneyMode


def value_per_point(cfg: Config) -> float:
    """ポイント当たりの価値を計算する。"""
    return cfg.tick_value / cfg.tick_size


def normalize_lot(lot: float, cfg: Config) -> float:
    """ロットサイズを規定の刻みに正規化する。"""
    step = 0.01 if cfg.ft6_mode else cfg.lot_step
    stepped = round(lot / step) * step
    return min(cfg.max_lot, max(cfg.min_lot, stepped))


def compute_lot(balance: float, risk_ratio: float, sl_points: float, cfg: Config) -> float:
    """リスク比率に基づきロットを計算する。"""
    vpp = value_per_point(cfg)
    raw = balance * risk_ratio / (sl_points * vpp)
    return normalize_lot(raw, cfg)


def apply_spread_policy(price: float, side: str, cfg: Config) -> float:
    """スプレッドポリシーを適用した価格を返す。"""
    if cfg.spread_policy == SpreadPolicy.NONE or cfg.spread_policy == SpreadPolicy.SL_ONLY:
        return price
    spread = cfg.fixed_spread_point * cfg.point
    return price + spread if side == "BUY" else price - spread


def commission_for_trade(lot: float, cfg: Config) -> float:
    """取引手数料を計算する。"""
    return lot * cfg.commission_per_lot_round


def swap_for_day(lot: float, days: int, is_long: bool, cfg: Config) -> float:
    """スワップポイントを計算する。"""
    rate = cfg.swap_long_per_lot_day if is_long else cfg.swap_short_per_lot_day
    return lot * days * rate


def compute_lot_money(loss_streak: int, cfg: Config) -> float:
    """マネーモードに従いロットを計算する。"""
    if cfg.money_mode is MoneyMode.GEOMETRIC:
        raw = cfg.min_lot * (1 + cfg.risk_ratio) ** loss_streak
    elif cfg.money_mode is MoneyMode.ARITHMETIC:
        raw = cfg.min_lot + cfg.lot_step * loss_streak
    else:
        raw = cfg.min_lot
    return normalize_lot(raw, cfg)
