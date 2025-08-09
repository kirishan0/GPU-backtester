import pandas as pd

from project.engine.enums import OHLCOrder
from project.engine.ticks import ohlc_to_4ticks, iter_minute_segments


def test_ohlc_to_4ticks_order():
    ticks = ohlc_to_4ticks(1, 2, 0, 1.5, OHLCOrder.O_H_L_C)
    assert ticks == (1, 2, 0, 1.5)
    ticks2 = ohlc_to_4ticks(1, 2, 0, 1.5, OHLCOrder.O_L_H_C)
    assert ticks2 == (1, 0, 2, 1.5)


def test_iter_minute_segments():
    df = pd.DataFrame(
        {"open": [1], "high": [2], "low": [0], "close": [1.5]},
        index=pd.date_range("2024-01-01", periods=1, freq="T"),
    )
    segs = list(iter_minute_segments(df, OHLCOrder.O_H_L_C))
    assert len(segs) == 1
    ts, t0, t1, t2, t3 = segs[0]
    assert t0 == 1 and t1 == 2 and t2 == 0 and t3 == 1.5
