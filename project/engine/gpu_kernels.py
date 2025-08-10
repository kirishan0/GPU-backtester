"""GPU kernels for trade simulation using Numba CUDA."""
from numba import cuda


@cuda.jit(device=True)
def seg_hit_order(side: int, p0: float, p1: float):
    """Return priority order for TP/SL when price moves p0->p1.

    Parameters
    ----------
    side : int
        +1 for BUY, -1 for SELL.
    p0, p1 : float
        Start and end prices of segment.

    Returns
    -------
    int, int
        (first, second) hit order: 1=TP, -1=SL, 0=None.
    """
    if p1 > p0:
        if side > 0:
            return 1, -1
        else:
            return -1, 1
    elif p1 < p0:
        if side > 0:
            return -1, 1
        else:
            return 1, -1
    else:
        return 0, 0


@cuda.jit(device=True)
def resolve_hit_in_bar(side: int, sl: float, tp: float,
                       bid0: float, bid1: float, bid2: float, bid3: float,
                       ask0: float, ask1: float, ask2: float, ask3: float) -> int:
    """Determine SL/TP hit within a bar of 4 ticks.

    Parameters
    ----------
    side : int
        +1=BUY, -1=SELL.
    sl, tp : float
        Stop-loss and take-profit prices.
    bid0..bid3, ask0..ask3 : float
        Tick prices for bid and ask.

    Returns
    -------
    int
        1 for TP, -1 for SL, 0 if none hit.
    """
    if side > 0:
        t0, t1, t2, t3 = bid0, bid1, bid2, bid3
    else:
        t0, t1, t2, t3 = ask0, ask1, ask2, ask3

    for i in range(3):
        if i == 0:
            p0 = t0; p1 = t1
        elif i == 1:
            p0 = t1; p1 = t2
        else:
            p0 = t2; p1 = t3
        hit_tp = (p0 <= tp <= p1) or (p1 <= tp <= p0)
        hit_sl = (p0 <= sl <= p1) or (p1 <= sl <= p0)
        if hit_tp and hit_sl:
            return -1
        first, second = seg_hit_order(side, p0, p1)
        if first == 1 and hit_tp:
            return 1
        if first == -1 and hit_sl:
            return -1
        if second == 1 and hit_tp:
            return 1
        if second == -1 and hit_sl:
            return -1
    return 0


@cuda.jit
def k_simulate_runs_ohlc4(open_m1, high_m1, low_m1, close_m1,
                          entry_side, sl_points, tp_points,
                          point, ohlc_order, spread_points, spread_policy,
                          max_minutes, n_minutes, n_runs,
                          exit_reason, entry_price, exit_price, pnl_points):
    """Simulate multiple runs with OHLC4 ticks.

    Each thread handles one run.
    """
    idx = cuda.grid(1)
    if idx >= n_runs:
        return

    base = idx * n_minutes
    spread = spread_points * point
    sl_p = sl_points[idx] * point
    tp_p = tp_points[idx] * point

    side = 0
    sl = 0.0
    tp = 0.0
    entry = 0.0
    reason = 0

    for t in range(max_minutes):
        i = base + t
        if side == 0:
            es = entry_side[i]
            if es != 0:
                side = es
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
            res = resolve_hit_in_bar(side, sl, tp, b0, b1, b2, b3, a0, a1, a2, a3)
            if res != 0:
                reason = res
                exit_reason[idx] = reason
                if reason == -1:
                    exit_price[idx] = sl
                else:
                    exit_price[idx] = tp
                pnl_points[idx] = (exit_price[idx] - entry) / point * side
                break
    if side != 0 and reason == 0:
        i = base + max_minutes - 1
        last = close_m1[i]
        if side > 0:
            exit_price[idx] = last
        else:
            exit_price[idx] = last + spread
        exit_reason[idx] = 0
        pnl_points[idx] = (exit_price[idx] - entry) / point * side
