from __future__ import annotations

from typing import Any, Dict, List

from .errors import ActionSchemaError

SUPPORTED_TYPES = {
    "OPEN",
    "CLOSE",
    "MODIFY",
    "SET_TRAILING",
    "PENDING_OPEN",
    "CANCEL_PENDING",
    "NOP",
}


def _ensure_keys(action: Dict[str, Any], required: List[str]) -> None:
    for key in required:
        if key not in action:
            raise ActionSchemaError(f"missing key: {key}")


def validate_action(action: Dict[str, Any]) -> None:
    """アクションのスキーマを検証する。"""
    if "type" not in action or action["type"] not in SUPPORTED_TYPES:
        raise ActionSchemaError("invalid action type")

    act_type = action["type"]
    if act_type == "OPEN":
        _ensure_keys(action, ["side", "lot"])
        if action["side"] not in {"BUY", "SELL"}:
            raise ActionSchemaError("invalid side")
        if not isinstance(action["lot"], (int, float)) or action["lot"] <= 0:
            raise ActionSchemaError("invalid lot")
        for key in ["sl", "tp"]:
            if key in action and not isinstance(action[key], (int, float)):
                raise ActionSchemaError(f"{key} must be float")
    elif act_type in {"CLOSE", "MODIFY", "SET_TRAILING", "CANCEL_PENDING"}:
        _ensure_keys(action, ["ticket"])
        if not isinstance(action["ticket"], int):
            raise ActionSchemaError("ticket must be int")
        if act_type == "MODIFY":
            if not any(k in action for k in ("sl", "tp")):
                raise ActionSchemaError("sl or tp required")
            for key in ["sl", "tp"]:
                if key in action and not isinstance(action[key], (int, float)):
                    raise ActionSchemaError(f"{key} must be float")
        if act_type == "SET_TRAILING":
            if "start_ratio" in action and not (0 <= action["start_ratio"] <= 1):
                raise ActionSchemaError("start_ratio out of range")
    elif act_type == "PENDING_OPEN":
        _ensure_keys(action, ["side", "lot", "price"])
        if action["side"] not in {"BUY", "SELL"}:
            raise ActionSchemaError("invalid side")
        if not isinstance(action["lot"], (int, float)) or action["lot"] <= 0:
            raise ActionSchemaError("invalid lot")
        if not isinstance(action["price"], (int, float)):
            raise ActionSchemaError("price must be float")
    elif act_type == "NOP":
        pass
    else:
        raise ActionSchemaError("unknown action type")


def validate_actions(actions: List[Dict[str, Any]]) -> None:
    """アクションリスト全体を検証する。"""
    for action in actions:
        validate_action(action)
