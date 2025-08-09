from project.engine.hit_rules import hit_order_for_segment, resolve_hit


def test_hit_order_for_segment():
    assert hit_order_for_segment("BUY", True) == ["TP", "SL"]
    assert hit_order_for_segment("SELL", False) == ["TP", "SL"]


def test_resolve_hit():
    result = resolve_hit("BUY", high=105, low=95, sl=96, tp=104, going_up=True)
    assert result == "TP"
    result = resolve_hit("SELL", high=105, low=95, sl=104, tp=96, going_up=False)
    assert result == "TP"
