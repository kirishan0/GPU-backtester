import logging
import os
from pathlib import Path
from typing import Optional


def get_logger(name: str, run_id: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    """ロガーを生成して返す。

    Args:
        name: ロガー名。
        run_id: 実行ID。ログファイル名に使用。
        level: ログレベル。

    Returns:
        logging.Logger: 初期化済みロガー。
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    run_label = run_id or "default"
    log_dir = Path("logs")
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / f"run_{run_label}.log", mode="a", encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    return logger
