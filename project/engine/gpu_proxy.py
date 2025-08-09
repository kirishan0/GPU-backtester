from __future__ import annotations

import argparse
import subprocess

from .config import Config
from .logger import get_logger


def main() -> None:
    """GPUテスターとモックを切り替えるプロキシ。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--gpu-debug", action="store_true")
    parser.add_argument("--runs", type=int, default=None)
    args = parser.parse_args()

    cfg = Config.from_yaml(args.config)
    gpu_debug = args.gpu_debug or cfg.gpu_debug_mode
    logger = get_logger(__name__, args.run_id)

    if gpu_debug:
        cmd = [
            "python",
            "-m",
            "project.engine.gpu_mock",
            "--config",
            args.config,
            "--run-id",
            args.run_id,
        ]
        if args.runs:
            cmd.extend(["--runs", str(args.runs)])
        logger.info("launching gpu_mock")
        subprocess.run(cmd, check=True)
    else:
        cmd = [
            "python",
            "-m",
            "project.engine.gpu_tester",
            "--config",
            args.config,
            "--run-id",
            args.run_id,
        ]
        logger.info("launching gpu_tester")
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
