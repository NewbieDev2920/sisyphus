from enum import Enum, auto

class State(Enum):
    FLAT = auto()
    LONG = auto()
    SHORT = auto()
    ORDER_PENDING = auto()