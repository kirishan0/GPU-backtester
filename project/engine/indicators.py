from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd

from .config import Config


def resample_ohlc_m(df: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """OHLCデータを指定分足へリサンプルする。"""
    ohlc_dict = {"open": "first", "high": "max", "low": "min", "close": "last"}
    return df.resample(f"{minutes}T", label="right", closed="right").agg(ohlc_dict).dropna()


def rsi_wilder(series: pd.Series, period: int) -> pd.Series:
    """Wilder方式のRSIを計算する。"""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_rsi_and_flags(df: pd.DataFrame, cfg: Config) -> Tuple[np.ndarray, pd.DataFrame]:
    """RSIと各種フラグを計算する。"""
    rsi = rsi_wilder(df["close"], cfg.rsi_period).to_numpy()
    flags = pd.DataFrame(
        {
            "overbought": rsi >= cfg.overbought,
            "oversold": rsi <= cfg.oversold,
            "reset": rsi >= cfg.reset_level,
        },
        index=df.index,
    )
    return rsi, flags
