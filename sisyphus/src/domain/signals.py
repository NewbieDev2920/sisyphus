from enum import Enum, auto

class Signal(Enum):
    BUY = auto()
    SELL = auto()
    HOLD = auto()
    BUY_NOTIONAL = auto()
    SELL_NOTIONAL = auto()