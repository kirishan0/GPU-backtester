from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from .actions import validate_actions
from .config import Config
from .context import ReadOnlyCtx, StateView
from .errors import SimulationError
from .indicators import compute_rsi_and_flags
from .logger import get_logger
from .state import init_states
from .ticks import iter_minute_segments
from .loader import load_user_ea
from .bar_sim import simulate_bar


def main() -> None:
    """CPUテスターのエントリポイント。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    cfg = Config.from_yaml(args.config)
    logger = get_logger(__name__, args.run_id, args.log_level)

    try:
        ea = load_user_ea()
        # サンプルデータ生成（決定論的）
        data = pd.DataFrame(
            {
                "open": np.linspace(150.0, 150.9, 10),
                "high": np.linspace(150.2, 151.1, 10),
                "low": np.linspace(149.8, 150.7, 10),
                "close": np.linspace(150.1, 151.0, 10),
            },
            index=pd.date_range("2024-01-01", periods=10, freq="T"),
        )
        rsi, flags = compute_rsi_and_flags(data, cfg)
        state = init_states()
        history: List[dict] = []
        for i, (ts, *ticks) in enumerate(iter_minute_segments(data, cfg.ohlc_order)):
            view = StateView(
                position_side=state.position_side,
                open_price=state.open_price,
                sl=state.sl,
                tp=state.tp,
                loss_streak=state.loss_streak,
                buy_locked=state.buy_locked,
                sell_locked=state.sell_locked,
                cfg=cfg,
            )
            ctx = ReadOnlyCtx(
                bid=ticks[0],
                ask=ticks[0] + cfg.fixed_spread_point * cfg.point,
                point=cfg.point,
                rsi=rsi[: i + 1],
                flags={k: flags.iloc[i][k] for k in flags.columns},
                state=view,
                cfg=cfg,
            )
            actions = ea.emit_actions(i, ctx)
            validate_actions(actions)
            for act in actions:
                if act["type"] == "OPEN":
                    state, closed, result = simulate_bar(
                        state,
                        act["side"],
                        ticks,
                        tuple(t + cfg.fixed_spread_point * cfg.point for t in ticks),
                        cfg,
                        cfg.rr,
                        cfg.enable_trailing_stop,
                        cfg.trailing_start_ratio,
                        cfg.trailing_width_points,
                        cfg.stoploss_points,
                    )
                    if closed:
                        history.append({"time": ts, "result": result})
        out_dir = Path("outputs")
        out_dir.mkdir(exist_ok=True)
        hist_path = out_dir / f"TH_{args.run_id}.csv"
        pd.DataFrame(history).to_csv(hist_path, index=False)
        manifest = {"run_id": args.run_id, "trades": len(history)}
        (out_dir / f"Manifest_{args.run_id}.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        logger.info("simulation finished: %s trades", len(history))
    except Exception as exc:  # pragma: no cover - エラー時出力
        logger.error("simulation error: %s", exc)
        err = {"error": str(exc)}
        Path("outputs").mkdir(exist_ok=True)
        (Path("outputs") / f"{args.run_id}_error.json").write_text(json.dumps(err, ensure_ascii=False), encoding="utf-8")
        raise SimulationError(str(exc)) from exc


if __name__ == "__main__":
    main()
