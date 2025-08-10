from project.engine.config import Config
from project.engine.enums import OHLCOrder, SpreadPolicy, MoneyMode
from project.engine.execution import (
    value_per_point,
    normalize_lot,
    compute_lot,
    compute_lot_money,
)


def _cfg() -> Config:
    return Config(
        symbol="USDJPY",
        timezone="UTC",
        dst=False,
        spread_policy=SpreadPolicy.NONE,
        fixed_spread_point=0,
        commission_per_lot_round=0.0,
        swap_long_per_lot_day=0.0,
        swap_short_per_lot_day=0.0,
        ohlc_order=OHLCOrder.O_H_L_C,
        point=0.01,
        tick_size=0.01,
        tick_value=1.0,
        min_lot=0.1,
        lot_step=0.1,
        max_lot=1.0,
        enable_trailing_stop=False,
        trailing_start_ratio=0.5,
        trailing_width_points=10,
        stoploss_points=10,
        rr=2.0,
        money_mode=MoneyMode.FIXED,
        risk_ratio=0.01,
        rsi_period=14,
        reset_level=50,
        overbought=70,
        oversold=30,
        loss_streak_max=3,
        ft6_mode=False,
        save_chart_flags=False,
        batch_size=1,
        chunk_years=1,
        gpu_debug_mode=False,
        gpu_debug_runs=1,
        gpu_debug_seed="seed",
    )


def test_value_per_point():
    cfg = _cfg()
    assert value_per_point(cfg) == 100.0


def test_normalize_lot():
    cfg = _cfg()
    assert normalize_lot(0.23, cfg) == 0.2
    assert normalize_lot(2.0, cfg) == 1.0


def test_compute_lot():
    cfg = _cfg()
    lot = compute_lot(1000, 0.01, 10, cfg)
    assert lot >= cfg.min_lot


def test_compute_lot_money():
    cfg = _cfg()
    lot = compute_lot_money(0, cfg)
    assert lot == cfg.min_lot
