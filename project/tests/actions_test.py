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
