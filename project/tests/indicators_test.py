import pandas as pd

from project.engine.config import Config
from project.engine.enums import OHLCOrder, SpreadPolicy
from project.engine.indicators import compute_rsi_and_flags


def _cfg() -> Config:
    return Config(
        symbol="USDJPY",
        timezone="UTC",
        dst=False,
        data_path="data",
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


def test_compute_rsi_and_flags():
    cfg = _cfg()
    df = pd.DataFrame({"close": [1, 2, 3, 4, 5, 6]}, index=pd.date_range("2024", periods=6, freq="T"))
    rsi, flags = compute_rsi_and_flags(df, cfg)
    assert len(rsi) == 6
    assert flags.shape[0] == 6
