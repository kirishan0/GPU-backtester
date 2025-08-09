from __future__ import annotations

import argparse

from .config import Config
from .logger import get_logger


def main() -> None:
    """GPU実行のためのスタブ。

    実装は未提供だが、必要な引数を受け取りログを出力する。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    cfg = Config.from_yaml(args.config)
    logger = get_logger(__name__, args.run_id)

    logger.info("gpu tester start: symbol=%s", cfg.symbol)
    logger.info("gpu tester completed")


if __name__ == "__main__":
    main()
