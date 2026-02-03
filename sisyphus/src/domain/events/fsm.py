from domain.events.event import Event
from domain.signals import Signal
from domain.ports.fsm.states import State


class StateChange(Event):
    def __init__(self, past_state : State, new_state : State):
        self.past_state = past_state
        self.new_state = new_state

class SignalEvent(Event):
    def __init__(self, signal : Signal):
        self.signal = signal

class OrderResolved(Event):
    def __init__(self, order_id, symbol : str, numeric_value : float, type):
        self.order_id = order_id
        self.symbol = symbol
        self.numeric_value = numeric_value
        self.type = type

"""
class ExecutionEvent(Event):
    def __init__(self,side: str, qty : float, notional : float):
        self.side = side
        self.qty = qty
        self.notional = notional
"""