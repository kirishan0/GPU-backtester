from enum import Enum


class OHLCOrder(Enum):
    """OHLCの価格到達順序を表す列挙型。"""

    O_H_L_C = 0
    O_L_H_C = 1


class SpreadPolicy(Enum):
    """スプレッドの扱いに関するポリシー。"""

    NONE = 0
    SL_ONLY = 1
    FULL = 2
