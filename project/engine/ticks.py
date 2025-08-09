from __future__ import annotations

from typing import Iterator, Tuple

import pandas as pd

from .enums import OHLCOrder


def ohlc_to_4ticks(open_: float, high: float, low: float, close: float, order: OHLCOrder) -> Tuple[float, float, float, float]:
    """OHLCを4ティックへ展開する。"""
    if order == OHLCOrder.O_H_L_C:
        return open_, high, low, close
    return open_, low, high, close


def iter_minute_segments(df: pd.DataFrame, order: OHLCOrder) -> Iterator[Tuple[pd.Timestamp, float, float, float, float]]:
    """DataFrameから1分足セグメントを順次返す。"""
    for ts, row in df.iterrows():
        yield ts, *ohlc_to_4ticks(row["open"], row["high"], row["low"], row["close"], order)
