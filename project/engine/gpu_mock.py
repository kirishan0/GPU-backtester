from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .config import Config
from .logger import get_logger


def _hash_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def _scale_int(value: int, min_v: int, max_v: int) -> float:
    span = max_v - min_v
    return min_v + (value % (span + 1))


def _scale_float(value: int, min_v: float, max_v: float) -> float:
    span = max_v - min_v
    return min_v + (value / (2**256 - 1)) * span


def _generate_metrics(seed: str) -> dict[str, Any]:
    base = _hash_int(seed)
    metrics = {
        "total_trades": int(_scale_int(base, 80, 420)),
        "win_rate": round(_scale_float(base >> 8, 0.35, 0.65), 4),
        "avg_win": round(_scale_float(base >> 16, 5, 25), 4),
        "avg_loss": round(_scale_float(base >> 24, -25, -5), 4),
        "profit_factor": round(_scale_float(base >> 32, 0.8, 2.5), 4),
        "max_dd_pts": int(_scale_int(base >> 40, 50, 400)),
        "net_profit_pts": int(_scale_int(base >> 48, -200, 500)),
    }
    return metrics


def main() -> None:
    """GPUデバッグ用のダミー出力を生成する。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--runs", type=int, default=None)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    cfg = Config.from_yaml(args.config)
    runs = args.runs or cfg.gpu_debug_runs
    logger = get_logger(__name__, args.run_id)

    out_root = Path("outputs/GPU") / f"Run_{args.run_id}"
    out_root.mkdir(parents=True, exist_ok=True)

    for i in range(runs):
        params_json = json.dumps({"index": i})
        seed = params_json + cfg.gpu_debug_seed
        metrics = _generate_metrics(seed)
        run_dir = out_root / f"{i}"
        run_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "run_id": args.run_id,
            "index": i,
            "metrics": metrics,
            "params": json.loads(params_json),
            "cfg": {"symbol": cfg.symbol, "point": cfg.point},
        }
        (run_dir / "Manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        with open(run_dir / "Summary.csv", "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["run_id", "index", "total_trades", "win_rate", "profit_factor", "net_profit_pts"])
            writer.writeheader()
            writer.writerow(
                {
                    "run_id": args.run_id,
                    "index": i,
                    "total_trades": metrics["total_trades"],
                    "win_rate": metrics["win_rate"],
                    "profit_factor": metrics["profit_factor"],
                    "net_profit_pts": metrics["net_profit_pts"],
                }
            )
        logger.info("run %d generated", i)

    logger.info("gpu mock completed")


if __name__ == "__main__":
    main()
