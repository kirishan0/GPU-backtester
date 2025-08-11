import pytest

from project.engine.optimizer import grid_search


def test_grid_search_returns_best_params():
    grid = {
        "x": {"start": 0, "stop": 2, "step": 1},
        "y": {"start": 0, "stop": 2, "step": 2},
    }

    def evaluate(params):
        return -((params["x"] - 1) ** 2 + (params["y"] - 2) ** 2)

    best_params, best_score = grid_search(grid, evaluate)
    assert best_params == {"x": 1, "y": 2}
    assert best_score == 0


def test_grid_search_empty():
    with pytest.raises(ValueError):
        grid_search({}, lambda _: 0)


def test_grid_search_accepts_list():
    grid = {"x": [0, 1, 2]}

    def evaluate(params):
        return params["x"]

    best_params, best_score = grid_search(grid, evaluate)
    assert best_params == {"x": 2}
    assert best_score == 2
