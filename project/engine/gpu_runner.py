"""Host-side utilities for running GPU kernels."""
from __future__ import annotations

import numpy as np
from numba import cuda

from .gpu_kernels import k_simulate_runs_ohlc4


def simulate_gpu_batch(open_m1: np.ndarray, high_m1: np.ndarray,
                        low_m1: np.ndarray, close_m1: np.ndarray,
                        entry_side: np.ndarray, sl_points: np.ndarray,
                        tp_points: np.ndarray, point: float,
                        ohlc_order: int, spread_points: int,
                        spread_policy: int, n_minutes: int) -> dict[str, np.ndarray]:
    """Execute the GPU simulation for a batch of runs.

    Parameters are numpy arrays with dtypes:
    - open/high/low/close: float32 of shape (n_runs * n_minutes)
    - entry_side: int8 of same shape
    - sl_points, tp_points: int32 of shape (n_runs,)
    """
    if not cuda.is_available():
        raise RuntimeError("CUDA not available")

    for arr, dt in [(open_m1, np.float32), (high_m1, np.float32),
                    (low_m1, np.float32), (close_m1, np.float32)]:
        if arr.dtype != dt or arr.ndim != 1:
            raise ValueError("Price arrays must be 1D float32")
    if entry_side.dtype != np.int8:
        raise ValueError("entry_side must be int8")
    if sl_points.dtype != np.int32 or tp_points.dtype != np.int32:
        raise ValueError("sl_points and tp_points must be int32")

    n_runs = sl_points.shape[0]
    if tp_points.shape[0] != n_runs:
        raise ValueError("tp_points length mismatch")
    expected = n_runs * n_minutes
    if open_m1.shape[0] != expected or entry_side.shape[0] != expected:
        raise ValueError("price arrays length mismatch")

    d_open = cuda.to_device(open_m1)
    d_high = cuda.to_device(high_m1)
    d_low = cuda.to_device(low_m1)
    d_close = cuda.to_device(close_m1)
    d_side = cuda.to_device(entry_side)
    d_sl = cuda.to_device(sl_points)
    d_tp = cuda.to_device(tp_points)

    d_exit_reason = cuda.device_array(n_runs, dtype=np.int8)
    d_entry_price = cuda.device_array(n_runs, dtype=np.float32)
    d_exit_price = cuda.device_array(n_runs, dtype=np.float32)
    d_pnl = cuda.device_array(n_runs, dtype=np.float32)

    block = 128
    grid = (n_runs + block - 1) // block

    k_simulate_runs_ohlc4[grid, block](d_open, d_high, d_low, d_close,
                                       d_side, d_sl, d_tp,
                                       np.float32(point), np.int8(ohlc_order),
                                       np.int32(spread_points), np.int8(spread_policy),
                                       np.int32(n_minutes), np.int32(n_minutes), np.int32(n_runs),
                                       d_exit_reason, d_entry_price, d_exit_price, d_pnl)

    return {
        "exit_reason": d_exit_reason.copy_to_host(),
        "entry_price": d_entry_price.copy_to_host(),
        "exit_price": d_exit_price.copy_to_host(),
        "pnl_points": d_pnl.copy_to_host(),
    }
