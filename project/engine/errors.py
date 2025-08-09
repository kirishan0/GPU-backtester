class EAValidationError(Exception):
    """EAの検証に失敗した場合に送出される例外。"""


class ActionSchemaError(Exception):
    """アクションのスキーマが不正な場合に送出される例外。"""


class ConfigError(Exception):
    """設定値が不正な場合に送出される例外。"""


class SimulationError(Exception):
    """シミュレーション中に発生した例外。"""
