import pytest

from project.engine.actions import validate_action, validate_actions, ActionSchemaError


def test_validate_action_open_ok():
    action = {"type": "OPEN", "side": "BUY", "lot": 0.1}
    validate_action(action)


def test_validate_action_open_ng():
    action = {"type": "OPEN", "side": "LONG", "lot": -1}
    with pytest.raises(ActionSchemaError):
        validate_action(action)


def test_validate_actions_mix():
    actions = [{"type": "NOP"}, {"type": "OPEN", "side": "SELL", "lot": 0.1}]
    validate_actions(actions)


def test_validate_action_pending_open_ok():
    action = {"type": "PENDING_OPEN", "side": "BUY", "lot": 0.1, "price": 100}
    validate_action(action)


def test_validate_action_pending_open_ng_lot_value():
    action = {"type": "PENDING_OPEN", "side": "BUY", "lot": 0, "price": 100}
    with pytest.raises(ActionSchemaError):
        validate_action(action)


def test_validate_action_pending_open_ng_lot_type():
    action = {"type": "PENDING_OPEN", "side": "BUY", "lot": "0.1", "price": 100}
    with pytest.raises(ActionSchemaError):
        validate_action(action)


def test_validate_action_modify_ok():
    action = {"type": "MODIFY", "ticket": 1, "sl": 50.0, "tp": 100.0}
    validate_action(action)


def test_validate_action_modify_ng_sl_type():
    action = {"type": "MODIFY", "ticket": 1, "sl": "50", "tp": 100.0}
    with pytest.raises(ActionSchemaError):
        validate_action(action)


def test_validate_action_modify_ng_tp_type():
    action = {"type": "MODIFY", "ticket": 1, "sl": 50.0, "tp": "100"}
    with pytest.raises(ActionSchemaError):
        validate_action(action)
