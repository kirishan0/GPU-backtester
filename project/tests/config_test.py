import yaml
from pathlib import Path
import pytest

from project.engine.config import Config, ConfigError


def _write_config(tmp_path, **updates):
    base = Path(__file__).resolve().parents[1] / "config.yaml"
    with open(base, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    data.update(updates)
    cfg = tmp_path / "config.yaml"
    with open(cfg, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)
    return cfg


def test_min_lot_type_error(tmp_path):
    path = _write_config(tmp_path, min_lot="0.1")
    with pytest.raises(ConfigError):
        Config.from_yaml(path)


def test_min_lot_range_error(tmp_path):
    path = _write_config(tmp_path, min_lot=0)
    with pytest.raises(ConfigError):
        Config.from_yaml(path)


def test_overbought_oversold_range(tmp_path):
    path = _write_config(tmp_path, overbought=30, oversold=70)
    with pytest.raises(ConfigError):
        Config.from_yaml(path)
