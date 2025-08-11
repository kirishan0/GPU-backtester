from __future__ import annotations

from itertools import product
from typing import Any, Callable, Dict, List, Tuple


def _expand_values(spec: Any) -> List[Any]:
    """MT4 風の範囲指定から値リストを生成する補助関数。"""
    if isinstance(spec, dict):
        start = spec["start"]
        stop = spec["stop"]
        step = spec["step"]
        if step <= 0:
            raise ValueError("step は正の値である必要があります")
        values: List[Any] = []
        value = start
        while value <= stop:
            values.append(value)
            value += step
        return values
    return list(spec)


def grid_search(param_grid: Dict[str, Any], evaluate: Callable[[Dict[str, Any]], float]) -> Tuple[Dict[str, Any], float]:
    """指定されたパラメータ網羅探索を行い、最高スコアの組み合わせを返す。

    Args:
        param_grid: 各パラメータ名に対する候補値の辞書。値にはリスト
            または ``{"start": a, "stop": b, "step": c}`` の形式で範囲を指定
            できる。
        evaluate: パラメータ辞書を受け取りスコアを返す評価関数。

    Returns:
        best_params: 最良スコアを得たパラメータ組み合わせ。
        best_score: その時のスコア。

    Raises:
        ValueError: param_grid が空の場合。
    """
    if not param_grid:
        raise ValueError("param_grid が空です")

    best_params: Dict[str, Any] | None = None
    best_score: float | None = None
    keys = list(param_grid.keys())
    grids = [_expand_values(param_grid[k]) for k in keys]
    for values in product(*grids):
        params = dict(zip(keys, values))
        score = evaluate(params)
        if best_score is None or score > best_score:
            best_score = score
            best_params = params

    assert best_params is not None and best_score is not None
    return best_params, best_score
