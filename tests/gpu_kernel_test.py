import numpy as np
import pytest
from numba import cuda

from project.engine.gpu_runner import simulate_gpu_batch


def seg_hit_order_cpu(side: int, p0: float, p1: float):
    if p1 > p0:
        return (1, -1) if side > 0 else (-1, 1)
    if p1 < p0:
        return (-1, 1) if side > 0 else (1, -1)
    return (0, 0)


def resolve_hit_cpu(side: int, sl: float, tp: float, bid_ticks, ask_ticks) -> int:
    ticks = bid_ticks if side > 0 else ask_ticks
    for p0, p1 in zip(ticks[:-1], ticks[1:]):
        hit_tp = (p0 <= tp <= p1) or (p1 <= tp <= p0)
        hit_sl = (p0 <= sl <= p1) or (p1 <= sl <= p0)
        if hit_tp and hit_sl:
            return -1
        first, second = seg_hit_order_cpu(side, p0, p1)
        if first == 1 and hit_tp:
            return 1
        if first == -1 and hit_sl:
            return -1
        if second == 1 and hit_tp:
            return 1
        if second == -1 and hit_sl:
            return -1
    return 0


def simulate_cpu(open_m1, high_m1, low_m1, close_m1,
                 entry_side, sl_points, tp_points,
                 point, ohlc_order, spread_points,
                 spread_policy, n_minutes):
    n_runs = sl_points.shape[0]
    exit_reason = np.zeros(n_runs, np.int8)
    entry_price = np.zeros(n_runs, np.float32)
    exit_price = np.zeros(n_runs, np.float32)
    pnl_points = np.zeros(n_runs, np.float32)
    spread = spread_points * point
    for idx in range(n_runs):
        base = idx * n_minutes
        side = 0
        sl = tp = entry = 0.0
        reason = 0
        sl_p = sl_points[idx] * point
        tp_p = tp_points[idx] * point
        for t in range(n_minutes):
            i = base + t
            if side == 0:
                es = entry_side[i]
                if es != 0:
                    side = int(es)
                    op = open_m1[i]
                    if side > 0:
                        entry = op + spread
                        sl = entry - sl_p
                        tp = entry + tp_p
                        if spread_policy >= 1:
                            sl -= spread
                        if spread_policy == 2:
                            tp -= spread
                    else:
                        entry = op
                        sl = entry + sl_p
                        tp = entry - tp_p
                        if spread_policy >= 1:
                            sl += spread
                        if spread_policy == 2:
                            tp += spread
                    entry_price[idx] = entry
            if side != 0 and reason == 0:
                if ohlc_order == 0:
                    b0 = open_m1[i]; b1 = high_m1[i]; b2 = low_m1[i]; b3 = close_m1[i]
                else:
                    b0 = open_m1[i]; b1 = low_m1[i]; b2 = high_m1[i]; b3 = close_m1[i]
                a0 = b0 + spread; a1 = b1 + spread; a2 = b2 + spread; a3 = b3 + spread
                res = resolve_hit_cpu(side, sl, tp, [b0, b1, b2, b3], [a0, a1, a2, a3])
                if res != 0:
                    reason = res
                    exit_reason[idx] = reason
                    exit_price[idx] = sl if reason == -1 else tp
                    pnl_points[idx] = (exit_price[idx] - entry) / point * side
                    break
        if side != 0 and reason == 0:
            last = close_m1[base + n_minutes - 1]
            if side > 0:
                exit_price[idx] = last
            else:
                exit_price[idx] = last + spread
            pnl_points[idx] = (exit_price[idx] - entry) / point * side
    return {
        "exit_reason": exit_reason,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "pnl_points": pnl_points,
    }


pytest.importorskip("numba.cuda")
if not cuda.is_available():
    pytest.skip("CUDA not available", allow_module_level=True)


def test_buy_sell_tp_hit():
    n_runs = 2
    n_minutes = 4
    open_m1 = np.array([
        100, 100, 100, 100,
        100, 100, 100, 100
    ], dtype=np.float32)
    high_m1 = np.array([
        112, 100, 100, 100,
        101, 100, 100, 100
    ], dtype=np.float32)
    low_m1 = np.array([
        95, 100, 100, 100,
        85, 100, 100, 100
    ], dtype=np.float32)
    close_m1 = np.array([
        110, 100, 100, 100,
        90, 100, 100, 100
    ], dtype=np.float32)
    entry_side = np.array([1,0,0,0,-1,0,0,0], dtype=np.int8)
    sl_points = np.array([10,10], dtype=np.int32)
    tp_points = np.array([10,10], dtype=np.int32)
    point = 1.0
    ohlc_order = 0
    spread_points = 0
    spread_policy = 0

    cpu = simulate_cpu(open_m1, high_m1, low_m1, close_m1,
                       entry_side, sl_points, tp_points,
                       point, ohlc_order, spread_points,
                       spread_policy, n_minutes)
    gpu = simulate_gpu_batch(open_m1, high_m1, low_m1, close_m1,
                             entry_side, sl_points, tp_points,
                             point, ohlc_order, spread_points,
                             spread_policy, n_minutes)
    for key in cpu:
        np.testing.assert_allclose(cpu[key], gpu[key])


def test_sl_priority_same_tick():
    n_runs = 1
    n_minutes = 1
    open_m1 = np.array([100], dtype=np.float32)
    high_m1 = np.array([110], dtype=np.float32)
    low_m1 = np.array([90], dtype=np.float32)
    close_m1 = np.array([100], dtype=np.float32)
    entry_side = np.array([1], dtype=np.int8)
    sl_points = np.array([0], dtype=np.int32)
    tp_points = np.array([0], dtype=np.int32)
    point = 1.0
    ohlc_order = 0
    spread_points = 0
    spread_policy = 0

    cpu = simulate_cpu(open_m1, high_m1, low_m1, close_m1,
                       entry_side, sl_points, tp_points,
                       point, ohlc_order, spread_points,
                       spread_policy, n_minutes)
    gpu = simulate_gpu_batch(open_m1, high_m1, low_m1, close_m1,
                             entry_side, sl_points, tp_points,
                             point, ohlc_order, spread_points,
                             spread_policy, n_minutes)
    for key in cpu:
        np.testing.assert_allclose(cpu[key], gpu[key])
    assert cpu["exit_reason"][0] == -1


def test_spread_policies():
    n_runs = 1
    n_minutes = 1
    open_m1 = np.array([100.0], dtype=np.float32)
    high_m1 = np.array([100.11], dtype=np.float32)
    low_m1 = np.array([99.92], dtype=np.float32)
    close_m1 = np.array([100.0], dtype=np.float32)
    entry_side = np.array([1], dtype=np.int8)
    sl_points = np.array([10], dtype=np.int32)
    tp_points = np.array([10], dtype=np.int32)
    point = 0.01
    ohlc_order = 0
    spread_points = 3
    for policy, exp in [(0, -1), (1, 0), (2, 1)]:
        cpu = simulate_cpu(open_m1, high_m1, low_m1, close_m1,
                           entry_side, sl_points, tp_points,
                           point, ohlc_order, spread_points,
                           policy, n_minutes)
        gpu = simulate_gpu_batch(open_m1, high_m1, low_m1, close_m1,
                                 entry_side, sl_points, tp_points,
                                 point, ohlc_order, spread_points,
                                 policy, n_minutes)
        for key in cpu:
            np.testing.assert_allclose(cpu[key], gpu[key])
        assert cpu["exit_reason"][0] == exp
