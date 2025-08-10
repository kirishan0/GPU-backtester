from __future__ import annotations

from .config import Config
from .enums import SpreadPolicy, MoneyMode


def value_per_point(cfg: Config) -> float:
    """ポイント当たりの価値を計算する。"""
    return cfg.tick_value / cfg.tick_size


def normalize_lot(lot: float, cfg: Config) -> float:
    """ロットサイズを規定の刻みに正規化する。"""
    if cfg.ft6_mode:
        min_lot = 0.01
        lot_step = 0.01
    else:
        min_lot = cfg.min_lot
        lot_step = cfg.lot_step

    stepped = round(lot / lot_step) * lot_step
    return min(cfg.max_lot, max(min_lot, stepped))


def compute_lot(balance: float, risk_ratio: float, sl_points: float, cfg: Config) -> float:
    """リスク比率に基づきロットを計算する。"""
    vpp = value_per_point(cfg)
    raw = balance * risk_ratio / (sl_points * vpp)
    return normalize_lot(raw, cfg)


def _geometric_risk(risk_pct: float, loss_streak: int, cfg: Config) -> float:
    """幾何級数的にリスクを増減させる。"""
    return risk_pct * (1 + cfg.step_percent) ** loss_streak


def _arithmetic_risk(risk_pct: float, loss_streak: int, cfg: Config) -> float:
    """等差級数的にリスクを増減させる。"""
    return risk_pct + cfg.step_percent * loss_streak


def compute_lot_with_mode(
    balance: float,
    risk_pct: float,
    sl_points: float,
    cfg: Config,
    loss_streak: int = 0,
) -> float:
    """資金管理モードに応じてロットを計算する。"""
    if cfg.money_mode == MoneyMode.FIXED:
        return normalize_lot(cfg.fixed_lot, cfg)
    if cfg.money_mode == MoneyMode.GEOMETRIC:
        eff = _geometric_risk(risk_pct, loss_streak, cfg)
        return compute_lot(balance, eff, sl_points, cfg)
    if cfg.money_mode == MoneyMode.ARITHMETIC:
        eff = _arithmetic_risk(risk_pct, loss_streak, cfg)
        return compute_lot(balance, eff, sl_points, cfg)
    return compute_lot(balance, risk_pct, sl_points, cfg)


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
